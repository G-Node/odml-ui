# -*- coding: utf8

import odml.format as format
import odml.dtypes as dtypes

from odml.base import BaseObject

from . import nodes, event


class ValueNode(nodes.ParentedNode):
    def path_from(self, path):
        raise TypeError("Value objects have no children")

    def path_to(self, child):
        raise TypeError("Value objects have no children")


class ValueFormat(format.Format):
    _name = "value"
    _args = {}
    _map = {}


class Value(BaseObject, ValueNode, event.ModificationNotifier):
    """
    Since the odML value node has been merged with the odml.Property, and is
    only available as a 'pure' python list we cannot render it to the Editor
    UI directly. So, we make use of this wrapper class which acts as a mapper
    between the model values and the values rendered in Editor UI.

    A list of objects from this class is added as an additional attribute to
    the original `odml.Property` node, as `pseudo_values`. All interactions
    from the Editor interact with these pseudo_values, and internally, these
    pseudo-values update the original property.values list.

    """
    _Changed = event.Event("value")
    _Changed.finish = event.pass_on_change
    _format = ValueFormat

    def __init__(self, parent, index=None):

        self._property = parent
        # Instantiate a new odML value
        if index is None:
            index = len(self._property.values)
            dtype = self.parent.dtype
            default_value = dtypes.default_values(dtype)
            # property.values returns a copy: we therefore need an in between step
            # to append a new value and reassign the modified value to the parent
            # property.values.
            val_cp = self.parent.values
            val_cp.append(default_value)
            self.parent.values = val_cp

        assert(isinstance(index, int))
        self._index = index

    def __repr__(self):
        return "PseudoValue <%s>" % self.get_display()

    def __eq__(self, obj):
        """
        Make sure all relevant attributes are properly compared.
        :param obj: odmlui PseudoValue

        :return: Boolean
        """
        if not isinstance(obj, self.__class__):
            return False

        if not self.parent == obj.parent:
            return False

        if not self.pseudo_values == obj.pseudo_values:
            return False

        return True

    @property
    def index(self):
        return self._index

    @property
    def parent(self):
        """the property containing this value"""
        return self._property

    @property
    def dtype(self):
        """
            Retuns the parent DType
        """
        return self.parent.dtype

    @property
    def pseudo_values(self):
        """
            Return a single element from the parent property's value list.
        """
        return self.parent._values[self._index]

    @pseudo_values.setter
    def pseudo_values(self, new_string):
        """
            First, try to check if the new value fits in the parent property's
            dtype. If it does, then update the value.
        """
        prop_dtype = self.parent.dtype
        new_value = dtypes.get(new_string, prop_dtype)

        set_values = self.parent.values
        set_values[self._index] = new_value
        self.parent.values = set_values

    @property
    def value(self):
        return self.pseudo_values

    def can_display(self, text=None, max_length=-1):
        """
        return whether the content of this can be safely displayed in the gui
        """
        if text is None:
            text = self.pseudo_values
        if text is None:
            return True

        if max_length != -1 and len(text) > max_length:
            return False

        if "\n" in text or "\t" in text:
            return False

        return True

    def get_display(self, max_length=-1):
        """
        return a textual representation that can be used for display

        typically takes the first line (max *max_length* chars) and adds '[...]'
        """
        text = str(self.pseudo_values)

        # Always escape "&" and "<" since they break the view otherwise.
        text = text.replace("&", "&amp;").replace("<", "&lt;")

        if self.can_display(text, max_length):
            return text

        text = text.split("\n")[0]
        if max_length != -1:
            text = text[:max_length]

        if self.can_display(text, max_length):
            return "%s [...]" % text

        return "(%d bytes)" % len(self._value)

    def reorder(self, new_index):
        return self._reorder(self.parent.values, new_index)

    def clone(self):
        obj = BaseObject.clone(self)
        obj._property = None
        return obj
