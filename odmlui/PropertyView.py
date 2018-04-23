import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk

import odml
import odml.dtypes as dtypes
import odml.terminology as terminology

from odml import DType
from odml.property import BaseProperty

from . import commands
from . import TextEditor
from .DragProvider import DragProvider
from .Helpers import create_pseudo_values
from .TreeView import TerminologyPopupTreeView
from .treemodel import PropertyModel, ValueModel
from .dnd.odmldrop import OdmlDrag, OdmlDrop
from .dnd.targets import ValueDrop, PropertyDrop, SectionDrop
from .dnd.text import TextDrag, TextDrop, TextGenericDropForPropertyTV

COL_KEY = 0
COL_VALUE = 1


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
                if name == "Value":
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
            OdmlDrag(mime="odml/property-ref", inst=BaseProperty),
            TextDrag(mime="odml/property", inst=BaseProperty),
            OdmlDrag(mime="odml/value-ref", inst=ValueModel.Value),
            TextDrag(mime="odml/value", inst=ValueModel.Value),
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

    def dtype_renderer_function(self, tv_column, cell_combobox, tree_model, tree_iter, data):
        """
            Defines a custom cell renderer function, which is executed for
            every cell of the column, and sets the DType value from the underlying model.

            Argument 'Data': Here, it defines the column number in the Tree View.
        """

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
        is_multi_value = isinstance(obj, BaseProperty) and len(obj.value) > 1
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
        prop = tree_iter._obj

        # are we editing the first_row of a <multi> value?
        first_row = not tree_iter.parent
        first_row_of_multi = first_row and tree_iter.has_child

        if not first_row and column_name != "pseudo_values":
            return
        # Do not replace multiple values with pseudo_value placeholder text.
        if first_row_of_multi and column_name == "pseudo_values" and new_text == "<multi>":
            return

        cmd = None
        # if we edit another attribute (e.g. unit), set this for all values of this property

        if first_row_of_multi and column_name == "pseudo_values":
            # editing multiple values of a property at once
            cmds = []
            for value in prop.pseudo_values:
                cmds.append(commands.ChangeValue(
                    object=value,
                    attr=[column_name, "value"],
                    new_value=new_text))

            cmd = commands.Multiple(cmds=cmds)

        else:
            # first row edit event for the property, so switch to appropriate object
            #  - Only if the 'value' column is edited, edit the pseudo-value object.
            #  - Else, edit the property object
            if column_name == 'pseudo_values' and first_row:
                prop = prop.pseudo_values[0]
            if column_name == "pseudo_values" and first_row:
                column_name = [column_name, "value"]  # backup the value attribute too
            cmd = commands.ChangeValue(
                    object=prop,
                    attr=column_name,
                    new_value=new_text)

        if cmd:
            self.execute(cmd)

    def get_popup_menu_items(self):
        model, path, obj = self.popup_data
        menu_items = self.create_popup_menu_items("Add Property", "Empty Property", model.section,
                                                  self.add_property, lambda sec: sec.properties,
                                                  lambda prop: prop.name, stock="odml-add-Property")
        if obj is not None:  # can also add value
            prop = obj

            if hasattr(obj, "_property"):  # we care about the properties only
                prop = obj._property

            value_filter = lambda prop: [val for val in prop.values if val.value is not None and val.value != ""]
            for item in self.create_popup_menu_items("Add Value", "Empty Value", prop, self.add_value,
                                                     value_filter, lambda val: val.value, stock="odml-add-Value"):
                menu_items.append(item)
            for item in self.create_popup_menu_items("Set Value", "Empty Value", prop, self.set_value,
                                                     value_filter, lambda val: val.value):
                if item.get_submenu() is None:
                    continue  # don't want a sole Set Value item
                menu_items.append(item)

            val = obj

            if prop is obj:
                val = prop.pseudo_values[0] if len(prop.pseudo_values) == 1 else None

            if val is not None and val.dtype == "text":
                menu_items.append(self.create_menu_item("Edit text in larger window", self.edit_text, val))

            # cannot delete properties that are linked (they'd be override on next load), instead allow to reset them
            merged = prop.get_merged_equivalent()
            if prop is obj and merged is not None:
                if merged != obj:
                    menu_items.append(self.create_menu_item("Reset to merged default", self.reset_property, obj))
            else:
                menu_items.append(self.create_popup_menu_del_item(obj))
        return menu_items

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
        """
        (prop, val) = prop_value_pair
        model, path, obj = self.popup_data
        if val is None:
            val = ValueModel.Value(prop)
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
            val = ValueModel.Value(obj)
        else:
            val = val.clone()

        cmd = commands.AppendValue(obj=obj.pseudo_values, val=val)
        self.execute(cmd)

        # Reset model if the Value changes from "normal" to MultiValue.
        if self.model and len(obj.value) > 1:
            self.model.destroy()
            self.model = PropertyModel.PropertyModel(obj.parent)

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
            prop = odml.Property(name=name, dtype='string')
            # The default value part should be put in odML core library
            prop._value = [dtypes.default_values('string')]
            create_pseudo_values([prop])
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
