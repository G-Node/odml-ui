import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk


class ChooserDialog(gtk.FileChooserDialog):
    def __init__(self, title, save):
        default_button = gtk.STOCK_SAVE if save else gtk.STOCK_OPEN
        default_action = gtk.FILE_CHOOSER_ACTION_SAVE if save else gtk.FILE_CHOOSER_ACTION_OPEN
        super(ChooserDialog, self).__init__(
                title=title,
                action=default_action)
        self.add_button(default_button, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        self.save = save
        self.connect('response', self.response)

    def response(self, widget, response_id):
        if response_id == gtk.RESPONSE_OK:
            self.hide()

            filter_selection = widget.get_filter().get_name()
            file_type = "XML"
            if filter_selection == odMLChooserDialog.YAML:
                file_type = "YAML"
            elif filter_selection == odMLChooserDialog.JSON:
                file_type = "JSON"

            self.on_accept(self.get_uri(), file_type)

        self.destroy()

    def on_accept(self, uri, file_type):
        raise NotImplementedError


class odMLChooserDialog(ChooserDialog):
    XML = "XML format (*.xml, *.odml)"
    YAML = "YAML format (*.yaml, *.odml)"
    JSON = "JSON format (*.json, *.odml)"

    def __init__(self, title, save):
        super(odMLChooserDialog, self).__init__(title, save)
        self.add_filters()

    @staticmethod
    def _setup_file_filter(filter):
        """
             Used for setting up recent filters for recently used files.
        """
        filter.set_name("odML Documents (*.xml, *.yaml, *.json, *.odml)")

        filter.add_mime_type("application/xml")
        filter.add_mime_type("text/xml")
        filter.add_pattern('*.xml')
        filter.add_pattern('*.yaml')
        filter.add_pattern('*.yml')
        filter.add_pattern('*.json')
        filter.add_pattern('*.odml')

    def xml_filter(self):
        filter = gtk.FileFilter()
        filter.set_name(self.XML)
        filter.add_pattern('*.xml')
        filter.add_pattern('*.odml')
        return filter

    def yaml_filter(self):
        filter = gtk.FileFilter()
        filter.set_name(self.YAML)
        filter.add_pattern('*.yaml')
        filter.add_pattern('*.yml')
        filter.add_pattern('*.odml')
        return filter

    def json_filter(self):
        filter = gtk.FileFilter()
        filter.set_name(self.JSON)
        filter.add_pattern('*.json')
        filter.add_pattern('*.odml')
        return filter

    def add_filters(self):
        self.add_filter(self.xml_filter())
        self.add_filter(self.yaml_filter())
        self.add_filter(self.json_filter())

        if not self.save:
            all_files = gtk.FileFilter()
            all_files.set_name("All Files")
            all_files.add_pattern("*")
            self.add_filter(all_files)
