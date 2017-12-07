from gi import pygtkcompat

pygtkcompat.enable() 
pygtkcompat.enable_gtk(version='3.0')

import gtk
import gio

import odml
import odml.terminology as terminology
import odml.format as format
from odml import DType
from . import commands
from .TreeView import TerminologyPopupTreeView
from .treemodel import PropertyModel
from .DragProvider import DragProvider
from .ChooserDialog import ChooserDialog
from . import TextEditor

COL_KEY = 0
COL_VALUE = 1

from .dnd.targets import ValueDrop, PropertyDrop, SectionDrop
from .dnd.odmldrop import OdmlDrag, OdmlDrop
from .dnd.text import TextDrag, TextDrop, TextGenericDropForPropertyTV

class PropertyView(TerminologyPopupTreeView):
    """
    The Main treeview for editing properties and their value-attributes
    """
    _section = None

    def __init__(self, registry):

        super(PropertyView, self).__init__()
        tv = self._treeview

        for name, (id, propname) in PropertyModel.ColMapper.sort_iteritems():
            if name == "Type":
                combo_col = self.create_odml_types_col(id, name, propname)
                tv.append_column(combo_col)
            else:
                renderer, column = self.add_column(
                    name=name,
                    edit_func=self.on_edited,
                    id=id, data=propname)
                if name == "Unit":
                    column.set_cell_data_func(renderer, self.unit_renderer_function, id)
                elif name == "Value":
                    tv.set_expander_column(column)

        tv.set_headers_visible(True)
        tv.set_rules_hint(True)
        tv.show()

        # set up our drag provider
        dp = DragProvider(self._treeview)
        _exec = lambda cmd: self.execute(cmd)
        vd = ValueDrop(exec_func=_exec)
        pd = PropertyDrop(exec_func=_exec)
        sd = SectionDrop(exec_func=_exec)
        for target in [
            OdmlDrag(mime="odml/property-ref", inst=odml.property.Property),
            TextDrag(mime="odml/property", inst=odml.property.Property),
            OdmlDrag(mime="odml/value-ref", inst=odml.value.Value),
            TextDrag(mime="odml/value", inst=odml.value.Value),
            TextDrag(mime="TEXT"),
            OdmlDrop(mime="odml/value-ref", target=vd, registry=registry, exec_func=_exec),
            OdmlDrop(mime="odml/property-ref", target=pd, registry=registry, exec_func=_exec),
            OdmlDrop(mime="odml/section-ref", target=sd, registry=registry, exec_func=_exec),
            TextDrop(mime="odml/value", target=vd),
            TextDrop(mime="odml/property", target=pd),
            TextDrop(mime="odml/section", target=sd),
            TextGenericDropForPropertyTV(exec_func=_exec),
            ]:
            dp.append(target)
        dp.execute = _exec
        dp.connect()

    def unit_renderer_function(self, tv_column, column_cell, tree_model, tree_iter, data):
        try:
            cell_data = tree_model.get(tree_iter, data)[0]
            column_cell.set_property('markup', cell_data)
        except TypeError:
            column_cell.set_property('markup', '')

    def dtype_renderer_function(self, tv_column, cell_combobox, tree_model, tree_iter, data):
        '''
            Defines a custom cell renderer function, which is executed for
            every cell of the column, and sets the DType value from the underlying model.

            Argument 'Data': Here, it defines the column number in the Tree View.
        '''

        cell_data = tree_model.get(tree_iter, data)[0]
        cell_combobox.set_property('markup', cell_data)


    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, section):
        if self._section is section and self.model:
            return
        self._section = section
        if self.model:
            self.model.destroy()
        self.model = PropertyModel.PropertyModel(section)

    @property
    def model(self):
        return self._treeview.get_model()

    @model.setter
    def model(self, new_value):
        self._treeview.set_model(new_value)

    def on_selection_change(self, tree_selection):
        (model, tree_iter) = tree_selection.get_selected()
        if not tree_iter:
            return
        obj = model.get_object(tree_iter)
        self.on_property_select(obj)

        # Always expand multi value properties when selected
        is_multi_value = isinstance(obj, odml.property.Property) and len(obj.values) > 1
        if is_multi_value:
            tree_selection.get_tree_view().expand_row(model.get_path(tree_iter), False)

    def on_property_select(self, prop):
        """called when a different property is selected"""
        pass

    def on_get_tooltip(self, model, path, iter, tooltip):
        """
        set the tooltip text, if the gui queries for it
        """
        obj = model.get_object(iter)
        doc = obj.document
        if doc and hasattr(doc, "validation_result"):
            errors = doc.validation_result[obj]
            if len(errors) > 0:
                tooltip.set_text("\n".join([e.msg for e in errors]))
                return True

    def on_object_edit(self, tree_iter, column_name, new_text):
        """
        called upon an edit event of the list view

        updates the underlying model property that corresponds to the edited cell
        """
        section = self.section
        prop = tree_iter._obj

        # are we editing the first_row of a <multi> value?
        first_row = not tree_iter.parent
        first_row_of_multi = first_row and tree_iter.has_child

        # can only edit the subvalues, but not <multi> itself
        if first_row_of_multi and column_name == "value":
            return
        if not first_row and column_name == "name":
            return

        cmd = None
        # if we edit another attribute (e.g. unit), set this for all values of this property

        if first_row_of_multi and column_name != "name":
            # editing multiple values of a property at once
            cmds = []
            for value in prop.values:
                cmds.append(commands.ChangeValue(
                    object    = value,
                    attr      = [column_name, "value"],
                    new_value = new_text))

            cmd = commands.Multiple(cmds=cmds)

        else:

            # first row edit event for the value, so switch the object
            if column_name != "name" and first_row:
                # Add empty value if value list is empty.
                if len(prop.values) < 1:
                    cmd = commands.AppendValue(obj=prop, val=odml.Value(""))
                    self.execute(cmd)
                    # Force reset view model to keep up to date with changed tree model.
                    self.model = PropertyModel.PropertyModel(section)

                prop = prop.values[0]
            if not (column_name == "name" and first_row):
                column_name = [column_name, "value"] # backup the value attribute too
            cmd = commands.ChangeValue(
                    object    = prop,
                    attr      = column_name,
                    new_value = new_text)

        if cmd:
            self.execute(cmd)

    def on_set_mapping(self, menu, obj_prop_pair):
        """
        popup menu action: set mapping for a property
        """
        # Shouldn't the below left hand side be (mapping_obj, prop) ?
        # ( From line 197 ? )
        (prop, mapping_obj) = obj_prop_pair
        mapstr = "%s#%s:%s" % (prop.parent.get_repository(), mapping_obj.parent.type, mapping_obj.name)

        cmd = commands.ChangeValue(
                object = prop,
                attr   = "mapping",
                new_value = mapstr)
        self.execute(cmd)

    def get_popup_mapping_section(self, sec, obj):
        """generate the popup menu items for a certain section in the mapping-popup-menu"""
        for sec in sec.sections:
            item = self.create_menu_item(sec.name)
            if len(sec) > 0:
                item.set_submenu(self.get_popup_menu(lambda: self.get_popup_mapping_section(sec, obj)))
                yield item

        if isinstance(sec, odml.doc.Document): return

        yield self.create_menu_item(None)  #separator

        for prop in sec.properties:
            item = self.create_menu_item(prop.name)
            item.connect('activate', self.on_set_mapping, (obj, prop))
            yield item

    def get_popup_mapping_suggestions(self, prop):
        """
        build a submenu with mapping suggestions
        """
        repo = prop.parent.get_repository()
        if not repo: return None
        term = terminology.load(repo)

        menu = self.create_menu_item("Map", stock="odml-set-Mapping")
        submenu = self.get_popup_menu(lambda: self.get_popup_mapping_section(term, prop))
        menu.set_submenu(submenu)
        return menu

    def get_popup_menu_items(self):
        model, path, obj = self.popup_data
        menu_items = self.create_popup_menu_items("Add Property", "Empty Property", model.section, self.add_property, lambda sec: sec.properties, lambda prop: prop.name, stock="odml-add-Property")
        if obj is not None: # can also add value
            prop = obj
            if hasattr(obj, "_property"): # we care about the properties only
                prop = obj._property

            value_filter = lambda prop: [val for val in prop.values if val.value is not None and val.value != ""]
            for item in self.create_popup_menu_items("Add Value", "Empty Value", prop, self.add_value, value_filter, lambda val: val.value, stock="odml-add-Value"):
                menu_items.append(item)
            for item in self.create_popup_menu_items("Set Value", "Empty Value", prop, self.set_value, value_filter, lambda val: val.value):
                if item.get_submenu() is None: continue # don't want a sole Set Value item
                menu_items.append(item)

            # conditionally allow to store / load binary content
            val = obj
            if prop is obj:
                val = obj.value if len(obj) == 1 else None

            if val is not None and val.dtype == "binary":
                menu_items.append(self.create_menu_item("Load binary content", self.binary_load, val))
                if val.data is not None:
                    menu_items.append(self.create_menu_item("Save binary content", self.binary_save, val))

            if val is not None and val.dtype == "text":
                menu_items.append(self.create_menu_item("Edit text in larger window", self.edit_text, val))

            # if repository is set, show a menu to set mappings
            mapping_menu = self.get_popup_mapping_suggestions(prop)
            if mapping_menu:
                menu_items.append(mapping_menu)

            # cannot delete properties that are linked (they'd be override on next load), instead allow to reset them
            merged = prop.get_merged_equivalent()
            if prop is obj and merged is not None:
                if merged != obj:
                    menu_items.append(self.create_menu_item("Reset to merged default", self.reset_property, obj))
            else:
                menu_items.append(self.create_popup_menu_del_item(obj))
        return menu_items

    def binary_load(self, widget, val):
        """
        popup menu action: load binary content
        """
        chooser = ChooserDialog(title="Open binary file", save=False)
        if val.filename is not None:
            # try to set the filename (if it exists)
            chooser.set_file(gio.File(val.filename))
        chooser.show()

        def binary_load_file(uri):
            if val._encoder is None:
                val.encoder = "base64"
            val.data = gio.File(uri).read().read()

        chooser.on_accept = binary_load_file

    def binary_save(self, widget, val):
        """
        popup menu action: load binary content
        """
        chooser = ChooserDialog(title="Save binary file", save=True)
        if val.filename is not None:
            # suggest a filename
            chooser.set_current_name(val.filename)
        chooser.show()

        def binary_save_file(uri):
            fp = gio.File(uri).replace(etag='', make_backup=False)
            fp.write(val.data)
            fp.close()

        chooser.on_accept = binary_save_file

    def edit_text(self, widget, val):
        """
        popup menu action: edit text in larger window
        """
        t = TextEditor.TextEditor(val, "value")
        t.execute = self.execute

    def reset_property(self, widget, prop):
        """
        popup menu action: reset property
        """
        dst = prop.get_merged_equivalent().clone()
        cmd = commands.ReplaceObject(obj=prop, repl=dst)
        self.execute(cmd)

    def set_value(self, widget, prop_value_pair):
        """
        popup menu action: set value

        set the curr
        """
        (prop, val) = prop_value_pair
        model, path, obj = self.popup_data
        if val is None:
            val = odml.Value("")
        else:
            val = val.clone()

        if obj is prop:
            obj = prop.values[0]

        prop = obj._property

        # first append, then remove to keep the constraint that a property
        # will always hold at least one value
        cmd = commands.Multiple(cmds=[
                commands.AppendValue(obj=prop, val=val),
                commands.DeleteObject(obj=obj)
                ])
        self.execute(cmd)

    def add_value(self, widget, obj_value_pair):
        """
        popup menu action: add value

        add a value to the selected property
        """
        (obj, val) = obj_value_pair
        if val is None:
            val = odml.Value("")
        else:
            val = val.clone()

        cmd = commands.AppendValue(obj=obj, val=val)
        self.execute(cmd)

        # Reselect updated object to update view.
        self.select_object(obj)

    def add_property(self, widget, obj_prop_pair):
        """
        popup menu action: add property

        add a property to the active section
        """
        (obj, prop) = obj_prop_pair
        if prop is None:
            name = self.get_new_obj_name(obj.properties, prefix='Unnamed Property')
            prop = odml.Property(name=name, value="")
        else:
            prefix = prop.name
            name = self.get_new_obj_name(obj.properties, prefix=prefix)
            prop = prop.clone()
            prop.name = name

        cmd = commands.AppendValue(obj=obj, val=prop)
        self.execute(cmd)

    # Maybe define a generic Combo Box column creator ?
    def create_odml_types_col(self, id, name, propname):
        
        # Get all the members of odml.DType, which are not callable and are not `private`.
        dtypes_list = [x for x in dir(DType) if not callable(getattr(DType, x)) and not x.startswith('__')]
        dtypes_combo_list = gtk.ListStore(str)
        for i in dtypes_list:
            dtypes_combo_list.append([i])

        combo_renderer = gtk.CellRendererCombo.new()
        combo_renderer.set_property("has-entry", False)
        combo_renderer.set_property("text-column", 0)
        combo_renderer.set_property("model", dtypes_combo_list)
        combo_renderer.set_property("editable", True)
        combo_renderer.connect("edited", self.on_edited, propname)

        combo_col = gtk.TreeViewColumn(name, combo_renderer)
        combo_col.set_min_width(40)
        combo_col.set_resizable(True)
        combo_col.set_cell_data_func(combo_renderer, self.dtype_renderer_function, id)

        return combo_col
