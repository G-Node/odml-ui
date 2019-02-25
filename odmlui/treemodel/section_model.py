import pygtkcompat

from odml.base import Sectionable
from odml.doc import BaseDocument

import odmlui

import gtk

from .tree_iters import SectionIter
from .tree_model import TreeModel, ColumnMapper

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

DEBUG = lambda x: 0
# to enable tree debugging:
# import sys
# DEBUG = lambda x: sys.stdout.write(x + "\n")

COL_MAPPER = ColumnMapper({"Name": (0, "name")})


class SectionModel(TreeModel):
    def __init__(self, odml_document):
        super(SectionModel, self).__init__(COL_MAPPER)

        # otherwise bad things happen
        assert isinstance(odml_document, BaseDocument)

        self._section = odml_document
        self._section.add_change_handler(self.on_section_changed)

    @property
    def document(self):
        return self._section

    def model_path_to_odml_path(self, path):
        # (a,b,c) -> (a,0,b,0,c)
        # document -> section
        rpath = (path[0],)
        for i in path[1:]:
            # section -> sub-section
            rpath += (0, i)
        return rpath

    def odml_path_to_model_path(self, path):
        # (a,0,b,0,c) -> (a,b,c)
        if not path:
            # this cannot be converted to a path, but it's fine
            return ()
        return (path[0],) + path[2::2]

    def on_get_iter(self, path):
        DEBUG("+on_get_iter: %s" % repr(path))
        if path == gtk.TreePath.new_first() and len(self._section.sections) == 0:
            return None

        # we get the path from the treemodel which does not show the properties
        # therefore adjust the path to always select the sections
        # document -> section
        rpath = (path[0],)
        for i in path[1:]:
            # section -> sub-section
            rpath += (0, i)
        section = self._section.from_path(rpath)
        DEBUG("-on_get_iter: %s" % section)
        return SectionIter(section)

    def on_get_value(self, tree_iter, column):
        """
        add some coloring to the value in certain cases
        """
        val = super(SectionModel, self).on_get_value(tree_iter, column)
        if val is None:
            return val

        obj = tree_iter._obj
        return self.highlight(obj, val, column)

    def on_iter_n_children(self, tree_iter):
        if tree_iter is None:
            tree_iter = SectionIter(self._section)
        return super(SectionModel, self).on_iter_n_children(tree_iter)

    def on_iter_nth_child(self, tree_iter, n):
        if tree_iter == None:
            return SectionIter(self._section.sections[n])
        return super(SectionModel, self).on_iter_nth_child(tree_iter, n)

    def _get_node_iter(self, node):
        # no safety checks here, always return a section iter even for the root node
        # (this is required to make n_children work when reordering)
        return SectionIter(node)

    def destroy(self):
        self._section.remove_change_handler(self.on_section_changed)

    def on_section_changed(self, context):
        """
        this is called by the Eventable modified MixIns of Value/Property/Section
        and causes the GUI to refresh the corresponding cells
        """
        if odmlui.DEBUG:
            print("change event(section): ", context)

        # we are only interested in changes on sections
        if not isinstance(context.obj, Sectionable):
            return

        if not context.cur.document is self.document:
            return

        if context.action == "set" and context.post_change:
            name, value = context.val
            if name == "name":
                path = self.get_node_path(context.obj)
                self.row_changed(path, self.get_iter(path))

        if context.action == "reorder":
            self.event_reorder(context)

        obj = context.val
        if not isinstance(obj, Sectionable):
            return

        if context.action == "remove":
            self.event_remove(context)

        if (context.action == "append" or context.action == "insert") and \
                context.post_change:
            self.event_insert(context)
