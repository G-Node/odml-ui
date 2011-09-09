import gtk, gobject
from TreeIters import PropIter, ValueIter
from TreeModel import TreeModel, ColumnMapper
import sys
from ... import value, property as odmlproperty
debug = lambda x: sys.stderr.write(x+"\n")
debug = lambda x: 0


ColMapper = ColumnMapper({"Name"        : (0, "name"),
                         "Value"       : (1, "value"),
                         "Definition"  : (2, "definition"),
                         "Type"        : (3, "dtype"),
                         "Unit"        : (4, "unit"),
                         "Comment"     : (5, "comment"),
                         "Id"          : (6, "id")})

class SectionModel(TreeModel):
    def __init__(self, section):
        super(SectionModel, self).__init__(ColMapper)
        self._section = section
        self._section._Changed += self.on_section_changed
        self.offset = len(section.to_path())

    @staticmethod
    def model_path_to_odml_path(path):
        # (n, ...) -> (1, ...)
        return (1,) + path # we consider properties only

    @staticmethod
    def odml_path_to_model_path(path):
        return path[1:]

    def on_get_iter(self, path):
        debug(":on_get_iter [%s] " % repr(path))

        if len(self._section._props) == 0: return None

        path = self.model_path_to_odml_path(path) # we consider properties only
        node = self._section.from_path(path)
        return self._get_node_iter(node)

    def on_iter_nth_child(self, tree_iter, n):
        debug(":on_iter_nth_child [%d]: %s " % (n, tree_iter))
        if tree_iter == None:
            prop = self._section._props[n]
            return PropIter(prop)
        return super(SectionModel, self).on_iter_nth_child(tree_iter, n)

    def _get_node_iter(self, node):
        if isinstance(node, value.Value):
            return ValueIter(node)
        return PropIter(node)

    def on_section_changed(self, context):
        """
        this is called by the Eventable modified MixIns of Value/Property/Section
        and causes the GUI to refresh the corresponding cells
        """
        print "change event: ", context

        # we are only interested in changes going up to the section level,
        # but not those dealing with subsections of ours
        if not context.cur is self._section or \
                isinstance(context.val, self._section.__class__):
            return

        if context.action == "set" and context.postChange:
            path = self.get_node_path(context.obj)
            if not path: return # probably the section changed
            iter = self.get_iter(path)
            self.row_changed(path, iter)

        if not context.obj is self._section:
            return

        if context.action == "remove":
            self.event_remove(context)

        if (context.action == "append" or context.action == "insert") and context.postChange:
            print "row inserted", context.val
            self.post_insert(context.val)



    def destroy(self):
        self._section._Changed -= self.on_section_changed

    @property
    def section(self):
        return self._section
