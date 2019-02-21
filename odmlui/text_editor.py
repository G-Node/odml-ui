import pygtkcompat

import gtk

from .scrolled_window import ScrolledWindow

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class TextEditor(gtk.Window):
    def __init__(self, obj, attr):
        super(TextEditor, self).__init__()
        self.obj = obj
        self.attr = attr
        self.set_title("Editing %s.%s" % (repr(obj), attr))
        self.set_default_size(400, 600)
        self.connect('destroy', self.on_close)

        self.text = gtk.TextView()
        buffer = self.text.get_buffer()
        buffer.set_text(getattr(obj, attr))

        self.add(ScrolledWindow(self.text))
        self.show_all()

    def on_close(self, window):
        from . import commands
        buffer = self.text.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end)
        cmd = commands.ChangeValue(object=self.obj, attr=self.attr, new_value=text)
        self.execute(cmd)

    def execute(self, cmd):
        cmd()


if __name__ == "__main__":
    class StandAloneTextEditor(object):
        _prop_a = "no text"

        @property
        def prop_a(self):
            print("read prop a")
            return self._prop_a

        @prop_a.setter
        def prop_a(self, new_value):
            print("set a to ", repr(new_value))
            self._prop_a = new_value

    _ = TextEditor(StandAloneTextEditor(), "prop_a")
    gtk.mainloop()
