import odml

from odml.base import Sectionable
from odml.property import BaseProperty
from odml.section import BaseSection

from .. import commands


class ActionDrop(object):
    """
    An ActionDrop is initialized with the *exec_func* argument.

    Calling self.execute(cmd) will then forward the call to *exec_func*.
    """
    def __init__(self, exec_func=None, *args, **kwargs):
        super(ActionDrop, self).__init__(*args, **kwargs)
        self.execute = exec_func

class GenericDrop(ActionDrop):
    """
    A Generic ActionDrop that allows to drop any object using the
    CopyOrMoveObject-command
    """
    def get_drop_dest(self, dst, action):
        return dst

    def odml_can_drop(self, action, dst, position, obj):
        return True

    def drop_object(self, action, dst, position, obj):
        cmd = commands.CopyOrMoveObject(obj=obj, dst=dst, copy=action.copy)
        return self.execute(cmd)

class ValueDrop(GenericDrop):
    def odml_can_drop(self, action, dst, position, obj):
        """
        can only move/copy into Properties
        """
        if action.link: return False
        return isinstance(dst, BaseProperty)

class PropertyDrop(GenericDrop):
    def get_drop_dest(self, dst, action):
        if action.link: return None
        while not isinstance(dst, BaseSection):
            dst = dst.parent
        return dst

    def odml_can_drop(self, action, dst, position, obj):
        """
        can only move/copy into Sections
        """
        if action.link: return False
        return isinstance(dst, BaseSection)

class SectionDrop(GenericDrop):
    def drop_object(self, action, dst, position, obj):
        """
        drop sections, but can also establish links or include attributes
        """
        if action.link:
            if dst.document is obj.document:
                cmd = commands.ChangeValue(
                        object=dst,
                        attr="link",
                        new_value=dst.get_relative_path(obj))
            else:
                cmd = commands.ChangeValue(
                        object=dst,
                        attr="include",
                        new_value=dst.filename + "#" + dst.document.get_relative_path(obj))
        else:
            return super(SectionDrop, self).drop_object(action, dst, position, obj)
        return self.execute(cmd)

    def odml_can_drop(self, action, dst, position, obj):
        """
        * can only establish links to Sections
        * can only move/copy into Sections/Documents
        """
        if action.link: return isinstance(dst, BaseSection)
        return isinstance(dst, Sectionable)

# TODO make links / include from other apps work
