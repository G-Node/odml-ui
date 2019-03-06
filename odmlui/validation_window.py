"""
This module contains all classes to display validation messages
"""

import sys

import pygtkcompat

import gtk

from .scrolled_window import ScrolledWindow
from .tree_view import TreeView

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

COL_PATH = 0
COL_INDEX = 1
COL_DESC = 2


class ValidationView(TreeView):
    """
    A two-column TreeView to display messages of an odml document validation.
    """
    def __init__(self):
        self._store = gtk.ListStore(str, int, str)

        super(ValidationView, self).__init__(self._store)

        self.errors = []

        self.add_column(name="Path", data=COL_PATH, col_id=COL_PATH)
        self.add_column(name="Description", data=COL_DESC, col_id=COL_DESC)

        curr_view = self._treeview
        curr_view.show()

    def set_errors(self, errors):
        """
        Update the widgets *error* attribute with the provided list of
        validation message objects and call the widgets *fill* method.
        :param errors: List of validation messages
        """
        self.errors = errors
        self.fill()

    def fill(self):
        """
        *fill* populates the widgets store from the widgets *errors*.
        The store is populated with the path of the odml object
        eliciting the message, the message severity and the validation message.
        """
        self._store.clear()
        warn = "\u26A0"
        if sys.version_info.major < 3:
            warn = warn.decode('unicode-escape')

        elements = [(err.path, j, err.msg, err.is_error)
                    for j, err in enumerate(self.errors)]
        elements.sort()

        for (path, idx, msg, is_error) in elements:
            if not is_error:
                path = "<span foreground='darkgrey'>%s</span>" % path

            msg = "<span foreground='%s'>%s</span> " % \
                  ("red" if is_error else "orange", warn) + msg
            self._store.append((path, idx, msg))

    def on_selection_change(self, tree_selection):
        """
        Called when an object in the validation window is selected.

        Elicits the selection of the corresponding odml object in
        the editor tab.
        """
        (_, tree_iter) = tree_selection.get_selected()
        index = self._store.get_value(tree_iter, COL_INDEX)
        self.on_select_object(self.errors[index].obj)

    def on_select_object(self, obj):
        """
        Called whenever an object in the validation window is selected.

        The actual method is set on the class at the point of usage.
        """
        raise NotImplementedError

    def get_tree_view(self):
        """
        Return the widgets tree view
        """
        return self._treeview


class ValidationWindow(gtk.Window):
    """
    A scrollable window containing a ValidationView.
    The size of the window is adjusted to the
    number of elements in the ValidationView.
    """
    max_height = 768
    max_width = 1024

    def __init__(self, tab):
        super(ValidationWindow, self).__init__()
        self.tab = tab
        self.set_title("Validation errors in %s" % tab.get_name())

        self.connect('delete_event', self.on_close)

        self.curr_view = ValidationView()
        self.curr_view.on_select_object = tab.window.navigate
        self.curr_view.set_errors(tab.document.validation_result.errors)

        tree_view = self.curr_view.get_tree_view()
        self.add(ScrolledWindow(tree_view))

        # required for updated size in 'tree_view.size_request()'
        tree_view.check_resize()
        width, height = tree_view.size_request()
        width = min(width + 10, self.max_width)
        height = min(height + 10, self.max_height)

        self.resize(width, height)

        self.show_all()

    def on_close(self, widget, _):
        """
        *on_close* calls the *remove_validation* method of
        the tab the validation was called for.
        """
        ValidationWindow.width, ValidationWindow.height = self.get_size()
        self.tab.remove_validation()
