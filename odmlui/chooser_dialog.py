import pygtkcompat
import gtk

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class ChooserDialog(gtk.FileChooserDialog):
    def __init__(self, title, save):
        default_button = gtk.STOCK_SAVE if save else gtk.STOCK_OPEN
        default_action = gtk.FILE_CHOOSER_ACTION_SAVE if save else gtk.FILE_CHOOSER_ACTION_OPEN
        super(ChooserDialog, self).__init__(title=title, action=default_action)

        self.add_button(default_button, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        self.save = save
        self.connect('response', self.response)

    def response(self, widget, response_id):
        if response_id == gtk.RESPONSE_OK:
            self.hide()

            filter_selection = widget.get_filter().get_name()
            file_type = "XML"
            if filter_selection == OdmlChooserDialog.YAML:
                file_type = "YAML"
            elif filter_selection == OdmlChooserDialog.JSON:
                file_type = "JSON"

            self.on_accept(self.get_uri(), file_type)

        self.destroy()

    def on_accept(self, uri, file_type):
        """
        This method is overridden by gi introspection.
        """
        pass


class OdmlChooserDialog(ChooserDialog):
    XML = "XML format (*.xml, *.odml)"
    YAML = "YAML format (*.yaml, *.odml)"
    JSON = "JSON format (*.json, *.odml)"

    def __init__(self, title, save):
        super(OdmlChooserDialog, self).__init__(title, save)
        self.add_filters()

    @staticmethod
    def setup_file_filter(format_filter):
        """
        Used to set up filters for recently used files.
        """
        format_filter.set_name("odML Documents (*.xml, *.yaml, *.json, *.odml)")

        format_filter.add_mime_type("application/xml")
        format_filter.add_mime_type("text/xml")
        format_filter.add_pattern('*.xml')
        format_filter.add_pattern('*.yaml')
        format_filter.add_pattern('*.yml')
        format_filter.add_pattern('*.json')
        format_filter.add_pattern('*.odml')

    def xml_filter(self):
        x_fil = gtk.FileFilter()
        x_fil.set_name(self.XML)
        x_fil.add_pattern('*.xml')
        x_fil.add_pattern('*.odml')
        return x_fil

    def yaml_filter(self):
        y_fil = gtk.FileFilter()
        y_fil.set_name(self.YAML)
        y_fil.add_pattern('*.yaml')
        y_fil.add_pattern('*.yml')
        y_fil.add_pattern('*.odml')
        return y_fil

    def json_filter(self):
        j_fil = gtk.FileFilter()
        j_fil.set_name(self.JSON)
        j_fil.add_pattern('*.json')
        j_fil.add_pattern('*.odml')
        return j_fil

    def add_filters(self):
        self.add_filter(self.xml_filter())
        self.add_filter(self.yaml_filter())
        self.add_filter(self.json_filter())

        if not self.save:
            all_files = gtk.FileFilter()
            all_files.set_name("All Files")
            all_files.add_pattern("*")
            self.add_filter(all_files)
