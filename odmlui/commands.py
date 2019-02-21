"""
Collection of Command classes with execute and undo methods to be used
together with the CommandManager class to enable execute and undo
actions within the Application.
"""


class Command(object):
    """
    Command is the base class for execute and undo capable commands.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __call__(self):
        self._execute()
        self.on_action()

    def _execute(self):
        pass

    def on_action(self, undo=False):
        """
        Placeholder method for any command specific execution code
        """
        pass

    def undo(self):
        """
        Execute the undo specific method of a command
        """
        self._undo()
        self.on_action(undo=True)

    def _undo(self):
        pass

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, ', '.join(
            ["%s=%s" % (k, v) for k, v in self.__dict__.items()]))


class Multiple(Command):
    """
    Multiple(cmds=[])

    Supported kwargs: *cmds* list of 'Command' objects.

    Aggregator of multiple 'odmlui.commands.Command' objects.
    """
    def __init__(self, *args, **kwargs):
        self.cmds = []
        super(Multiple, self).__init__(*args, **kwargs)

    def _execute(self):
        for cmd in self.cmds:
            cmd()

    def _undo(self):
        for cmd in self.cmds:
            cmd.undo()


class ChangeValue(Command):
    """
    ChangeValue(object=, attr=, new_value=)

    Supported kwargs: *object* object, *attr* (an attribute of the object),
                      *new_value* text

    If *attr* is a list, only the first attribute is changed, but all other attributes
    are stored for the undo mechanism.
    """
    _required = ['object', 'attr', 'new_value']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.object = {}
        self.attr = []
        self.new_value = None
        self.old_value = None

        super(ChangeValue, self).__init__(*args, **kwargs)

    def _execute(self):
        if not isinstance(self.attr, list):
            self.attr = [self.attr]

        self.old_value = {}
        for attr in self.attr:
            self.old_value[attr] = getattr(self.object, attr)

        setattr(self.object, self.attr[0], self.new_value)

    def _undo(self):
        if not hasattr(self, "old_value"):
            # execute failed
            return

        for attr in self.attr:
            setattr(self.object, attr, self.old_value[attr])


class AppendValue(Command):
    """
    AppendValue(obj=, val=)

    Appends value *val* to an append capable object *obj*.
    """
    _required = ['obj', 'val']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.obj = None
        self.val = None

        super(AppendValue, self).__init__(*args, **kwargs)

    def _execute(self):
        self.index = len(self.obj)
        self.obj.append(self.val)

    def _undo(self):
        try:
            if self.obj[self.index] == self.val:
                del self.obj[self.index]
                return
        except (IndexError, TypeError):
            # Document or Section deletion raise a TypeError at this point.
            pass

        if hasattr(self.obj, "pop"):
            val = self.obj.pop()
            if val == self.val:
                return
            self.obj.append(val)

        self.obj.remove(self.val)


class DeleteObject(Command):
    """
    DeleteObject(obj=)

    Removes *obj* from its parent.
    """
    _required = ['obj']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.obj = None

        super(DeleteObject, self).__init__(*args, **kwargs)
        # use an AppendCommand for the actual operation but use it reversed
        self.append_cmd = AppendValue(obj=self.obj.parent, val=self.obj)
        self.append_cmd.index = self.obj.position

    def _execute(self):
        """
        Remove *obj* (append_cmd.val) from its parent
        """
        self.append_cmd._undo()

    def _undo(self):
        """
        Append *obj* (append_cmd.val) to its original parent (append_cmd.obj)
        """
        self.append_cmd._execute()


class ReorderObject(Command):
    """
    ReorderObject(obj=, new_index=)

    Calls obj.reorder(new_index) to move *obj* to new position *new_index*
    in its parent list.
    """
    _required = ['obj', 'new_index']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.obj = None
        self.new_index = None
        self.old_index = None
        super(ReorderObject, self).__init__(*args, **kwargs)

    def _execute(self):
        self.old_index = self.obj.reorder(self.new_index)

    def _undo(self):
        if self.old_index:
            self.obj.reorder(self.old_index)


# So far, the application is not actually using this class
class CopyObject(Command):
    """
    CopyObject(obj=, dst=)

    Appends a clone of *obj* to destination object *dst*.
    """
    # Cannot add 'dst' as required attribute, since ReplaceObject inherits
    # from CopyObject and does not feature the 'dst' attribute.
    _required = ['obj']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.obj = None
        self.dst = None
        self.new_obj = None
        super(CopyObject, self).__init__(*args, **kwargs)

    def get_new_object(self):
        """
        Clone handed in object
        """
        return self.obj.clone()

    def _execute(self):
        """
        Clone obj and append it to dst.
        """
        self.new_obj = self.get_new_object()
        self.dst.append(self.new_obj)

    def _undo(self):
        """
        Remove the clone from its parent.
        """
        parent = self.new_obj.parent
        if parent is not None:
            parent.remove(self.new_obj)


class MoveObject(CopyObject):
    """
    MoveObject(obj=, dst=)

    Removes *obj* from *obj.parent* and appends it to destination object *dst*.
    """
    _required = ['dst']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.parent = None
        self.index = None
        super(MoveObject, self).__init__(*args, **kwargs)

    def get_new_object(self):
        """
        Used in the inherited Copy.Object._execute method.
        Removes the handed in object from its parent and
        returns the object.
        """
        try:
            self.index = self.obj.position
        except AttributeError:
            self.index = self.obj.parent.index(self.obj)

        self.parent = self.obj.parent
        self.parent.remove(self.obj)

        return self.obj

    # _execute is inherited from CopyObject

    def _undo(self):
        """
        Move obj back to its original parent and try to insert it at its old position.
        """
        super(MoveObject, self)._undo()
        try:
            self.parent.insert(self.index, self.obj)
        except TypeError:
            self.parent.append(self.obj)


class ReplaceObject(MoveObject):
    """
    ReplaceObject(obj=, repl=)

    Removes *obj* from *obj.parent* and appends object *repl* to *obj.parent*.
    It does not remove *repl* from *repl.parent*, use only with a cloned *repl* object.
    """
    _required = ['repl']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.repl = None
        self.new_obj = None
        super(ReplaceObject, self).__init__(*args, **kwargs)

    def _execute(self):
        self.new_obj = self.get_new_object()
        self.obj = self.repl
        self.repl = self.new_obj
        # insert self.obj (=repl) into self.parent (=obj.parent)
        super(ReplaceObject, self)._undo()

    def _undo(self):
        # exchange the objects again and execute in reverse
        self._execute()


class CopyOrMoveObject(Command):
    """
    CopyOrMoveObject(obj=, dst=, copy=True/False)

    Depending on the value of *copy*, a CopyObject or a MoveObject
    will be initialised.
    Object *obj* will be copied or moved to destination object *dst*.
    """
    _required = ['obj', 'dst']

    def __init__(self, *args, **kwargs):
        for req in self._required:
            if req not in kwargs:
                raise TypeError("Missing positional argument %s" % req)

        self.obj = None
        self.dst = None
        self.copy = None

        super(CopyOrMoveObject, self).__init__(*args, **kwargs)
        cmd_class = CopyObject if self.copy else MoveObject
        self.cmd = cmd_class(obj=self.obj, dst=self.dst)

    def _execute(self):
        self.cmd()

    def _undo(self):
        self.cmd.undo()
