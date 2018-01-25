import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk
import sys
from .ScrolledWindow import ScrolledWindow
from .TreeView import TreeView

COL_PATH = 0
COL_INDEX = 1
COL_DESC = 2


class ValidationView(TreeView):
    """
    A two-column TreeView to display the validation errors
    """
    def __init__(self):
        self._store = gtk.ListStore(str, int, str)

        super(ValidationView, self).__init__(self._store)

        for i, name in ((COL_PATH, "Path"), (COL_DESC, "Description")):
            self.add_column(name=name, data=i, id=i)

        tv = self._treeview
        tv.show()

    def set_errors(self, errors):
        self.errors = errors
        self.fill()

    def fill(self):
        self._store.clear()
        warn = "\u26A0"
        if sys.version_info.major < 3:
            warn = warn.decode('unicode-escape')

        elements = [(err.path, j, err.msg, err.is_error) for j, err in enumerate(self.errors)]
        elements.sort()
        for (path, idx, msg, is_error) in elements:
            if not is_error:
                path = "<span foreground='darkgrey'>%s</span>" % path
            msg = "<span foreground='%s'>%s</span> " % ("red" if is_error else "orange", warn) + msg
            self._store.append((path, idx, msg))

    def on_selection_change(self, tree_selection):
        """
        select the corresponding object in the editor upon a selection change
        """
        (model, tree_iter) = tree_selection.get_selected()
        index = self._store.get_value(tree_iter, COL_INDEX)
        self.on_select_object(self.errors[index].obj)

    def on_select_object(self, obj):
        raise NotImplementedError


class ValidationWindow(gtk.Window):
    max_height = 768
    max_width = 1024
    height = max_height
    width = max_width

    def __init__(self, tab):
        super(ValidationWindow, self).__init__()
        self.tab = tab
        self.set_title("Validation errors in %s" % tab.get_name())

        self.connect('delete_event', self.on_close)

        self.tv = ValidationView()
        self.tv.on_select_object = tab.window.navigate
        self.tv.set_errors(tab.document.validation_result.errors)

        self.add(ScrolledWindow(self.tv._treeview))
        self.tv._treeview.check_resize()  # required for updated size in 'treeview.size_request()'
        width, height = self.tv._treeview.size_request()
        width = min(width+10, max(self.width, self.max_width))
        height = min(height+10, max(self.height, self.max_height))
        self.set_default_size(width, height)

        self.show_all()

    def on_close(self, window, data=None):
        ValidationWindow.width, ValidationWindow.height = self.get_size()
        self.tab.remove_validation()

    def execute(self, cmd):
        cmd()


if __name__ == "__main__":
    from odml.validation import Validation
    from odml.tools.odmlparser import ODMLReader

    class Tab:  # a small mock object
        document = ODMLReader("JSON").from_string("""
{
    "odml-version": "1.1",
    "Document": {
        "sections": [{
                "sections": [],
                "properties": [
                    {
                        "dtype": "string",
                        "name": "Unnamed Property",
                        "value": [""]
                    },{
                        "dtype": "string",
                        "name": "Unnamed Property 1",
                        "value": [""]
                    }
                ],
                "name": "Unnamed Section"
        }]
    }
}
""")

        def get_name(self):
            return "animal_keeping.odml"

        class Window:
            navigate = None

    tab = Tab()
    tab.document.validation_result = Validation(tab.document)
    for err in tab.document.validation_result.errors:
        print(err.path, err.msg)
    x = ValidationWindow(tab)
    gtk.mainloop()
