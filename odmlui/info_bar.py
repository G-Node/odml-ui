import pygtkcompat
import glib
import gtk

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class EditorInfoBar(gtk.InfoBar):
    default_timeout = 10

    def __init__(self, *args, **kargs):
        gtk.InfoBar.__init__(self, *args, **kargs)
        self._msg_label = gtk.Label(label="")
        self._msg_label.show()
        self.get_content_area().pack_start(self._msg_label, True, True, 0)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        self.connect("response", self._on_response)
        self._timerid = 0

    def _on_response(self, widget, response_id):
        if self == widget and response_id == gtk.RESPONSE_OK:
            if self._timerid > 0:
                glib.source_remove(self._timerid)
                self._timerid = 0
            self.hide()

    def show_info(self, text):
        self._msg_label.set_text(text)
        self.set_message_type(gtk.MESSAGE_INFO)
        self.show()
        time_delay = max(int(3.0 * len(text) / 60), self.default_timeout)
        self._add_timer(time_delay)

    def _add_timer(self, seconds=default_timeout):
        self._timerid = glib.timeout_add_seconds(seconds, self._on_timer)

    def _on_timer(self):
        self.hide()
        self._timerid = 0
