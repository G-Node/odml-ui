import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import odml

from odml.property import BaseProperty
from odml.section import BaseSection

from .TreeIters import PropIter, ValueIter, SectionPropertyIter
from .TreeModel import TreeModel, ColumnMapper
from . import ValueModel


ColMapper = ColumnMapper({"Name":        (0, "name"),
                          "Value":       (1, "pseudo_values"),
                          "Type":        (2, "dtype"),
                          "Unit":        (3, "unit"),
                          "Uncertainty": (4, "uncertainty"),
                          "Definition":  (5, "definition"),
                          })


class PropertyModel(TreeModel):
    def __init__(self, section):
        super(PropertyModel, self).__init__(ColMapper)
        self._section = section
        self._section.add_change_handler(self.on_section_changed)
        self.offset = len(section.to_path())

    @staticmethod
    def model_path_to_odml_path(path):
        # (n, ...) -> (1, ...)
        # this can only go wrong sometimes because properties
        # with only one value share a common path
        return (1,) + tuple(path.get_indices())  # we consider properties only

    def odml_path_to_model_path(self, path):
        if len(path) == 3:  # 1, prop, val
            # if only one child, return property row
            if len(self._section.from_path(path[:2])) == 1:
                return path[1:2]
        return path[1:]

    def on_get_iter(self, path):
        if len(self._section._props) == 0:
            return None

        path = self.model_path_to_odml_path(path)  # we consider properties only
        node = self._section.from_path(path)
        return self._get_node_iter(node)

    def on_get_value(self, tree_iter, column):
        """
        add some coloring to the value in certain cases
        """
        v = super(PropertyModel, self).on_get_value(tree_iter, column)
        if v is None:
            return v

        obj = tree_iter._obj
        if isinstance(tree_iter, ValueIter):
            obj = obj._property

        return self.highlight(obj, v, column)

    def on_iter_n_children(self, tree_iter):
        if tree_iter is None:
            tree_iter = SectionPropertyIter(self._section)
        return super(PropertyModel, self).on_iter_n_children(tree_iter)

    def on_iter_nth_child(self, tree_iter, n):
        if tree_iter is None:
            prop = self._section._props[n]
            return PropIter(prop)
        return super(PropertyModel, self).on_iter_nth_child(tree_iter, n)

    def _get_node_iter(self, node):
        if isinstance(node, BaseProperty):
            return PropIter(node)
        if isinstance(node, ValueModel.Value):
            return ValueIter(node)
        return SectionPropertyIter(node)

    def post_delete(self, parent, old_path):
        super(PropertyModel, self).post_delete(parent, old_path)
        if isinstance(parent, BaseProperty):
            # a value was deleted
            if len(parent) == 1:
                # the last child row is also not present anymore,
                # the value is now displayed inline
                path = self.get_node_path(parent)
                self.row_deleted(path + (0,))  # first child
                self.row_has_child_toggled(path, self.get_iter(path))

    def post_insert(self, node):
        # this actually already works fine, since the subtree will always start
        # collapsed, however in fact we would need to insert an additional row
        # if the property switched from one value to two values
        # (the first was displayed inline, but now gets its own row)
        super(PropertyModel, self).post_insert(node)

    def on_section_changed(self, context):
        """
        this is called by the Eventable modified MixIns of Value/Property/Section
        and causes the GUI to refresh the corresponding cells
        """
        # we are only interested in changes going up to the section level,
        # but not those dealing with subsections of ours
        if context.cur is not self._section or \
                isinstance(context.val, BaseSection):
            return

        if context.action == "set" and context.post_change:
            path = self.get_node_path(context.obj)
            if not path:
                return  # probably the section changed
            try:
                curriter = self.get_iter(path)
                self.row_changed(path, curriter)
            except ValueError as e:
                # an invalid tree path, that should never have reached us
                print(repr(e))
                print(context.dump())

        # there was some reason we did this, however context.obj can
        # also be a property of the current section
        # if not context.obj is self._section:
        #    return

        if context.action == "remove":
            self.event_remove(context)

        if (context.action == "append" or
                context.action == "insert") and context.post_change:
            self.event_insert(context)

        if context.action == "reorder":
            self.event_reorder(context)

    def destroy(self):
        self._section.remove_change_handler(self.on_section_changed)

    def __repr__(self):
        return "<PropertyModel of %s>" % self.section

    @property
    def section(self):
        return self._section
