import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk
import heapq
from . import commands


class TreeView(object):
    """
    Covers basic tasks of Treeview objects
    """
    popup = None

    def __init__(self, store=None):
        tv = gtk.TreeView(model=store)
        tv.set_headers_visible(False)

        if self.on_selection_change is not None:
            selection = tv.get_selection()
            selection.set_mode(gtk.SELECTION_BROWSE)
            selection.connect("changed", self.on_selection_change)

        if self.on_button_press is not None:
            tv.connect("button_press_event", self.on_button_press)

        # The tooltip doesn't provide any new info in the current implementation,
        # and also, it messes up with the display of properties in the "Property
        # View". Hence, disabling this temporarily.
        # if self.on_get_tooltip is not None:
        #     tv.connect('query-tooltip', self.on_query_tooltip)
        #     tv.props.has_tooltip = True

        tv.set_headers_visible(True)
        tv.set_rules_hint(True)

        self._treeview = tv

    def get_model(self):
        return self._treeview.get_model()

    def add_column(self, name, edit_func=None, id=0, data=0):
        renderer = gtk.CellRendererText()
        if edit_func:
            renderer.set_property("editable", True)
            renderer.connect("edited", edit_func, data)

        column = gtk.TreeViewColumn(name, renderer, markup=id)
        column.set_resizable(True)
        column.set_min_width(15)
        column.set_expand(True)
        self._treeview.append_column(column)
        return renderer, column

    def get_selected_object(self):
        """
        return the currently selected object

        retrieve the selection from the treeview
        and ask its model to get the object for the selected
        tree_iter
        """
        (model, tree_iter) = self._treeview.get_selection().get_selected()
        if tree_iter is None:
            return None
        return model.get_object(tree_iter)

    def get_popup_menu(self):
        return None

    def on_button_press(self, widget, event):
        if event.button == 3:  # right-click
            x = int(event.x)
            y = int(event.y)
            model = widget.get_model()
            path = widget.get_path_at_pos(x, y)
            obj = None

            if path:
                path, col, x, y = path
            else:
                path = ()

            if path:
                obj = model.on_get_iter(path)._obj

            self.popup_data = (model, path, obj)

            # Seems that the Popup menu should be persistent, hence declared it
            # as a member of *self*.
            # From this -->  https://stackoverflow.com/a/15716681
            self.popup = self.get_popup_menu()
            if self.popup is not None:
                self.popup.popup(None, None, None, None, event.button, event.time)

    def on_edited(self, widget, path, new_value, data):
        """
        a user edited a value

        now callback another method with more meaningful information
        """
        model = self._treeview.get_model()
        gtk_tree_iter = model.get_iter(path)
        tree_iter = model.on_get_iter(model.get_path(gtk_tree_iter))
        return self.on_object_edit(tree_iter, data, new_value)

    def on_query_tooltip(self, widget, x, y, keyboard_tip, tooltip):
        if widget.get_tooltip_context(x, y, keyboard_tip):
            # Now, it returns a 5-tuple value. We require first 3 only.
            model, path, iter = widget.get_tooltip_context(x, y, keyboard_tip)[3:]
            if model is None:
                return
            value = model.get(iter, 0)
            if self.on_get_tooltip(model, path, iter, tooltip) is not None:
                widget.set_tooltip_row(tooltip, path)
                return True
        return False

    on_get_tooltip = None

    def execute(self, cmd):
        cmd()

    on_selection_change = None

    def get_new_obj_name(self, siblings, prefix):
        """
            Get a uniquely indexed name of an object.
            Derives the names of new objects, like Sections and Properties,
            being created based on a common prefix. An index is appended to
            the prefix (if necessary) in a sequential manner, selecting the
            lowest index available.
        """
        new_obj_index = 0
        used_obj_num = []

        for i in siblings:
            if i.name.startswith(prefix):
                try:
                    num = int(i.name[len(prefix):])
                    heapq.heappush(used_obj_num, num)
                except ValueError:
                    # If any sibling has a name prefixed with `prefix`
                    # then the new object should have a count of at least '1'.
                    heapq.heappush(used_obj_num, 0)

        while len(used_obj_num) > 0:
            popped_ele = heapq.heappop(used_obj_num)
            if new_obj_index < popped_ele:
                break
            else:
                new_obj_index += 1

        if new_obj_index == 0:
            return prefix
        else:
            return prefix + ' ' + str(new_obj_index)


class TerminologyPopupTreeView(TreeView):
    def get_terminology_suggestions(self, obj, func):
        """
        return a list of objects

        return func(obj.terminology_equivalent())

        however if any result is None, return []
        """
        if obj is None:
            return []
        term = obj.get_terminology_equivalent()
        if term is None:
            return []
        return func(term)

    def get_popup_menu(self, func=None):
        """
        create the popup menu for this object

        calls *func* (defaults to *get_popup_menu_items*) to retrieve the actual
        items for the menu
        """
        if func is None:
            func = self.get_popup_menu_items

        popup = gtk.Menu()
        for i in func():
            popup.append(i)
            i.show()
        popup.show()
        return popup

    def get_popup_menu_items(self):
        """
        to be implemented by a concrete TreeView

        returns a list of gtk.MenuItem to be displayed in a popup menu
        """
        raise NotImplementedError

    def on_delete(self, widget, obj):
        """
        called for the popup menu action delete
        """
        cmd = commands.DeleteObject(obj=obj)
        self.execute(cmd)

    def create_popup_menu_del_item(self, obj):
        return self.create_menu_item("Delete %s" % repr(obj), self.on_delete, obj)

    def create_menu_item(self, name, func=None, data=None, stock=None):
        """
        Creates a single menu item
        """
        # Now *stock* refers to the stock-id, and not whether to use a
        # Stock Item or not. This issue is due to the failing in registering
        # stock items, as they were being done in PyGTK. The label is not
        # automatically derived from the stock item now, hence the *name*
        # becomes the Label of the menu item.
        if stock:
            item = gtk.ImageMenuItem.new_from_stock(stock, None)
            item.set_label(name)
        else:
            item = gtk.MenuItem.new_with_label(name)
        if func is not None:
            item.connect('activate', func, data)
        item.show()
        return item

    def create_popup_menu_items(self, add_name, empty_name, obj, func, terminology_func, name_func, stock=None):
        """
        create menu items for a popup menu

        * *add_name* is a menu item text e.g. ("Add Section")
        * *empty_name* is a menu item text e.g. ("Empty Section")
        * *obj* is the parent object to which to add the data
        * *func* is the target function that is called upon click action:
            func(widget, (obj, val)) where *val* is the template value or None
        * *terminology_func* is passed to *get_terminology_suggestions* and used to extract the relevant
          suggestions of a terminology object (e.g. lambda section: section.properties)
        * *name_func* is a function the create a menu-item label from an object (e.g. lambda prop: prop.name)
        * *stock* is the stock-id of the resource to use

        returns an array of gtk.MenuItem
        """
        add_section = self.create_menu_item(add_name, stock=stock)

        terms = self.get_terminology_suggestions(obj, terminology_func)
        if len(terms) == 0:
            add_section.connect('activate', func, (obj, None))
            return [add_section]

        menu = gtk.Menu()
        terms = [(name_func(sec), sec) for sec in terms]

        # DOUBT :- Why was there a (None, None) part in the below list ??
        for name, val in [(empty_name, None)] + terms:
            menu.append(self.create_menu_item(name, func, (obj, val)))

        menu.show()
        add_section.set_submenu(menu)
        return [add_section]

    def save_state(self):
        """
        return the current state (i.e. expanded and selected objects)
        that can be restored with restore_state later
        """

        model = self._treeview.get_model()
        if model is None:
            return
        exp_rows = []

        def get_expanded_rows(model, path, iter, data=None):
            if self._treeview.row_expanded(path):
                exp_rows.append(path.copy())
            return False

        model.foreach(get_expanded_rows)
        model, selected_rows = self._treeview.get_selection().get_selected_rows()
        return exp_rows, selected_rows

    def restore_state(self, state):
        """
        restore a state saved by save_state
        """
        if state is None:
            return
        exp_rows, selected_rows = state
        selection = self._treeview.get_selection()

        for row in exp_rows:
            self._treeview.expand_row(row, False)

        for row in selected_rows:
            selection.select_path(row)

    def select_object(self, obj, expand=True):
        """
        change current the selection to *obj*, i.e. navigate there

        if expand is set, the selection
        """
        model = self._treeview.get_model()
        path = model.get_node_path(obj)
        if not path:
            return
        path = gtk.TreePath.new_from_indices(path)

        if expand:
            self._treeview.expand_to_path(path)

        selection = self._treeview.get_selection()
        selection.select_path(path)
