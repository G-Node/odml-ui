import os
import platform
import sys

import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk
import gobject

from distutils.version import LooseVersion as CheckVer

import odml
# Currently odml.terminology does not longer support CACHE_DIR
# but might again in the future.
# from odml.terminology import CACHE_DIR
import tempfile
import odmlui.treemodel.mixin

from odml.property import BaseProperty

from odmlui.info import AUTHOR, CONTACT, COPYRIGHT, HOMEPAGE, VERSION, ODMLTABLES_VERSION
from odmlui.treemodel import SectionModel, ValueModel

from .AttributeView import AttributeView
from .ChooserDialog import odMLChooserDialog
from .DocumentRegistry import DocumentRegistry
from .EditorTab import EditorTab
from .Helpers import uri_to_path, get_extension, get_parser_for_file_type, \
        get_parser_for_uri, get_conda_root, run_odmltables
from .InfoBar import EditorInfoBar
from .MessageDialog import ErrorDialog, DecisionDialog
from .NavigationBar import NavigationBar
from .PropertyView import PropertyView
from .ScrolledWindow import ScrolledWindow
from .SectionView import SectionView
from .Wizard import DocumentWizard

gtk.gdk.threads_init()

ui_info = \
    '''
<ui>
  <menubar name='MenuBar'>
    <menu name='FileMenu' action='FileMenu'>
      <menuitem action='NewFile'/>
      <menuitem action='FileOpen'/>
      <menuitem action='Import'/>
      <menuitem action='OpenRecent' />
      <menuitem name='Save' action='Save' />
      <menuitem action='SaveAs' />
      <separator/>
      <menuitem action='CloseTab'/>
      <menuitem action='Close'/>
      <menuitem action='Quit'/>
    </menu>
    <menu name='EditMenu' action='EditMenu'>
      <menuitem action='Undo'/>
      <menuitem action='Redo'/>
      <separator/>
      <menu name='AddMenu' action='AddMenu'>
          <menuitem action='NewSection'/>
          <menuitem action='NewProperty'/>
          <menuitem action='NewValue'/>
      </menu>
      <menuitem action='Delete'/>
      <separator/>
      <menuitem action='CloneTab'/>
      <menuitem action='Validate'/>
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='VisitHP'/>
      <separator/>
      <menuitem action='About'/>
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem name='New' action='NewFile' />
    <toolitem name='Open' action='OpenRecent' />
    <toolitem name='Save' action='Save' />
    <separator/>
    <toolitem name='Undo' action='Undo' />
    <toolitem name='Redo' action='Redo' />
    <separator/>
    <toolitem action='NewSection'/>
    <toolitem action='NewProperty'/>
    <toolitem action='NewValue'/>
    <toolitem action='Delete'/>
    <separator/>
    <toolitem action='Validate' />
    <separator/>
    <toolitem action='odMLTablesCompare' />
    <toolitem action='odMLTablesConvert' />
    <toolitem action='odMLTablesFilter' />
    <toolitem action='odMLTablesMerge' />
  </toolbar>
</ui>'''

# Handle loading from python virtual environments
env_root = ""
if hasattr(sys, 'prefix'):
    env_root = sys.prefix


# See CACHE_DIR comment in the import section.
CACHE_DIR = os.path.join(tempfile.gettempdir(), "odml.cache")

if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except OSError:  # might happen due to concurrency
        if not os.path.exists(CACHE_DIR):
            raise

# Quick and dirty to find out if Anaconda is being used and where it installed
# all the goodies we need. Not robust but good enough for now.
conda_env_root = get_conda_root()  # root of the currently active Anaconda environment


# Finding package root for license file and custom icons
package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def lookup_resource_paths(const_path):
    res = [const_path,
           os.path.join(package_root, const_path),
           os.path.join(env_root, const_path),
           os.path.join('usr', const_path),
           os.path.join('usr', 'local', const_path)]

    if env_root:
        res.append(os.path.join(env_root, const_path))

    if conda_env_root:
        res.append(os.path.join(conda_env_root, const_path))

    if os.getenv('HOME'):
        res.append(os.path.join(os.getenv('HOME'), '.local', const_path))

    if os.getenv('USERPROFILE'):
        res.append(os.path.join(os.getenv('USERPROFILE'), '.local', const_path))

    return res


# Loading text from license file
lic_name = "LICENSE"

lic_paths = lookup_resource_paths(os.path.join('share', 'odmlui', lic_name))

lic_paths.append(os.path.join(os.path.dirname(__file__), lic_name))
lic_paths.append(os.path.join(package_root, lic_name))

license = ""
for lic in lic_paths:
    if os.path.isfile(lic):
        with open(lic) as f:
            license = f.read()
            break


def gui_action(name, tooltip=None, stock_id=None, label=None, accelerator=None):
    """
    function decorator indicating and providing info for a gui Action
    """
    def func(f):
        f.name = name
        f.tooltip = tooltip
        f.stock_id = stock_id
        f.label = label
        f.accelerator = accelerator

        # For Mac, replace 'control' modifier with 'primary' modifier
        if f.accelerator is not None and platform.system() == 'Darwin':
            f.accelerator = f.accelerator.replace('control', 'primary')

        return f
    return func


class EditorWindow(gtk.Window):
    odMLHomepage = HOMEPAGE
    registry = DocumentRegistry()
    editors = set()
    welcome_disabled_actions = ["Save", "SaveAs", "NewSection", "NewProperty",
                                "NewValue", "Delete", "CloneTab", "Validate",
                                "odMLTablesCompare", "odMLTablesConvert",
                                "odMLTablesFilter", "odMLTablesMerge"]

    def __init__(self, parent=None):
        gtk.Window.__init__(self)
        self.editors.add(self)
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('delete-event', self.close)

        self.set_title("odML Editor")
        self.set_default_size(800, 600)

        # Check available screen size and adjust default app size to 1024x768 if possible.
        screen = self.get_screen()
        # Use first available monitor as default.
        currmon = 0
        actwin = screen.get_active_window()
        # Set current monitor only, when active window returns not None.
        if actwin:
            currmon = screen.get_monitor_at_window(actwin)

        mondims = screen.get_monitor_geometry(currmon)
        if mondims.width >= 1024 and mondims.height >= 768:
            self.set_default_size(1024, 768)

        icons = load_icon_pixbufs("odml-logo")
        self.set_icon_list(icons)

        merge = gtk.UIManager()
        merge.connect('connect-proxy', self.on_uimanager__connect_proxy)
        merge.connect('disconnect-proxy', self.on_uimanager__disconnect_proxy)

        # ### CHANGE :-
        # The 'set-data' method in PyGTK is no longer available.
        # Now, we have to set it just as a data member of the object.
        self.ui_manager = merge
        merge.insert_action_group(self.__create_action_group(), 0)
        self.add_accel_group(merge.get_accel_group())

        try:
            mergeid = merge.add_ui_from_string(ui_info)
        except gobject.GError as msg:
            print("building menus failed: %s" % msg)
        bar = merge.get_widget("/MenuBar")
        bar.show()

        table = gtk.Table(n_rows=2, n_columns=6, homogeneous=False)
        self.add(table)

        table.attach(bar,
                     # X direction #          # Y direction
                     0, 2,                      0, 1,
                     gtk.EXPAND | gtk.FILL,     0,
                     0,                         0)

        bar = merge.get_widget("/ToolBar")
        # bar.set_tooltips(True) -->  Not needed
        bar.show()
        table.attach(bar,
                     # X direction #       # Y direction
                     0, 2,                   1, 2,
                     gtk.EXPAND | gtk.FILL,  0,
                     0,                      0)

        tool_button = merge.get_widget("/ToolBar/Open")
        tool_button.connect("clicked", self.open_file)
        tool_button.set_arrow_tooltip_text("Open a recently used file")
        tool_button.set_label("Open")
        tool_button.set_tooltip_text("Open Files")

        navigation_bar = NavigationBar()
        navigation_bar.on_selection_change = self.on_navigate
        self._navigation_bar = navigation_bar

        # schematic organization
        #  -vpaned---------------------------
        # | -hpaned-----+-------------------
        # ||            | -property_view(vbox)
        # || scrolled:  | | info_bar
        # ||  section_tv| +----------------
        # ||            | | scrolled: property_tv
        # ||            | \----------------
        # |\------------+-------------------
        # +----------------------------------
        # |  --frame: navigation bar -------
        # | +-------------------------------
        # | | scrolled: _property_view
        # | \-------------------------------
        # \----------------------------------
        hpaned = gtk.HPaned()
        hpaned.show()
        hpaned.set_position(150)

        section_tv = SectionView(self.registry)
        section_tv.execute = self.execute
        section_tv.on_section_change = self.on_section_change
        section_view = gtk.VBox(homogeneous=False, spacing=0)
        tmp = gtk.Frame.new("Sections")
        tmp.add(ScrolledWindow(section_tv._treeview))
        tmp.show()
        section_view.pack_start(tmp, True, True, 1)
        section_view.show()
        hpaned.add1(section_view)

        property_tv = PropertyView(self.registry)
        property_tv.execute = self.execute
        property_tv.on_property_select = self.on_object_select
        property_view = gtk.VBox(homogeneous=False, spacing=0)

        info_bar = EditorInfoBar()
        self._info_bar = info_bar
        property_view.pack_start(info_bar, False, False, 1)
        tmp = gtk.Frame.new("Properties")
        tmp.add(ScrolledWindow(property_tv._treeview))
        tmp.show()
        property_view.pack_start(tmp, True, True, 1)
        property_view.show()
        hpaned.add2(property_view)

        self._property_tv = property_tv
        self._section_tv = section_tv

        # property_view to edit ODML-Properties
        # to edit properties of Document, Section or Property:
        self._property_view = AttributeView(self.execute)
        frame = gtk.Frame()
        frame.set_label_widget(navigation_bar)
        frame.add(ScrolledWindow(self._property_view._treeview))
        frame.show()

        vpaned = gtk.VPaned()
        vpaned.show()
        # Adjust Attribute view position to default window size
        vpaned.set_position(self.get_default_size().height - 300)
        vpaned.pack1(hpaned, resize=True, shrink=False)
        vpaned.pack2(frame, resize=False, shrink=True)

        # Check if odML-tables is available
        self.odml_tables_available = False
        try:
            from odmltables import gui
            from odmltables import VERSION as OT_VERSION
            if CheckVer(OT_VERSION) >= ODMLTABLES_VERSION:
                self.odml_tables_available = True
        except (ImportError, AttributeError) as e:
            print("[Info] odMLTables not available: %s" % e)

        class Tab(gtk.HBox):
            """
            a tab container
            """
            child = vpaned

        self.Tab = Tab

        notebook = gtk.Notebook()  # we want tabs
        notebook.connect("switch-page", self.on_tab_select)
        notebook.connect("create-window", self.on_new_tab_window)
        notebook.show()
        self.notebook = notebook

        table.attach(notebook,
                     # X direction           Y direction
                     0, 2,                   3, 4,
                     gtk.EXPAND | gtk.FILL,  gtk.EXPAND | gtk.FILL,
                     0,                      0)

        statusbar = gtk.Statusbar()
        table.attach(statusbar,
                     # X direction           Y direction
                     0, 2,                   5, 6,
                     gtk.EXPAND | gtk.FILL,  0,
                     0,                      0)
        self._statusbar = statusbar
        statusbar.show()

        self.show_all()

    def mktab(self, tab):
        t = self.Tab()
        t.tab = tab
        t.show()
        return t

    def on_menu_item__select(self, menuitem, tooltip):
        context_id = self._statusbar.get_context_id('menu_tooltip')
        self._statusbar.push(context_id, tooltip)

    def on_menu_item__deselect(self, menuitem):
        context_id = self._statusbar.get_context_id('menu_tooltip')
        self._statusbar.pop(context_id)

    def on_uimanager__connect_proxy(self, uimgr, action, widget):
        # TODO this does not work on unity at least
        tooltip = action.get_property('tooltip')
        if isinstance(widget, gtk.MenuItem) and tooltip:
            cid = widget.connect(
             'select', self.on_menu_item__select, tooltip)
            cid2 = widget.connect(
             'deselect', self.on_menu_item__deselect)
            widget.connect_ids = (cid, cid2)

    def on_uimanager__disconnect_proxy(self, uimgr, action, widget):
        try:
            cids = widget.connect_ids or ()
            for cid in cids:
                widget.disconnect(cid)
        except AttributeError:
            pass

    def __create_action_group(self):
        # entry: name, stock id, label
        entries = [
              ("FileMenu", None, "_File"),
              ("EditMenu", None, "_Edit"),
              ("AddMenu",  gtk.STOCK_ADD),
              ("HelpMenu", gtk.STOCK_HELP),
              ]
        for (k, v) in self.__class__.__dict__.items():
            if hasattr(v, "stock_id"):
                entries.append(
                    (v.name, v.stock_id, v.label, v.accelerator,
                     v.tooltip, getattr(self, k)))

        recent_action = gtk.RecentAction(name="OpenRecent",
                                         label="Open Recent",
                                         tooltip="Open Recent Files",
                                         stock_id=gtk.STOCK_OPEN)
        recent_action.connect("item-activated", self.open_recent)

        recent_filter = gtk.RecentFilter()
        odMLChooserDialog._setup_file_filter(recent_filter)

        recent_action.set_sort_type(gtk.RECENT_SORT_MRU)
        recent_action.add_filter(recent_filter)
        recent_action.set_show_not_found(False)

        action_group = gtk.ActionGroup(name="EditorActions")
        self.editor_actions = action_group
        action_group.add_actions(entries)
        action_group.add_action(recent_action)
        return action_group

    def welcome(self, action=None):
        """
        display a welcome window
        """
        page = gtk.Label()
        # welcome text
        text = """<span size="x-large" weight="bold">Welcome to odML-Editor</span>\n\n
                   Now go ahead and <a href="#new">create a new document</a>."""
        for action in self.welcome_disabled_actions:
            self.enable_action(action, False)

        # display recently used files
        recent_filter = gtk.RecentFilter()
        odMLChooserDialog._setup_file_filter(recent_filter)

        # Now, we need to pass in a separate struct 'gtk.RecentFilterInfo',
        # for each recently used file, for the filtering process by the
        # recent_filter.filter() method. If the 'filter' return True,
        # the file is included, else not included.
        recent_odml_files = []
        MAX_RECENT_ITEMS = 12

        all_recent_files = gtk.RecentManager.get_default().get_items()
        filter_info = gtk.RecentFilterInfo()
        filter_info.contains = recent_filter.get_needed()

        for i in all_recent_files:
            if not i.exists():
                continue
            filter_info.display_name = i.get_display_name()
            filter_info.uri = i.get_uri()
            filter_info.mime_type = i.get_mime_type()
            if recent_filter.filter(filter_info):
                recent_odml_files.append(i)

        recent_odml_files.sort(key=lambda x: x.get_age())
        recent_odml_files = recent_odml_files[:MAX_RECENT_ITEMS]

        if recent_odml_files:
            text += "\n\nOr open a <b>recently used file</b>:\n"
            text += "\n".join([u"\u2022 <a href='%s'>%s</a>" %
                               (i.get_uri(), i.get_display_name())
                               for i in recent_odml_files])

        page.set_markup(text)
        page.connect("activate-link", self.welcome_action)
        page.show()
        self.notebook.set_show_tabs(False)
        self.notebook.append_page(page)

    def welcome_action(self, widget, path):
        """
        create a new document or open a recently used file
        as indicated by the *path* argument.

        the method is invoked by clicking on a link in the welcome tab
        """
        # remove the page and enable the gui actions again
        self.notebook.remove_page(0)
        for action in self.welcome_disabled_actions:
            self.enable_action(action, True)

        if path == "#new":
            self.new_file()
        elif path is not None:
            self.load_document(path)

        return True

    @gui_action("About", tooltip="About odML editor", stock_id=gtk.STOCK_ABOUT)
    def about(self, action):
        logo = self.render_icon("odml-logo", gtk.ICON_SIZE_DIALOG)

        dialog = gtk.AboutDialog()
        dialog.set_name("odMLEditor")
        dialog.set_copyright(COPYRIGHT)
        dialog.set_authors(AUTHOR.split(", "))
        dialog.set_website(self.odMLHomepage)
        dialog.set_license(license)
        dialog.set_logo(logo)
        dialog.set_version(VERSION)
        dialog.set_comments("Contact <%s>" % CONTACT)

        dialog.set_transient_for(self)

        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()

    @gui_action("NewFile", tooltip="Create a new document", stock_id=gtk.STOCK_NEW)
    def new_file(self, action=None, wizard=True, doc=None):
        """
        open a new tab with an empty document

        if *wizard* is True, run the wizard first
        """
        if wizard:
            wiz = DocumentWizard()
            wiz.finish = lambda doc: self.new_file(wizard=False, doc=doc)
            return

        tab = EditorTab(self)
        tab.new(doc)
        self.append_tab(tab)
        return tab

    @gui_action("FileOpen", tooltip="Open an odML File", stock_id=gtk.STOCK_OPEN)
    def open_file(self, action):
        """called to show the open file dialog"""
        self.chooser_dialog(title="Open Document", callback=self.load_document)

    def load_document(self, uri, file_type=None):
        """open a new tab, load the document into it"""
        tab = EditorTab(self)
        if not tab.load(uri):  # Close tab upon parsing errors
            tab.close()
            return

        self.append_tab(tab)
        return tab

    @gui_action("Import", tooltip="Import previous odML version", label="Import odML")
    def import_file(self, action):
        """Open a file chooser dialog to import a previous odML version file."""
        self.chooser_dialog(title="Import previous odML version",
                            callback=self.convert_version)

    def convert_version(self, uri, file_type=None):
        """
        Open a new tab, and load a previous version odML file into it.
        """
        tab = EditorTab(self)
        if not tab.convert(uri):  # Close tab upon parsing errors
            tab.close()
            return

        self.append_tab(tab)
        return tab

    @gui_action("CloneTab", tooltip="Create a copy of the current tab", label="_Clone",
                stock_id=gtk.STOCK_COPY, accelerator="<control><shift>C")
    def on_clone_tab(self, action):
        self.clone_tab(self.current_tab)

    def clone_tab(self, tab):
        ntab = tab.clone()
        self.append_tab(ntab)
        return ntab

    @gui_action("Validate", tooltip="Validate the document and check for errors",
                label="_Validate", stock_id=gtk.STOCK_APPLY, accelerator="<control>E")
    def on_validate(self, action):
        self.current_tab.validate()

    def handle_odmltables(self, wizard):
        if not self.current_tab.file_uri or self.current_tab.is_modified:
            self._info_bar.show_info("Please validate and save "
                                     "your document before starting odMLTables.")
        elif self.odml_tables_available:
            run_odmltables(self.current_tab.file_uri, CACHE_DIR,
                            self.current_tab.document, wizard)
        else:
            self._info_bar.show_info("You need odMLTables (v%s or newer) "
                                     "installed to run this feature." %
                                     ODMLTABLES_VERSION)

    @gui_action("odMLTablesCompare", tooltip="Compare entities of an odML document",
                label="odMLTablesCompare", stock_id="INM6-compare-table",
                accelerator="<control>E")
    def on_compare_entities(self, action):
        self.handle_odmltables("compare")

    @gui_action("odMLTablesConvert", tooltip="Convert document to xls or csv",
                label="odMLTablesConverter", stock_id="INM6-convert-odml",
                accelerator="<control>C")
    def on_convert(self, action):
        self.handle_odmltables("convert")

    @gui_action("odMLTablesFilter", tooltip="Filter document contents",
                label="odMLTablesFilter", stock_id="INM6-filter-odml",
                accelerator="<control>F")
    def on_filter(self, action):
        self.handle_odmltables("filter")

    @gui_action("odMLTablesMerge", tooltip="Merge odML documents",
                label="odMLTablesMerge", stock_id="INM6-merge-odml",
                accelerator="<control>M")
    def on_merge(self, action):
        self.handle_odmltables("merge")

    def select_tab(self, tab, force_reset=False):
        """
        activate a new tab, reset the statusbar and models accordingly
        """
        ctab = self.current_tab
        if not force_reset and ctab is tab:
            return

        # Disabling Tab state save-and-restore methods, as first, we need to
        # handle the TreePath conversions properly

        if ctab is not None:
            ctab.state = self.get_tab_state()

        if not force_reset:
            self.current_tab = tab

        self.set_status_filename(tab)
        self.update_model(tab)
        self.enable_undo(tab.command_manager.can_undo)
        self.enable_redo(tab.command_manager.can_redo)

        if hasattr(tab, "state"):
            self.set_tab_state(tab.state)

        # Ensure PropertyView update for tab switch and added tabs
        if len(tab.document.sections) > 0:
            selection = self._section_tv._treeview.get_selection()
            _, tree_iter = selection.get_selected()
            # Select first section only when opening document
            if tree_iter is None:
                selection.select_path((0,))
        else:
            # Reset property treeview model in case of empty document
            self._property_tv.model = None

    @property
    def current_tab(self):
        """
        returns the current odml tab
        """
        page = self.notebook.get_current_page()
        child = self.notebook.get_nth_page(page)
        if child is not None and not isinstance(child, gtk.Label):
            return child.tab

    @current_tab.setter
    def current_tab(self, tab):
        if self.current_tab is tab:
            return
        self.notebook.set_current_page(self.get_notebook_page(tab))

    def get_tab_state(self):
        state = self._section_tv.save_state(), self._property_tv.save_state()
        return state

    def set_tab_state(self, state):
        self._section_tv.restore_state(state[0])
        self._property_tv.restore_state(state[1])

    def get_notebook_page(self, tab):
        """
        returns the index holding *tab*
        """
        for i, child in enumerate(self.notebook):
            if child.tab is tab:
                return i

    @property
    def tabs(self):
        """iterate over the tabs in the notebook"""
        for child in self.notebook:
            yield child.tab

    def mk_tab_label(self, tab):
        # hbox will be used to store a label and button, as notebook tab title
        hbox = gtk.HBox(homogeneous=False, spacing=0)
        label = gtk.Label(label=tab.get_name())
        tab.label = label
        hbox.pack_start(label)

        # get a stock close button image
        close_image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)

        # make the close button
        btn = gtk.Button()
        btn.set_relief(gtk.RELIEF_NONE)
        btn.set_focus_on_click(False)
        btn.connect('clicked', self.on_tab_close_click, tab)
        btn.add(close_image)
        hbox.pack_start(btn, False, False)

        hbox.show_all()
        return hbox

    def append_tab(self, tab):
        """
        append the tab to our tab list

        may replace the current tab, if its a new file that
        has not been edited
        """
        child = self.mktab(tab)
        # some action caused creation of a new tab
        # make sure, that we close the welcome screen if still present
        if isinstance(self.notebook.get_nth_page(0), gtk.Label):
            self.welcome_action(widget=None, path=None)

        self.notebook.append_page(child, self.mk_tab_label(tab))
        self.notebook.set_tab_reorderable(child, True)
        self.notebook.set_tab_detachable(child, True)
        self.notebook.set_show_tabs(self.notebook.get_n_pages() > 1)

        # Switch to new tab
        self.on_tab_select(self.notebook, None, self.get_notebook_page(tab), False)

    def close_tab(self, tab, save=True, create_new=True, close=True):
        """
        try to save and then remove the tab from our tab list
        and remove the tab from the Notebook widget

        if *save* is true, the tab will only be closed upon successful save

        if *create_new* is true, a new empty document will be created
        after the last tab was closed

        if *close* is True, call close() on the tab. We don't want to do
        that, if we move the tab somewhere else, but close it here.
        """
        if tab is None or (save and not tab.save_if_changed()):
            return False

        idx = self.get_notebook_page(tab)

        if create_new and self.notebook.get_n_pages() == 1:
            self.welcome()
            # open a new tab already, so we never get empty.
            # also: remove the vpaned (hbox.child) from the widget, so that
            # it does not receive any destroy signals and can be reused.
            hbox = self.notebook.get_nth_page(idx)
            hbox.remove(hbox.child)

        self.notebook.remove_page(idx)
        if close:
            tab.close()
        self.notebook.set_show_tabs(self.notebook.get_n_pages() > 1)
        return True

    def on_tab_select(self, notebook, page, pagenum, force_reset=True):
        """
        the notebook widget selected a tab
        """
        hbox = notebook.get_nth_page(pagenum)
        if isinstance(hbox, gtk.Label):
            return  # quick exit for the Welcome screen
        if hbox.child.get_parent() is None:
            hbox.child.show()
            hbox.add(hbox.child)
        else:
            prev_parent = hbox.child.get_parent()
            prev_parent.remove(hbox.child)
            hbox.add(hbox.child)
        self.select_tab(hbox.tab, force_reset=force_reset)

    def on_tab_close_click(self, button, tab):
        self.close_tab(tab)

    def on_new_tab_window(self, notebook, page, x, y):
        """
        the tab so dropped to another window
        """
        editor = EditorWindow()
        tab = page.tab
        state = self.get_tab_state()
        tab.window = editor
        editor.append_tab(tab)
        editor.set_tab_state(state)
        self.close_tab(tab, save=False, close=False)
        return True

    def chooser_dialog(self, title, callback, save=False):
        chooser = odMLChooserDialog(title=title, save=save)
        chooser.set_transient_for(self)
        chooser.on_accept = callback
        chooser.show()

    def open_recent(self, recent_action):
        uri = recent_action.get_current_uri()
        self.load_document(uri)

    def set_status_filename(self, tab=None):
        if tab is None:
            tab = self.current_tab
        filename = tab.file_uri
        if not filename:
            filename = "<new file>"
        self.update_statusbar(filename)

    def update_model(self, tab):
        """updates the models if a different tab is selected changed"""
        model = None
        if tab.document is not None:
            model = SectionModel.SectionModel(tab.document)

        self._section_tv.set_model(model)
        self._navigation_bar.document = tab.document

    @gui_action("SaveAs", tooltip="Save changes to another file", stock_id=gtk.STOCK_SAVE_AS)
    def save_as(self, action):
        """
        called upon save_file action

        always runs a file_chooser dialog to allow saving to a different filename
        """
        self.chooser_dialog(title="Save Document",
                            callback=self.on_file_save, save=True)
        return False
        # TODO this signals that file saving was not successful
        # because no action should be taken until the chooser
        # dialog is finish, however the user might then need to
        # repeat the action, once the document was saved and the
        # edited flag was cleared.

    @gui_action("Save", tooltip="Save changes", stock_id=gtk.STOCK_SAVE)
    def save(self, action):
        """
        called upon save_file action

        runs a file_chooser dialog if the file_uri is not set
        """
        if self.current_tab.file_uri:
            return self.current_tab.save(self.current_tab.file_uri)
        return self.save_as(action)

    def on_file_save(self, uri, file_type=None):
        """
        Called on any "Save as" action after a file has been
        defined via the FileChooser Dialog.

        Checks whether the selected File already exists
        and provides a confirmation dialog to overwrite
        said file.
        """
        parser = None
        if file_type:
            parser = get_parser_for_file_type(file_type)
        if not parser:
            parser = get_parser_for_uri(uri)

        check_existing_file = uri_to_path(uri)
        ext = get_extension(check_existing_file)
        if ext != parser:
            check_existing_file += ".%s" % parser.lower()

        if os.path.isfile(check_existing_file):
            dialog = DecisionDialog(None, "File exists",
                                    "The file you selected already exists. "
                                    "Do you want to replace it?", "")
            response = dialog.run()
            if (response == gtk.ResponseType.CANCEL or
                    response == gtk.ResponseType.DELETE_EVENT):

                dialog.destroy()
                self.save_as(self.editor_actions.get_action("SaveAs"))
                return

            dialog.destroy()  # Cleaner handling of duplicate .destroy()?

        self.current_tab.file_uri = uri
        self.current_tab.update_label()
        self.current_tab.save(uri, file_type)
        self.set_status_filename()

    def save_if_changed(self):
        """
        if any open document was modified, ask the user
        if he or she wants to save the document.

        returns false if the user cancelled the action
        """
        for child in self.notebook:
            if not isinstance(child, gtk.Label) and not child.tab.save_if_changed():
                return False
        return True

    @gui_action("CloseTab", tooltip="Close the current tab", stock_id=gtk.STOCK_CLOSE,
                label="_Close Tab", accelerator="<control>W")
    def on_close_tab(self, action):
        self.close_tab(self.current_tab)

    @gui_action("Close", tooltip="Close the current window", stock_id=gtk.STOCK_CLOSE,
                label="Close _Window", accelerator="<control><shift>W")
    def close(self, action, extra=None):
        if self.save_if_changed():
            self.destroy()
        return True

    def destroy(self):
        """
        destroy the window and quit the app if no further odml windows
        are left
        """
        super(EditorWindow, self).destroy()
        if self in self.editors:
            self.editors.remove(self)
        if len(self.editors) == 0:
            gtk.main_quit()

    @gui_action("Quit", tooltip="Quit", stock_id=gtk.STOCK_QUIT)
    def quit(self, action, extra=None):
        for win in self.editors:
            if not win.save_if_changed():
                return True  # the event is handled and won't be passed to the window.
        gtk.main_quit()

    @gui_action("NewSection", label="Add Section",
                tooltip="Add a section to the current selected one",
                stock_id="odml_addSection")
    def new_section(self, action):
        obj = self._section_tv.get_selected_object()
        if obj is None:
            obj = self.current_tab.document
        self._section_tv.add_section(None, (obj, None))

    @gui_action("NewProperty", label="Add Property",
                tooltip="Add a property to the current section",
                stock_id="odml_addProperty")
    def new_property(self, action):
        obj = self._property_tv.section
        self._property_tv.add_property(None, (obj, None))

    @gui_action("NewValue", label="Add Value",
                tooltip="Add a value to the current selected property",
                stock_id="odml_addValue")
    def new_value(self, action):
        obj = self._property_tv.get_selected_object()
        if obj is None:
            return
        if isinstance(obj, ValueModel.Value):
            obj = obj.parent
        self._property_tv.add_value(None, (obj, None))

    @gui_action("Delete", tooltip="Remove the currently selected object from the document",
                stock_id="odml_Dustbin", accelerator="<shift>Delete", label="Delete")
    def delete_object(self, action):
        widget = self.get_focus()
        for w in [self._section_tv, self._property_tv]:
            if widget is w._treeview:
                widget = w
                break
        else:
            return False

        obj = widget.get_selected_object()
        if obj is None:
            return False
        widget.on_delete(None, obj)
        return True

    # TODO should we save a navigation history here?
    def on_section_change(self, section):
        self._property_tv.section = section
        self.on_object_select(section)

    def on_object_select(self, obj):
        """an object has been selected, now fix the current property_view"""
        for name, tv in (
                ("NewProperty", self._section_tv), ("NewValue", self._property_tv)):
            self.enable_action(name,
                               tv._treeview.get_selection().count_selected_rows() > 0)
        self.set_navigation_object(obj)

    def set_navigation_object(self, obj):
        """
        set a new item for the navigation bar
        """
        self._navigation_bar.set_model(obj)

    def on_navigate(self, obj):
        """
        update the property_view to work on object *obj*
        """
        self._property_view.set_model(obj)

    def navigate_to_document(self, doc):
        if self.current_tab.document is doc:
            return
        for tab in self.tabs:
            if tab.document is doc:
                return self.select_tab(tab)

    def navigate(self, obj):
        """navigate to a certain object"""
        # 1. select the right tab
        self.navigate_to_document(obj.document)

        # 2. select the corresponding section
        sec = obj
        prop = None
        if isinstance(obj, BaseProperty):
            sec = obj.parent
            prop = obj
        self._section_tv.select_object(sec)
        # 3. select the property
        if prop is not None:
            self._property_tv.select_object(prop)

    def update_statusbar(self, message, clear_previous=True):
        if clear_previous:
            self._statusbar.pop(0)
        self._statusbar.push(0, message)

    def visit_uri(self, uri, timestamp=None):
        if not timestamp:
            timestamp = gtk.get_current_event_time()
        gtk.show_uri(self.get_screen(), uri, timestamp)

    @gui_action("VisitHP", tooltip="Go to the odML Homepage", label="Visit Homepage")
    def on_visit_homepage(self, action):
        timestamp = None
        self.visit_uri(self.odMLHomepage, timestamp)

    def enable_action(self, action_name, enable):
        self.editor_actions.get_action(action_name).set_sensitive(enable)

    def enable_undo(self, enable=True):
        self.enable_action("Undo", enable)

    def enable_redo(self, enable=True):
        self.enable_action("Redo", enable)

    @gui_action("Undo", tooltip="Undo last editing action", stock_id=gtk.STOCK_UNDO,
                label="_Undo", accelerator="<control>Z")
    def undo(self, action):
        self.current_tab.command_manager.undo()

    @gui_action("Redo", tooltip="Redo an undone editing action", stock_id=gtk.STOCK_REDO,
                label="_Redo", accelerator="<control>Y")
    def redo(self, action):
        self.current_tab.command_manager.redo()

    def command_error(self, cmd, error):
        self._info_bar.show_info("Editing failed: %s" % error)

    def execute(self, cmd):
        return self.current_tab.command_manager.execute(cmd)


# Dependent on python environment and installation used, default gtk
# and custom icons will be found at different locations.
def get_img_path(icon_name):
    share_pixmaps = os.path.join('share', 'pixmaps')

    paths = lookup_resource_paths(share_pixmaps)
    paths.append(os.path.join(package_root, 'images'))

    found = None
    for check_path in paths:
        for dp, dn, fn in os.walk(check_path):
            for fname in [f for f in fn if f == icon_name]:
                found = dp
                break
        if found:
            break

    return found


def register_stock_icons():
    # conda environments might not have access to the system stock items.
    # Therefore update the IconTheme search path.
    if conda_env_root:
        print("[Info] Updating IconTheme search path")
        icon_theme = gtk.icon_theme_get_default()
        icon_theme.prepend_search_path(os.path.join(conda_env_root, "share", "icons"))

    ctrlshift = gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK
    icons = [('odml-logo', '_odML', 0, 0, ''),
             ('odml_addSection', 'Add _Section', ctrlshift, ord("S"), ''),
             ('odml_addProperty', 'Add _Property', ctrlshift, ord("P"), ''),
             ('odml_addValue', 'Add _Value', ctrlshift, ord("V"), ''),
             ('odml_Dustbin', '_Delete', 0, 0, ''),
             ('INM6-compare-table', 'Compare_entities', ctrlshift, ord("E"), ''),
             ('INM6-convert-odml', 'Convert_document', ctrlshift, ord("C"), ''),
             ('INM6-filter-odml', 'Filter_document', ctrlshift, ord("F"), ''),
             ('INM6-merge-odml', 'Merge_documents', ctrlshift, ord("M"), '')
             ]

    # This method is failing (silently) in registering the stock icons.
    # Passing a list of Gtk.StockItem also has no effects.
    # To circumvent this, the *stock* and *label* properties of items
    # have been separated, wherever necessary.
    gtk.stock_add(icons)

    # The icons are being registered by the following steps.
    # Add our custom icon factory to the list of defaults
    factory = gtk.IconFactory()
    factory.add_default()

    for stock_icon in icons:
        icon_name = stock_icon[0]

        try:
            # Dependent on python environment and installation used, default gtk
            # and custom icons will be found at different locations.
            name = "%s.%s" % (icon_name, "png")

            img_dir = get_img_path(name)
            if not img_dir:
                print("[Warning] Icon %s not found in supported paths" % name)
                continue

            img_path = os.path.join(img_dir, name)
            icon = load_pixbuf(img_path)
            icon_set = gtk.IconSet.new_from_pixbuf(icon)

            for icon in load_icon_pixbufs(icon_name):
                src = gtk.IconSource()
                src.set_pixbuf(icon)
                icon_set.add_source(src)

            factory.add(icon_name, icon_set)

        except gobject.GError as error:
            print('[Warning] Failed to load icon', icon_name, error)



def load_pixbuf(path):
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        transparent = pixbuf.add_alpha(False, 255, 255, 255)
        return transparent
    except Exception as exc:
        print("[Warning] Pixbuf loading exception: %s" % exc)
        return None


def load_icon_pixbufs(prefix):
    icons = []

    # Dirty fix for loading the odml-logo.
    get_icon = prefix
    if prefix == 'odml-logo':
        get_icon = "%s.png" % prefix

    img_dir = get_img_path(get_icon)
    if img_dir:
        files = os.listdir(img_dir)
        for f in files:
            if f.startswith(prefix):
                abs_path = os.path.join(img_dir, f)
                icon = load_pixbuf(abs_path)
                if icon:
                    icons.append(icon)
    return icons
