import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk

from . import drag
from . import drop

class Action(object):
    """
    Wraps the gtk.gdk.ACTION_ constants for easier pythonic access
    """
    def __init__(self, action):
        self.action = action

    @property
    def move(self):
        return (self.action & gtk.gdk.ACTION_MOVE)

    @property
    def copy(self):
        return (self.action == gtk.gdk.ACTION_COPY)

    @property
    def link(self):
        return (self.action == gtk.gdk.ACTION_LINK)


class TreeDropTarget(drop.DropTarget):
    """
    A TreeDropTarget is a DropTarget explicitly applicable for TreeView widgets.

    It translates the x,y-coordinates into actual model and iter objects and thus
    provides the methods:

    * tree_can_drop(action, model, iter, position, data=None):
    * tree_receive_data(action, model, iter, position, data=None)
    """
    def can_drop(self, treeview, context, x, y, data=None):
        model = treeview.get_model()
        action = Action(context.get_suggested_action())
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if not drop_info:
            return self.tree_can_drop(action, model, None, -1, data)

        path, position = drop_info
        iter = model.get_iter(path)
        return self.tree_can_drop(action, model, iter, position, data)

    def tree_can_drop(self, action, model, iter, position, data=None):
        return True

    def receive_data(self, treeview, context, x, y, data, etime):
        model = treeview.get_model()
        action = Action(context.get_actions())
        drop_info = treeview.get_dest_row_at_pos(x, y)

        if not drop_info:
            return self.tree_receive_data(action, data, model, None, -1)

        path, position = drop_info
        iter = model.get_iter(path)
        return self.tree_receive_data(action, data, model, iter, position)

    def tree_receive_data(self, action, data, model, iter, position):
        raise NotImplementedError

class TreeDragTarget(drag.DragTarget):
    """
    A TreeView-specific DragTarget. See also TreeDropTarget.

    it uses the org-selection data from the context (it is provided by the
    DragProvider to account for widget-changes while dragging)
    """
    def tree_get_source(self, treeview, context):
        treeselection = context.org_selection if context else None
        if treeselection is None:
            treeselection = treeview.get_selection()
            model, iter = treeselection.get_selected()
        else:
            model, iter = treeselection
        return model, iter

    def get_data(self, treeview, context):
        model, iter = self.tree_get_source(treeview, context)
        action = Action(context.get_actions() if context is not None else 0)
        return self.tree_get_data(action, model, iter)

    def tree_get_data(self, action, model, iter):
        raise NotImplementedError

    def delete_data(self, treeview, context):
        model, iter = self.tree_get_source(treeview, context)
        return self.tree_delete_data(model, iter)

    def tree_delete_data(self, model, iter):
        pass
