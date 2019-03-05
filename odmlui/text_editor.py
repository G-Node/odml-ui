"""
'text_editor' provides a simple TextEditor Window class.
"""

import pygtkcompat

import gtk

from .commands import ChangeValue
from .scrolled_window import ScrolledWindow
from .treemodel.value_model import Value

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class TextEditor(gtk.Window):
    """
    TextEditor is a simple text editor window that
    reads the value of a passed objects attribute
    and overwrites this attributes value with the content
    of the editor when the window is closed.
    """
    def __init__(self, obj, attr):
        super(TextEditor, self).__init__()
        self.obj = obj

        # The 'value' attribute of the Values Class
        # can only be set via the 'pseudo_values' attribute.
        # We need to account for this particularity.
        if isinstance(obj, Value) and attr == "value":
            attr = "pseudo_values"

        self.attr = attr
        self.set_title("Editing %s" % repr(obj))
        self.set_default_size(600, 600)

        # Text container
        self.text = gtk.TextView()
        text_buffer = self.text.get_buffer()
        text_buffer.set_text(getattr(obj, attr))
        text_container = ScrolledWindow(self.text)

        # Main window container. Using the recommended gtk.Box with
        # gtk.ORIENTATION_VERTICAL fails so we stick
        # to the deprecated VBox for now.
        vbox = gtk.VBox()
        vbox.pack_start(text_container)

        # Button Container
        hbox = gtk.Box(gtk.ORIENTATION_HORIZONTAL)
        save = gtk.Button("Save")
        save.connect('clicked', self.on_ok)
        hbox.add(save)

        cancel = gtk.Button("Cancel")
        cancel.connect('clicked', self.on_cancel)
        hbox.add(cancel)

        h_align = gtk.Alignment(1, 0, 0, 0)
        h_align.add(hbox)

        vbox.pack_start(h_align, False, False)

        self.add(vbox)

        self.show_all()

    def on_cancel(self, _):
        """
        Close widget w/o doing anything
        """
        self.destroy()

    def on_ok(self, _):
        """
        Reads the text buffer value, and updates
        the target object with the new value via
        a command.ChangeValue object.
        """
        text_buffer = self.text.get_buffer()
        start, end = text_buffer.get_bounds()
        include_hidden_text = False
        text = text_buffer.get_text(start, end, include_hidden_text)
        cmd = ChangeValue(object=self.obj, attr=self.attr, new_value=text)
        cmd()

        self.destroy()
