"""
The 'property_view' module provides a class to display and edit odml.Properties
and their attributes and Values.
"""

import pygtkcompat

import odml
import odml.dtypes as dtypes

from odml import DType
from odml.property import BaseProperty

import gtk

from . import commands
from . import text_editor
from .drag_provider import DragProvider
from .helpers import create_pseudo_values
from .tree_view import TerminologyPopupTreeView
from .treemodel import property_model, value_model
from .dnd.odmldrop import OdmlDrag, OdmlDrop
from .dnd.targets import ValueDrop, PropertyDrop, SectionDrop
from .dnd.text import TextDrag, TextDrop, TextGenericDropForPropertyTV

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class PropertyView(TerminologyPopupTreeView):
    """
    The main TreeView for editing Properties and their value-attributes
    """
    _section = None

    def __init__(self, registry):
        super(PropertyView, self).__init__()
        curr_view = self._treeview

        for name, (col_id, prop_name) in property_model.COL_MAPPER.sort_iteritems():
            if name == "Type":
                combo_col = self.create_odml_types_col(col_id, name, prop_name)
                curr_view.append_column(combo_col)
            else:
                _, column = self.add_column(name=name, edit_func=self.on_edited,
                                            col_id=col_id, data=prop_name)
                if name == "Value":
                    curr_view.set_expander_column(column)

        curr_view.set_headers_visible(True)
        curr_view.set_rules_hint(True)
        curr_view.show()

        # set up our drag provider
        drager = DragProvider(self._treeview)
        v_drop = ValueDrop(exec_func=self.execute)
        p_drop = PropertyDrop(exec_func=self.execute)
        s_drop = SectionDrop(exec_func=self.execute)
        for target in [
                OdmlDrag(mime="odml/property-ref", inst=BaseProperty),
                TextDrag(mime="odml/property", inst=BaseProperty),
                OdmlDrag(mime="odml/value-ref", inst=value_model.Value),
                TextDrag(mime="odml/value", inst=value_model.Value),
                TextDrag(mime="TEXT"),
                OdmlDrop(mime="odml/value-ref", target=v_drop,
                         registry=registry, exec_func=self.execute),
                OdmlDrop(mime="odml/property-ref", target=p_drop,
                         registry=registry, exec_func=self.execute),
                OdmlDrop(mime="odml/section-ref", target=s_drop,
                         registry=registry, exec_func=self.execute),
                TextDrop(mime="odml/value", target=v_drop),
                TextDrop(mime="odml/property", target=p_drop),
                TextDrop(mime="odml/section", target=s_drop),
                TextGenericDropForPropertyTV(exec_func=self.execute), ]:

            drager.append(target)
        drager.execute = self.execute
        drager.connect()

    @staticmethod
    def dtype_renderer(_, cell_combobox, tree_model, tree_iter, data):
        """
        Defines a custom cell renderer function, which is executed for
        every cell of the column, and sets the DType value from the underlying model.

        Argument 'Data': Here it defines the column number in the Tree View.
        """

        cell_data = tree_model.get(tree_iter, data)[0]
        cell_combobox.set_property('markup', cell_data)

    @property
    def section(self):
        """
        :return: The odml.Section that is the parent of the current PropertyView.
        """
        return self._section

    @section.setter
    def section(self, section):
        """
        Update the parent odml.Section of the current PropertyView and
        update the underlying model accordingly.

        :param section: odml.Section
        """
        if self._section is section and self.model:
            return

        self._section = section

        if self.model:
            self.model.destroy()

        self.model = property_model.PropertyModel(section)

    @property
    def model(self):
        """
        :return: The current model of the PropertyView.
        """
        return self._treeview.get_model()

    @model.setter
    def model(self, new_value):
        self._treeview.set_model(new_value)

    def on_selection_change(self, tree_selection):
        """
        Updates the view model if a different object is selected.

        :param tree_selection: gtk.TreeSelection
        """
        (model, tree_iter) = tree_selection.get_selected()
        if not tree_iter:
            return
        obj = model.get_object(tree_iter)
        self.on_property_select(obj)

        # Always expand multi value properties when selected
        is_multi_value = isinstance(obj, BaseProperty) and len(obj.values) > 1
        if is_multi_value:
            tree_selection.get_tree_view().expand_row(model.get_path(tree_iter), False)

    def on_property_select(self, prop):
        """
        Called when a Property is selected.

        The actual method is set on the class at the point of usage.
        """
        pass

    @staticmethod
    def on_get_tooltip(model, tree_iter, tooltip):
        """
        If the GUI is queried for a tooltip on a Property,
        set any existing validation errors as tooltip text.

        This method is currently inactivated in TreeView.init
        until the pseudo_value display can be resolved.

        :return: True if the tooltip text is set, False otherwise
        """
        obj = model.get_object(tree_iter)
        doc = obj.document
        if doc and hasattr(doc, "validation_result"):
            errors = doc.validation_result[obj]
            if errors:
                tooltip.set_text("\n".join([e.msg for e in errors]))
                return True

        return False

    def on_object_edit(self, tree_iter, column_name, new_text):
        """
        Called upon an edit event of Properties and Values in the list view
        and updates the underlying model Property correspondingly.

        :param tree_iter: Iterator object of the currently edited cell
        :param column_name: Column name of the currently edited cell
        :param new_text: String that should replace the value of the
                         currently edited cell
        """
        prop = tree_iter._obj

        is_value_column = column_name == "pseudo_values"

        # Are we editing the first_row of a <multi> value?
        first_row = not tree_iter.parent
        first_row_of_multi = first_row and tree_iter.has_child

        # Do not edit any column other than 'value' on a multi_value row
        if not first_row and not is_value_column:
            return

        # Do not replace multiple values with pseudo_value placeholder text.
        if first_row_of_multi and is_value_column and new_text == "<multi>":
            return

        # If we edit another attribute (e.g. unit), set this
        # for all values of this property.
        if first_row_of_multi and is_value_column:
            # Editing multiple values of a property at once
            cmds = []
            for value in prop.pseudo_values:
                cmds.append(commands.ChangeValue(
                    object=value,
                    attr=[column_name, "value"],
                    new_value=new_text))

            cmd = commands.Multiple(cmds=cmds)

        else:
            # First row edit event for the property, so switch to appropriate object
            #  - Only if the 'value' column is edited, edit the pseudo-value object.
            #  - Else, edit the property object
            if first_row and is_value_column:
                column_name = [column_name, "value"]
                # If the list of pseudo_values was empty, we need to initialize a new
                # empty PseudoValue and add it properly to enable undo.
                if not prop.pseudo_values:
                    val = value_model.Value(prop)
                    cmd = commands.AppendValue(obj=prop.pseudo_values, attr=column_name,
                                               val=val)
                    self.execute(cmd)

                prop = prop.pseudo_values[0]

            cmd = commands.ChangeValue(object=prop, attr=column_name, new_value=new_text)

        if cmd:
            self.execute(cmd)

        # Always reset the view when changes have occurred
        # to ensure no GTK view out of sync horror happening.
        self.reset_value_view(None)

    @staticmethod
    def _value_filter(prop):
        values = []
        for val in prop.values:
            if val is not None and val != "":
                values.append(val)
        return values

    def get_popup_menu_items(self):
        """
        Creates and populates the popup menu of the PropertyView.

        The menu provides access to Property and Value specific functions.
        - Add a new empty or Terminology Value to a Property
        - Set a Value to empty or to a Terminology Value
        - Open a Value with odml datatype 'Text' in a TextEditor window.
        - Reset a manipulated Terminology Property back to its Terminology state.

        :return: gtk.Menu populated with Value and Property specific gtk.MenuItems
        """
        model, _, obj = self.popup_data
        menu_items = self.create_popup_menu_items("Add Property", "Empty Property",
                                                  model.section, self.add_property,
                                                  lambda sec: sec.properties,
                                                  lambda prop: prop.name,
                                                  stock="odml-add-Property")
        if obj is not None:
            prop = obj

            # We are working exclusively with Properties
            if isinstance(obj, value_model.Value):
                prop = obj.parent

            for item in self.create_popup_menu_items("Add Value", "Empty Value", prop,
                                                     self.add_value, self._value_filter,
                                                     lambda curr_val: curr_val,
                                                     stock="odml-add-Value"):
                menu_items.append(item)

            for item in self.create_popup_menu_items("Set Value", "Empty Value", prop,
                                                     self.set_value, self._value_filter,
                                                     lambda curr_val: curr_val):
                if item.get_submenu() is None:
                    # We don't want a single Set Value item
                    continue
                menu_items.append(item)

            val = obj

            if prop is obj:
                val = prop.pseudo_values[0] if len(prop.pseudo_values) == 1 else None

            if val is not None and val.dtype == "text":
                menu_items.append(self.create_menu_item("Edit text in larger window",
                                                        self.edit_text, val))

            # Cannot delete properties that are linked (they'd be override on next load),
            # instead allow to reset them.
            merged = prop.get_merged_equivalent()
            if prop is obj and merged is not None:
                if merged != obj:
                    menu_items.append(self.create_menu_item("Reset to merged default",
                                                            self.reset_property, obj))
            else:
                menu_items.append(self.create_popup_menu_del_item(obj))

        return menu_items

    def edit_text(self, _, val):
        """
        Opens a TextEditor window containing the provided value.
        """
        t_edit = text_editor.TextEditor(val, "value")
        t_edit.execute = self.execute

    def reset_property(self, _, prop):
        """
        *reset_property* replaces a provided Property with its
        equivalent from a terminology linked in the parent of the Property.

        :param prop: odml.Property to be replaced by its terminology equivalent.
        """
        dst = prop.get_merged_equivalent().clone()
        create_pseudo_values([dst])
        cmd = commands.ReplaceObject(obj=prop, repl=dst)
        self.execute(cmd)

        # Reset the view to make sure the changes are properly displayed.
        self.reset_value_view(None)

    def set_value(self, _, prop_value_pair):
        """
        Set the content of a Value. In context this means,
        that the content if an existing Value is replaced by a Terminology Value
        via the popup menu option.

        :param prop_value_pair: Tuple containing *prop*, an odml.Property,
                                and *val* a String to replace the content of
                                the value object passed via a popup event.
        """
        (prop, val) = prop_value_pair

        _, _, obj = self.popup_data
        if not isinstance(obj, value_model.Value):
            raise TypeError("Expected %s" % type(value_model.Value))

        if not prop == obj.parent:
            raise ValueError("Property '%s' is not the parent of '%s'" % (prop, obj))

        # To enable undo redo for this we need a bit of trickery
        new_prop = prop.clone(keep_id=True)
        create_pseudo_values([new_prop])
        if new_prop.pseudo_values[obj.index].pseudo_values != obj.pseudo_values:
            raise ValueError("Cannot find replacement value")

        # Update the value in the new property
        new_prop.pseudo_values[obj.index].pseudo_values = val

        # Lets replace the old property with the new and updated one
        cmd = commands.ReplaceObject(obj=prop, repl=new_prop)
        self.execute(cmd)

        # Reset the view to make sure the changes are properly displayed.
        self.select_object(new_prop)
        self.reset_value_view(None)

    def add_value(self, _, obj_value_pair):
        """
        Add a value to a selected Property

        :param obj_value_pair: Tuple containing *obj*, an odml.Property,
                               and *val* a string containing the new value.
        """
        (obj, val) = obj_value_pair
        new_val = value_model.Value(obj)

        # Add new empty PseudoValue to the Properties PseudoValue list
        cmd = commands.AppendValue(obj=obj.pseudo_values, val=new_val)
        self.execute(cmd)

        # Update the empty new PseudoValue with the actual value.
        if val:
            new_val.pseudo_values = val

        # Reset the view to make sure the changes are properly displayed.
        self.reset_value_view(None)

    def add_property(self, _, obj_prop_pair):
        """
        Add a Property to a selected Section.

        :param obj_prop_pair: Tuple containing *obj*, an odml.Section,
                              and *prop*, either None or the new odml.Property.
        """
        (obj, prop) = obj_prop_pair
        if prop is None:
            name = self.get_new_obj_name(obj.properties, prefix='Unnamed Property')
            prop = odml.Property(name=name, dtype='string')
            # The default value part should be put in odML core library
            prop.values = [dtypes.default_values('string')]
            create_pseudo_values([prop])
        else:
            prefix = prop.name
            name = self.get_new_obj_name(obj.properties, prefix=prefix)
            prop = prop.clone()
            prop.name = name
            create_pseudo_values([prop])

        cmd = commands.AppendValue(obj=obj, val=prop)
        self.execute(cmd)

    def reset_value_view(self, _):
        """
        Reset the view if the value model has changed e.g. after an undo or a redo.
        """
        obj = self.get_selected_object()
        if obj is None or not hasattr(obj, "parent") or not obj.parent:
            return

        prop = obj
        sec = obj.parent
        if isinstance(obj, value_model.Value):
            sec = obj.parent.parent
            prop = obj.parent

        self.model.destroy()
        self.model = property_model.PropertyModel(sec)

        # Always select the Property when resetting the view
        self.select_object(prop)

    def create_odml_types_col(self, col_id, name, prop_name):
        """
        Create and return an odML 'dtype' specific gtk.TreeViewColumn

        :param col_id: column ID
        :param name: String containing the column name to be displayed.
        :param prop_name: name of the odML Property attribute

        :return: gtk.TreeViewColumn
        """

        # Get all the members of odml.DType, which are not callable and are not 'private'.
        dtypes_list = [x for x in dir(DType) if not callable(getattr(DType, x)) and
                       not x.startswith('__')]
        dtypes_combo_list = gtk.ListStore(str)
        for i in dtypes_list:
            dtypes_combo_list.append([i])

        combo_renderer = gtk.CellRendererCombo.new()
        combo_renderer.set_property("has-entry", False)
        combo_renderer.set_property("text-column", 0)
        combo_renderer.set_property("model", dtypes_combo_list)
        combo_renderer.set_property("editable", True)
        combo_renderer.connect("edited", self.on_edited, prop_name)

        combo_col = gtk.TreeViewColumn(name, combo_renderer)
        combo_col.set_min_width(40)
        combo_col.set_resizable(True)
        combo_col.set_cell_data_func(combo_renderer, self.dtype_renderer, col_id)

        return combo_col
