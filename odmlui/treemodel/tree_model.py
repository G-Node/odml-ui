import sys

import pygtkcompat
import gtk
import gobject

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

DEBUG = lambda x: 0


class ColumnMapper(object):
    def __init__(self, mapping_dictionary):
        """
        takes a dictionary of the form
        {"Text": (row_id, "attribute_name")}
        """
        self._col_map = mapping_dictionary
        rev_map = {}
        for key, val in self._col_map.items():
            rev_map[val[0]] = key

        self.rev_map = rev_map

    def __getitem__(self, key):
        return self._col_map[key]

    def iteritems(self):
        return iter(self._col_map.items())

    def sort_iteritems(self):
        for i in range(len(self.rev_map)):
            yield self.rev_map[i], self._col_map[self.rev_map[i]]

    def name_by_column(self, column):
        return self._col_map[self.rev_map[column]][1]

    def __len__(self):
        return len(self._col_map)


class TreeModel(gtk.GenericTreeModel):
    offset = 0  # number of elements to be cutoff from TreeIter paths

    def __init__(self, col_mapper):
        self.col_mapper = col_mapper
        gtk.GenericTreeModel.__init__(self)

    def get_object(self, gtk_tree_iter):
        """
        gtk has its on special tree_iter that don't do our cool stuff

        the method gets our on tree_iter-version of the gtk one and returns
        its holding object
        """
        tree_iter = self.get_user_data(gtk_tree_iter)
        return tree_iter._obj

    def highlight(self, obj, value, column=0):
        """
        highlights value depending on whether obj is merged
        or a terminology default etc.
        """
        color = None
        italics = False
        merged = obj.get_merged_equivalent()
        if merged is not None:
            if column == 0:
                color = "darkgrey"
            if merged == obj:
                color = "grey"

        merged = obj.get_terminology_equivalent()
        if column == 0 and merged is not None:
            italics = True

        if italics:
            value = "<i>%s</i>" % value

        # check for validation errors
        if column == 0:
            warning = -1
            doc = obj.document
            if doc is not None and hasattr(doc, "validation_result"):
                for err in doc.validation_result.errors:
                    if err.obj is obj:
                        warning = max(warning, 1 if err.is_error else 0)

            if warning >= 0:
                warn = "\u26A0"
                if sys.version_info.major < 3:
                    # Even with decode the warning symbol is not properly displayed
                    # in py2 when using the tree model. Using a workaround for now.
                    # warn = warn.decode('unicode-escape')
                    warn = "(!)"
                colors = ['orange', 'red']
                value = "%s <span foreground='%s'>%s</span>" % (value, colors[warning], warn)

        if color is None:
            return value
        return "<span foreground='%s'>%s</span>" % (color, value)

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return len(self.col_mapper)

    def on_get_column_type(self, index):
        return gobject.TYPE_STRING

    def on_get_path(self, tree_iter):
        return self.odml_path_to_model_path(tree_iter.to_path()[self.offset:])

    def on_get_value(self, tree_iter, column):
        attr = self.col_mapper.name_by_column(column)
        DEBUG(":on_get_value [%d:%s]: %s" % (column, attr, tree_iter))
        return tree_iter.get_value(attr)

    def on_iter_next(self, tree_iter):
        next = tree_iter.get_next()
        DEBUG(":on_iter_next [%s]: %s" % (tree_iter, next))
        return next

    def on_iter_children(self, tree_iter):
        DEBUG(":on_iter_children [%s]" % tree_iter)
        return tree_iter.get_children()

    def on_iter_has_child(self, tree_iter):
        DEBUG(":on_iter_has_child [%s,%s]" % (tree_iter, tree_iter.has_child))
        return tree_iter.has_child

    def on_iter_n_children(self, tree_iter):
        return tree_iter.n_children

    def on_iter_nth_child(self, tree_iter, n):
        DEBUG(":on_iter_nth_child [%d]: %s " % (n, tree_iter))
        if tree_iter is None:
            return None
        return tree_iter.get_nth_child(n)

    def on_iter_parent(self, tree_iter):
        DEBUG(":on_iter_parent [%s]" % tree_iter)
        return tree_iter.parent

    def _get_node_iter(self, node):
        raise NotImplementedError

    def get_node_iter(self, node):
        """
        returns the corresponding iter to a node
        """
        # ugly fix, so to get a GtkTreeIter from our custom Iter instance
        # we first convert our custom Iter to a path and the return an iter from it
        # (apparently they are different)
        custom_iter = self._get_node_iter(node)
        if custom_iter is not None:
            return self.create_tree_iter(custom_iter)

    def get_node_path(self, node):
        """
        returns the path of a node
        """
        custom_iter = self._get_node_iter(node)
        if custom_iter is not None:
            return self.on_get_path(custom_iter)

    def post_insert(self, node):
        """
        called to notify the treemodel that *node* is a new inserted row
        and the parent may have a child toggled
        """
        iter = self.get_node_iter(node)
        self.row_inserted(self.get_path(iter), iter)
        if self.iter_has_child(iter):
            self.row_has_child_toggled(self.get_path(iter), iter)
        # todo recurse to children!
        iter = self.iter_parent(iter)
        if iter is not None:
            self.row_has_child_toggled(self.get_path(iter), iter)

    def post_delete(self, parent, old_path):
        """
        called to notify the treemodel that the path *old_path* is no
        longer valid and parent might have its child toggled

        TODO figure out how to handle recursive removals
        """
        if hasattr(parent, "values") and len(parent.values) == 1:
            self.row_deleted((old_path[0], (old_path[1]+1) % 2))
        else:
            self.row_deleted(old_path)
        iter = self.get_node_iter(parent)

        # We need to check if the old path is already the very root.
        # In this case we don't need to check any child toggles, since
        # there are no toggleable children.
        if iter is not None and len(old_path) > 1:
            path = self.get_path(iter)
            if path:
                self.row_has_child_toggled(path, iter)

    def event_remove(self, context):
        """
        handles action="remove" events and notifies the model about
        occurred changes. Be sure to call this method for both pre_change
        and post_change events.
        """
        if not hasattr(context, "path"):
            context.path = {}
            context.parent = {}
        if context.pre_change:
            context.path[self] = self.get_node_path(context.val)
            context.parent[self] = context.val.parent
        if context.post_change:
            path = context.path[self]
            self.post_delete(context.parent[self], path)

    def event_insert(self, context):
        """
        handles action="append" and action="insert" events and notifies the
        model about occurred changes.
        """
        if context.post_change:
            self.post_insert(context.val)

    def event_reorder(self, context):
        """
        handles action="reorder" and notifies the model accordingly issuing
        a rows_reordered call
        """
        if context.pre_change and not hasattr(context, "neworder"):
            if not hasattr(context.val[0].parent, 'properties') and \
                    not hasattr(context.val[0].parent, 'author'):
                (value, new_index) = context.val
                child_list = value.parent.values
                old_index = child_list.index(getattr(value, "value"))
            elif hasattr(context.val[0].parent, 'author'):
                (sec, new_index) = context.val
                child_list = sec.parent.sections
                old_index = child_list.index(sec)
            else:
                (prop, new_index) = context.val
                child_list = prop.parent.properties
                old_index = child_list.index(prop)
            res = list(range(len(child_list)))
            res.insert(new_index, old_index)
            del res[old_index if new_index > old_index else (old_index+1)]
            context.new_order = res
        if context.post_change:
            if context.obj.parent is not self._section:
                iter = self.get_node_iter(context.obj.parent)
                path = self.get_path(iter)
                if not path:
                    return  # not our deal
                self.rows_reordered(path, iter, context.new_order)
