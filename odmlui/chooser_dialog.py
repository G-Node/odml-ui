"""
'chooser_dialog' contains odML specific file chooser widget classes.
"""

import pygtkcompat
import gtk

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class ChooserDialog(gtk.FileChooserDialog):
    """
    The ChooserDialog class extends the gtk.FileChooserDialog class
    to enable both opening and saving of files.
    """
    def __init__(self, title, save=False):
        default_button = gtk.STOCK_OPEN
        default_action = gtk.FILE_CHOOSER_ACTION_OPEN
        if save:
            default_button = gtk.STOCK_SAVE
            default_action = gtk.FILE_CHOOSER_ACTION_SAVE

        super(ChooserDialog, self).__init__(title=title, action=default_action)

        self.add_button(default_button, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        self.save = save
        self.connect('response', self.response)

    def response(self, widget, response_id):
        """
        The 'response' method is executed when a file has been
        selected for opening or when a file path has been provided
        for saving a file. Closes and destroys the Window once its done.

        A set 'file_type' is only required for a 'on_accept: save file' callback.

        :param widget: gtk.Widget object
        :param response_id: gtk.RESPONSE signal
        """
        if response_id == gtk.RESPONSE_OK:
            self.hide()

            if self.save:
                filter_selection = widget.get_filter().get_name()
                file_type = "XML"
                if filter_selection == OdmlChooserDialog.YAML:
                    file_type = "YAML"
                elif filter_selection == OdmlChooserDialog.JSON:
                    file_type = "JSON"

                self.on_accept(self.get_uri(), file_type)
            else:
                self.on_accept(self.get_uri())

        self.destroy()

    def on_accept(self, uri, file_type=None):
        """
        This method is overridden by gi introspection. The actual method
        is set as a callback on the class at the point of usage.
        """
        pass


class OdmlChooserDialog(ChooserDialog):
    """
    The OdmlChooserDialog class extends the custom
    ChooserDialog class to handle file filters for
    all supported odML specific file types.
    """
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
        """
        Creates and provides a file filter for XML files
        and files with an '.odml' ending.

        :return: gtk.FileFilter specific for XML files.
        """
        x_fil = gtk.FileFilter()
        x_fil.set_name(self.XML)
        x_fil.add_pattern('*.xml')
        x_fil.add_pattern('*.odml')
        return x_fil

    def yaml_filter(self):
        """
        Creates and provides a file filter for YAML files
        and files with an '.odml' ending.

        :return: gtk.FileFilter specific for YAML files.
        """
        y_fil = gtk.FileFilter()
        y_fil.set_name(self.YAML)
        y_fil.add_pattern('*.yaml')
        y_fil.add_pattern('*.yml')
        y_fil.add_pattern('*.odml')
        return y_fil

    def json_filter(self):
        """
        Creates and provides a file filter for JSON files
        and files with an '.odml' ending.

        :return: gtk.FileFilter specific for JSON files.
        """
        j_fil = gtk.FileFilter()
        j_fil.set_name(self.JSON)
        j_fil.add_pattern('*.json')
        j_fil.add_pattern('*.odml')
        return j_fil

    def add_filters(self):
        """
        Adds all available class filters to the filter selection.

        If the dialog has been called with the intention to save
        a file, the filter option "All files" is added as well.
        """
        self.add_filter(self.xml_filter())
        self.add_filter(self.yaml_filter())
        self.add_filter(self.json_filter())

        if not self.save:
            all_files = gtk.FileFilter()
            all_files.set_name("All Files")
            all_files.add_pattern("*")
            self.add_filter(all_files)
