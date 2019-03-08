"""
The 'wizard' module provides all classes that are required
to create a new empty document or a selection of Sections and
Properties from an odML terminology.
"""

import datetime

from collections import OrderedDict

import pygtkcompat

import odml
import odml.terminology as terminology

import gtk

from .helpers import handle_property_import, get_username
from .treemodel.section_model import SectionModel
from .section_view import SectionView
from .scrolled_window import ScrolledWindow

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class Table(object):
    """
    Table containing 'Label'-'Entry' rows
    """

    def __init__(self, cols):
        self.table = gtk.Table(n_rows=1, n_columns=cols)
        self.cols = cols
        self.rows = 0

    def append(self, fill, *cols):
        """
        Appends a gtk.Entry field with its corresponding
        label to the table content.

        :param fill: gtk.Entry
        :param cols: Label and Entry columns
        """
        if fill is None:
            fill = []

        self.table.resize(rows=self.rows+1, columns=self.cols)
        for i, widget in enumerate(cols):
            xoptions = gtk.EXPAND | gtk.FILL if widget in fill else 0
            self.table.attach(widget, i, i+1, self.rows, self.rows+1, xoptions=xoptions)
        self.rows += 1


class Page(gtk.VBox):
    """
    Content container of individual steps in a gtk.Assistant.
    """

    type = gtk.ASSISTANT_PAGE_CONTENT
    complete = True

    def __init__(self, *args, **kargs):
        super(Page, self).__init__(*args, **kargs)
        self.set_border_width(5)

    def deploy(self, assistant, title):
        """
        Used to append the Page instance to a gtk.Assistant.

        :param assistant: gtk.Assistant
        :param title: String displayed as the Page instances title
        """
        page = assistant.append_page(self)
        assistant.set_page_title(self, title)
        assistant.set_page_type(self, self.type)
        assistant.set_page_complete(self, self.complete)

        return page

    def prepare(self, assistant, prev_page):
        """
        Called when to set up any required information before
        the page itself is displayed.

        The actual method is set on the class at the point of usage.
        """
        pass

    def finalize(self):
        """
        Called when moving to the next gtk.Assistant step to process
        information from the current page.

        The actual method is set on the class at the point of usage.
        """
        pass


class DataPage(Page):
    """
    First page of the wizard collecting general document
    information and setting the URL of the terminology
    repository of interest.
    """

    def __init__(self, *args, **kargs):
        super(DataPage, self).__init__(*args, **kargs)

        self.table = Table(cols=2)
        # Put the data area in center, fill only horizontally
        align = gtk.Alignment(0.5, 0.5, xscale=1.0)
        self.add(align)

        self.data = {}

        fields = OrderedDict()
        fields["Author"] = get_username()
        fields["Date"] = datetime.date.today().isoformat()
        fields["Version"] = "1.0"
        fields["Repository"] = terminology.REPOSITORY
        self.fields = fields

        # Add a label and an entry box for each field
        for key, val in fields.items():
            label = gtk.Label(label="%s: " % key)
            label.set_alignment(1, 0.5)
            entry = gtk.Entry()
            entry.set_text(val)
            setattr(self, key.lower(), entry)
            self.table.append([entry], label, entry)

        align.add(self.table.table)

        # Already fetch the default terminology data in the background
        terminology.terminologies.deferred_load(fields["Repository"])

    def finalize(self):
        """
        Setting the pages' data dictionary with the content
        of the pages' entry form.
        """
        self.data = {}
        for k in self.fields:
            self.data[k.lower()] = getattr(self, k.lower()).get_text()


class CheckableSectionView(SectionView):
    """
    A TreeView showing all the documents' sections of a terminology
    together with Checkboxes, allowing to select subsets of it.
    """
    def __init__(self, *args, **kargs):
        super(CheckableSectionView, self).__init__(*args, **kargs)

        # Add a column for the toggle button
        renderer = gtk.CellRendererToggle()
        renderer.connect("toggled", self.toggled)

        column = gtk.TreeViewColumn(None, renderer)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_cell_data_func(renderer, self.celldatamethod)

        self._treeview.insert_column(column, 0)
        self._treeview.set_expander_column(self._treeview.get_column(1))
        self.sections = {}

    @property
    def tree_view(self):
        """
        Getter of the private *_tree_view* attribute.
        """
        return self._treeview

    def celldatamethod(self, column, cell, model, sec_iter, _):
        """
        Custom method to set the active state via the gtk CellRenderer
        for the classes gtk TreeViewColumn.
        """
        sec = model.get_object(sec_iter)
        cell.set_active(self.sections.get(sec, False))

    def toggled(self, renderer, path):
        """
        Selecting or unselecting items recursively in the
        classes TreeView. Selecting an item also selects
        all child items recursively and all direct parent items.

        :param renderer: gtk.CellRendererToggle
        :param path: string containing a gtk style TreePath to the selected item
        """
        active = not renderer.get_active()

        model = self._treeview.get_model()
        path_iter = model.get_iter(path)
        obj = model.get_object(path_iter)

        # Checking a section, includes/excludes all subsections by default
        for sec in obj.itersections(recursive=True, yield_self=True):
            self.set_active(sec, active)

        # If activating a section, all parent sections must be included too
        sec = obj
        if active and hasattr(sec, "parent"):
            while sec.parent is not None:
                sec = sec.parent
                self.set_active(sec, active)

    def set_active(self, sec, active):
        """
        Marks an item as active/inactive and triggers
        the corresponding TreeView actions.
        """
        self.sections[sec] = active
        model = self.get_model()
        path = model.get_node_path(sec)
        if not path:
            return
        model.row_changed(path, model.get_iter(path))


class SectionPage(Page):
    """
    A gtk.Assistant page loading and preparing odML sections
    for selection from a provided terminology.
    """

    def __init__(self, *args, **kargs):
        super(SectionPage, self).__init__(*args, **kargs)
        self.view = CheckableSectionView(None)

        vbox = gtk.VBox()

        message_lbl = gtk.Label()
        vbox.pack_start(message_lbl, False, False, 5)

        scroll_win = ScrolledWindow(self.view.tree_view)
        vbox.add(scroll_win)

        self.pack_start(vbox, True, True, 0)
        self.term = None
        self.error = message_lbl

    def prepare(self, assistant, prev_page):
        """
        Loading the terminology defined in the first step into
        an odML document and presenting it via the *CheckableSectionView*.

        :param assistant: *gtk.Assistant*
        :param prev_page: *DataPage* containing the terminology URL.
        """
        reset = True
        self.error.set_text("")

        data = prev_page.data
        if "repository" in data.keys() and data["repository"].strip():
            try:
                self.term = terminology.terminologies.load(data["repository"])
                self.view.set_model(SectionModel(self.term))
                reset = False
            except AssertionError:
                # Handle terminology loading error
                self.error.set_text("Could not load terminology '%s'" %
                                    data["repository"])

        if reset:
            # Reset view on empty terminology repository
            self.term = None
            self.view.set_model(None)

    @property
    def sections(self):
        """
        Returning all selected sections selected in widgets'
        CheckableSectionView in the order as they are found
        in the terminology.

        :return: generator of all selected terminology sections.
        """
        for sec in self.term.itersections(recursive=True):
            if self.view.sections.get(sec, False):
                yield sec


class SummaryPage(Page):
    """
    Final gtk.Assistant page
    """
    type = gtk.ASSISTANT_PAGE_CONFIRM

    def __init__(self, *args, **kargs):
        super(SummaryPage, self).__init__(*args, **kargs)

        msg = "All information has been gathered. Ready to create document."
        self.add(gtk.Label(label=msg))


class DocumentWizard:
    """
    Main window managing and providing the different steps
    to create a new empty odML document or a document with
    Sections selected from an odML Terminology repository.
    """

    def __init__(self):
        assistant = gtk.Assistant()

        assistant.set_title("New odML-Document wizard")
        assistant.set_default_size(800, 500)
        assistant.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        assistant.connect("apply", self.apply)
        assistant.connect("close", self.cancel)
        assistant.connect("cancel", self.cancel)

        # General information and URL to a terminology repository
        data_page = DataPage()
        data_page.deploy(assistant, "Document information")
        self.data_page = data_page

        # Page displaying terminology sections available for import
        # via the terminology URL in the DataPage.
        section_page = SectionPage()
        section_page.data = data_page
        section_page.deploy(assistant, "Repository section import")
        self.section_page = section_page

        # Wrap up page before the new document is created
        SummaryPage().deploy(assistant, "Complete")

        assistant.connect("prepare", self.prepare)
        assistant.show_all()

    def prepare(self, assistant, page):
        """
        Wizard navigation method handling 'Next' and 'Back' actions.

        :param assistant: gtk.Assistant
        :param page: requested wizard page.
        """
        last_page_idx = assistant.get_current_page()-1
        prev_page = None

        if last_page_idx >= 0:
            prev_page = assistant.get_nth_page(last_page_idx)
            prev_page.finalize()

        return page.prepare(self, prev_page)

    def cancel(self, assistant):
        """
        Call the cleanup method and close the wizard.
        """
        self.cleanup()
        assistant.destroy()

    def cleanup(self):
        """
        Reset the main window view in case no new document is created
        when exiting the wizard.

        The actual method is set on the class at the point of usage.
        """
        raise NotImplementedError

    def apply(self, _):
        """
        The process is finished, create the new document empty or with
        any selected Terminology Sections.
        """
        doc = odml.Document()

        # Set the document attributes with data from the first page
        for key, val in self.data_page.data.items():
            setattr(doc, key, val)

        # All selected sections and their properties need to be cloned from the
        # terminology and added at the appropriate position in the new document tree.
        if hasattr(self.section_page, "term") and self.section_page.term:
            term = self.section_page.term

            # Use terminology as scaffold to create the new document
            term.new_doc_sec = doc
            for term_sec in term.itersections(recursive=True):
                if term_sec not in self.section_page.sections:
                    continue

                new_sec = term_sec.clone(children=False)
                for prop in term_sec.properties:
                    cprop = prop.clone()

                    # All new properties need to be adjusted to odml-ui needs!
                    handle_property_import(cprop)

                    new_sec.append(cprop)

                term_sec.new_doc_sec = new_sec
                if hasattr(term_sec.parent, "new_doc_sec"):
                    term_sec.parent.new_doc_sec.append(new_sec)

        self.finish(doc)

    def finish(self, document):
        """
        Callback method in the main window setting the document in
        a new tab once the wizard is done.

        The actual method is set on the class at the point of usage.
        """
        raise NotImplementedError
