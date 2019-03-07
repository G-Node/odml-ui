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
    def __init__(self, cols):
        self.table = gtk.Table(n_rows=1, n_columns=cols)
        self.cols = cols
        self.rows = 0

    def append(self, fill, *cols):
        if fill is None:
            fill = []

        self.table.resize(rows=self.rows+1, columns=self.cols)
        for i, widget in enumerate(cols):
            xoptions = gtk.EXPAND | gtk.FILL if widget in fill else 0
            self.table.attach(widget, i, i+1, self.rows, self.rows+1, xoptions=xoptions)
        self.rows += 1


class Page(gtk.VBox):
    type = gtk.ASSISTANT_PAGE_CONTENT
    complete = True

    def __init__(self, *args, **kargs):
        super(Page, self).__init__(*args, **kargs)
        self.set_border_width(5)

    def deploy(self, assistant, title):
        page = assistant.append_page(self)
        assistant.set_page_title(self, title)
        assistant.set_page_type(self, self.type)
        assistant.set_page_complete(self, self.complete)
        return page

    def prepare(self, assistant, prev_page):
        """
        called before actually showing the page, but after all previous pages
        have finished
        """
        pass

    def finalize(self):
        """
        called to finish processing the page and allow it to collect all entered data
        """
        pass


class DataPage(Page):
    def __init__(self, *args, **kargs):
        super(DataPage, self).__init__(*args, **kargs)

        self.table = Table(cols=2)
        # put the data area in center, fill only horizontally
        align = gtk.Alignment(0.5, 0.5, xscale=1.0)
        self.add(align)

        self.data = {}

        fields = OrderedDict()
        fields["Author"] = get_username()
        fields["Date"] = datetime.date.today().isoformat()
        fields["Version"] = "1.0"
        fields["Repository"] = terminology.REPOSITORY
        self.fields = fields

        # add a label and an entry box for each field
        for key, val in fields.items():
            label = gtk.Label(label="%s: " % key)
            label.set_alignment(1, 0.5)
            entry = gtk.Entry()
            entry.set_text(val)
            setattr(self, key.lower(), entry)
            self.table.append([entry], label, entry)

        align.add(self.table.table)
        # already load the data in background
        terminology.terminologies.deferred_load(fields["Repository"])

    def finalize(self):
        """read the data from the corresponding labels"""
        self.data = {}
        for k in self.fields:
            self.data[k.lower()] = getattr(self, k.lower()).get_text()


class CheckableSectionView(SectionView):
    """
    A TreeView showing all the documents sections of a terminology
    together with Checkboxes, allowing to select subsets of it
    """
    def __init__(self, *args, **kargs):
        super(CheckableSectionView, self).__init__(*args, **kargs)
        # add a column for the toggle button
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
        return self._treeview

    def celldatamethod(self, column, cell, model, sec_iter, _):
        """
        custom method to set the active state for the CellRenderer
        """
        sec = model.get_object(sec_iter)
        cell.set_active(self.sections.get(sec, False))

    def toggled(self, renderer, path):
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
        marks an item as active/inactive and triggers
        the corresponding treeview actions
        """
        self.sections[sec] = active
        model = self.get_model()
        path = model.get_node_path(sec)
        if not path:
            return
        model.row_changed(path, model.get_iter(path))


class SectionPage(Page):
    def __init__(self, *args, **kargs):
        super(SectionPage, self).__init__(*args, **kargs)
        self.view = CheckableSectionView(None)
        self.pack_start(ScrolledWindow(self.view.tree_view), True, True, 0)
        self.term = None

    def prepare(self, assistant, prev_page):
        data = prev_page.data
        if "repository" in data.keys() and data["repository"].strip():
            self.term = terminology.terminologies.load(data["repository"])
            self.view.set_model(SectionModel(self.term))

    @property
    def sections(self):
        for sec in self.term.itersections(recursive=True):
            if self.view.sections.get(sec, False):
                yield sec


class SummaryPage(Page):
    type = gtk.ASSISTANT_PAGE_CONFIRM

    def __init__(self, *args, **kargs):
        super(SummaryPage, self).__init__(*args, **kargs)

        msg = "All information has been gathered. Ready to create document."
        self.add(gtk.Label(label=msg))


class DocumentWizard:
    def __init__(self):
        assistant = gtk.Assistant()

        assistant.set_title("New odML-Document wizard")
        assistant.set_default_size(800, 500)
        assistant.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        assistant.connect("apply", self.apply)
        assistant.connect("close", self.cancel)
        assistant.connect("cancel", self.cancel)

        data_page = DataPage()
        data_page.deploy(assistant, "Document information")
        self.data_page = data_page

        section_page = SectionPage()
        section_page.data = data_page
        section_page.deploy(assistant, "Repository section import")
        self.section_page = section_page

        SummaryPage().deploy(assistant, "Complete")

        assistant.connect("prepare", self.prepare)
        # third page loads the repository and offers which sections to import initially
        assistant.show_all()

    def prepare(self, assistant, page):
        last_page_idx = assistant.get_current_page()-1
        prev_page = None
        if last_page_idx >= 0:
            prev_page = assistant.get_nth_page(last_page_idx)
            prev_page.finalize()
        return page.prepare(self, prev_page)

    def cancel(self, assistant):
        self.cleanup()
        assistant.destroy()

    def cleanup(self):
        """
        Placeholder to reset the main window view in case there is no open tab.
        """
        raise NotImplementedError

    def apply(self, _):
        """
        the process is finished, create the desired document
        """
        doc = odml.Document()
        for key, val in self.data_page.data.items():
            setattr(doc, key, val)

        # copy all selected sections from the terminology
        if hasattr(self.section_page, "term") and self.section_page.term:
            term = self.section_page.term
            # set the associated section
            term._assoc_sec = doc
            for sec in term.itersections(recursive=True):
                if sec not in self.section_page.sections:
                    continue
                newsec = sec.clone(children=False)
                for prop in sec.properties:
                    cprop = prop.clone()

                    # All added properties need to be adjusted to odml-ui needs!
                    handle_property_import(cprop)

                    newsec.append(cprop)

                sec._assoc_sec = newsec
                if hasattr(sec.parent, "_assoc_sec"):
                    sec.parent._assoc_sec.append(newsec)

        self.finish(doc)

    def finish(self, document):
        """
        Placeholder that is overridden by an actual implementation
        """
        raise NotImplementedError
