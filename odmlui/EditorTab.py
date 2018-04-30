import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk
import os.path

import odml
import odml.validation
from odml.tools.odmlparser import ODMLReader, ODMLWriter
from odml.tools.parser_utils import InvalidVersionException
from odml.tools.version_converter import VersionConverter

from .CommandManager import CommandManager
from .Helpers import uri_to_path, get_parser_for_uri, get_extension, \
    create_pseudo_values, get_parser_for_file_type
from .MessageDialog import ErrorDialog
from .treemodel import event
from .ValidationWindow import ValidationWindow


class EditorTab(object):
    """
    Represents a Document Object in the Editor
    """
    file_uri = None
    edited = 0

    def __init__(self, window, cmdm=None):
        if cmdm is None:
            cmdm = CommandManager()
            cmdm.enable_undo = self.enable_undo
            cmdm.enable_redo = self.enable_redo
            cmdm.error_func = window.command_error
        self.command_manager = cmdm
        self.document = None
        self.window = window
        self._clones = [self]

    def new(self, doc=None):
        """
        initialize a new document
        """
        if doc is None:
            doc = odml.Document()
            sec = odml.Section(name="Default Section")
            doc.append(sec)

        self.window.registry.add(doc)

        self.document = doc
        self.file_uri = None

    def parse_properties(self, odml_sections):
        for i in odml_sections:
            create_pseudo_values(i.properties)
            self.parse_properties(i.sections)

    def load(self, uri):
        self.file_uri = uri
        file_path = uri_to_path(uri)
        parser = get_parser_for_uri(file_path)
        odml_reader = ODMLReader(parser=parser)
        try:
            self.document = odml_reader.from_file(file_path)
        except InvalidVersionException as inver:
            _, curr_file = os.path.split(file_path)
            err_header = "Cannot open file '%s'." % curr_file
            err_msg = ("You are trying to open an odML file of an outdated format. "
                       "\n\nUse 'File .. import' to convert and open files of "
                       "a previous odML format.")
            ErrorDialog(self.window, err_header, err_msg)
            return False

        except Exception as e:
            ErrorDialog(self.window, "Error parsing '%s'" % file_path, str(e))
            if len(self.window.notebook) < 1:
                self.window.welcome()
            return False

        self.document.finalize()
        self.parse_properties(self.document.sections)
        self.window.registry.add(self.document)
        self.window._info_bar.show_info("Loading of %s done!" % (os.path.basename(file_path)))
        return True

    def convert(self, uri):
        """
        Convert a previous odML version to the current one. If the file can be
        successfully converted, it is saved with the old filename and the
        postfix '_converted' in the xml format and immediately loaded into a new tab.

        :param uri: uri of the conversion candidate file.
        :return: True if loading worked, False if any conversion or loading errors occur.
        """
        file_path = uri_to_path(uri)
        parser = get_parser_for_uri(file_path)
        vconv = VersionConverter(file_path)

        # Currently we can only convert to xml out of the box,
        # so don't bother about the extension.
        file_name = os.path.basename(file_path)
        new_file_name = "%s_converted.xml" % os.path.splitext(file_name)[0]
        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

        try:
            vconv.write_to_file(new_file_path, parser)
        except Exception as err:
            err_header = "Error converting file '%s'." % file_name
            ErrorDialog(self.window, err_header, str(err))
            return False

        # TODO display conversion warnings

        # When we have written, we can load!
        return self.load(new_file_path)

    def reset(self):
        self.edited = 0  # initialize the edit stack position
        self.command_manager.reset()
        self.enable_undo(enable=False)
        self.enable_redo(enable=False)

    @property
    def is_modified(self):
        return self.edited != len(self.command_manager)

    def save_if_changed(self):
        """
        if the document was modified, ask the user if he or she wants to save the document

        returns false if the user cancelled the action
        """
        if not self.is_modified:
            return True

        msg = "%s has been modified. Do you want to save your changes?" % (
            self.file_uri if self.file_uri is not None else "The document")

        dialog = gtk.MessageDialog(transient_for=self.window,
                                   modal=True,
                                   message_type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_YES_NO,
                                   text=msg)

        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.set_title("Save changes?")
        dialog.set_default_response(gtk.RESPONSE_CANCEL)

        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_CANCEL:
            return False
        if response == gtk.RESPONSE_NO:
            return True
        return self.window.save(None)

    def save(self, uri, file_type=None):
        # Mandatory document validation before save to avoid
        # not being able to open an invalid document.
        self.remove_validation()
        validation = odml.validation.Validation(self.document)
        self.document.validation_result = validation

        for e in self.document.validation_result.errors:
            if e.is_error:
                self.window._info_bar.show_info("Invalid document. Please fix errors (red) before saving.")
                self.validate()
                return

        self.document.clean()

        parser = None
        if file_type:
            parser = get_parser_for_file_type(file_type)

        if not parser:
            parser = get_parser_for_uri(uri)

        odml_writer = ODMLWriter(parser=parser)
        file_path = uri_to_path(uri)
        ext = get_extension(file_path)

        if ext != parser:
            file_path += ".%s" % parser.lower()

        try:
            odml_writer.write_file(self.document, file_path)
        except Exception as e:
            self.window._info_bar.show_info("Save failed: %s" % e)
            return

        self.document.finalize()  # undo the clean
        self.window._info_bar.show_info("%s was saved" % (os.path.basename(file_path)))
        self.edited = len(self.command_manager)
        return True  # TODO return false on any error and notify the user

    def enable_undo(self, enable=True):
        for tab in self._clones:
            tab._enable_undo(enable)

    def _enable_undo(self, enable):
        if self.window.current_tab is self:
            self.window.enable_undo(enable)

    def enable_redo(self, enable=True):
        for tab in self._clones:
            tab._enable_redo(enable)

    def _enable_redo(self, enable=True):
        if self.window.current_tab is self:
            self.window.enable_redo(enable)

    def clone(self, klass=None):
        if klass is None:
            klass = self.__class__
        ntab = klass(self.window, self.command_manager)
        self._clones.append(ntab)
        ntab._clones = self._clones
        ntab.file_uri = self.file_uri
        ntab.document = self.document
        return ntab

    def validate(self):
        """check the document for errors"""
        self.remove_validation()
        validation = odml.validation.Validation(self.document)
        self.document.validation_result = validation
        if len(validation.errors) > 0:
            self.update_validation_error_objects(validation.errors)
            ValidationWindow(self).show()
        else:
            self.window._info_bar.show_info("The document is valid. No errors found.")
            self.remove_validation()

    def update_validation_error_objects(self, errors):
        """
        send out a change event for all error-affected objects
        so that the gui can refresh these
        """
        for err in errors:
            c = event.ChangeContext(('_error', True))
            c.post_change = True
            c.action = "set"
            c.pass_on(err.obj)

    def remove_validation(self):
        """remove any dangling validation references"""
        if not hasattr(self.document, "validation_result"):
            return
        errors = self.document.validation_result.errors
        del self.document.validation_result
        self.update_validation_error_objects(errors)

    def get_name(self):
        """return the filename of this tab's document"""
        return os.path.basename(str(self.file_uri))

    def update_label(self):
        """update the tab label with the current filename"""
        self.label.set_text(self.get_name())

    def close(self):
        """
        any cleanup?
        """
        self._clones.remove(self)
