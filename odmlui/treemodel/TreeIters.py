import sys
from . import GenericIter
from . import nodes
from .ValueModel import Value

class PropIter(GenericIter.GenericIter):
    """
    An iterator for a Property

    returns ValueIter objects if queried for children.
    Since Values don't have a parent relationship, the PropIter will store
    pass a corresponding parent attribute (the Property object) to the ValueIter

    As odML supports multi-values, each property may or may not have multiple children.
    """

    def get_value(self, attr):
        if attr == "pseudo_values":
            if self.has_child:
                return self.get_mulitvalue(attr)
            else:
                return self.get_singlevalue(attr)

        else:
            return self.escape(getattr(self._obj, attr))

    def get_mulitvalue(self, name):
        # Most of the stuff is empty and handled by the ValueIter
        if name == "pseudo_values":
                return self.escape("<multi>")
        return ""

    def get_singlevalue(self, name):
        #here we proxy the value object
        if len(self._obj.pseudo_values) == 0:
            return ""

        return ValueIter(self._obj.pseudo_values[0]).get_value(name)

    @property
    def has_child(self):
        return self.n_children > 1

    @property
    def n_children(self):
        return len(self._obj.pseudo_values)

    @property
    def parent(self):
        return None

class ValueIter(GenericIter.GenericIter):
    """
    An iterator for a Value object
    """

    def get_value(self, attr):

        if attr == "pseudo_values":
            value = self._obj.get_display()

            # If the value is an empty string, render a placeholder text.
            if not value:
                value = '<i>n/a</i>'
            else:
                # Some issues with the rendering of `unicode` in Python 2 directly
                # to Tree Column cell renderer. Hence, first encode it here.
                if ValueIter.is_python2:
                    value = value.encode('utf-8')

                # Always escape "&" and "<" since they break assigning values containing
                # these characters.
                value = value.replace("&", "&amp;").replace("<", "&lt;")

            return value

        # Return an empty string for anything lese
        return ""


class SectionIter(GenericIter.GenericIter):
    @property
    def parent(self):
        if not self._obj.parent:
            return None
        if not self._obj.parent.parent: # the parent is the document root
            return None
        return super(SectionIter, self).parent

class SectionPropertyIter(GenericIter.GenericIter):
    @property
    def n_children(self):
        return len(self._obj.properties)

# associate the odml-classes to the corresponding iter-classes
nodes.Section.IterClass  = SectionIter
nodes.Property.IterClass = PropIter
Value.IterClass          = ValueIter
