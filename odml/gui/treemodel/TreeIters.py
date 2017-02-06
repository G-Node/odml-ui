import GenericIter

class PropIter(GenericIter.GenericIter):
    """
    An iterator for a Property

    returns ValueIter objects if queried for children.
    Since Values don't have a parent relationship, the PropIter will store
    pass a corresponding parent attribute (the Property object) to the ValueIter

    As odML supports multi-values, each property may or may not have multiple children.
    """

    def get_value(self, attr):
        if attr == "name":
            return self.escape(self._obj.name)

        if self.has_child:
            return self.get_mulitvalue(attr)
        else:
            return self.get_singlevalue(attr)

    def get_mulitvalue(self, name):
        #Most of the stuff is empty and handled by the
        #value
        if name == "value":
                return self.escape("<multi>")
        return ""

    def get_singlevalue(self, name):
        #here we proxy the value object
        if len(self._obj._values) == 0:
            return ""

        return ValueIter(self._obj.values[0]).get_value(name)

    @property
    def has_child(self):
        return self.n_children > 1

    @property
    def n_children(self):
        return len(self._obj._values)

    @property
    def parent(self):
        return None

class ValueIter(GenericIter.GenericIter):
    """
    An iterator for a Value object
    """
    def get_value(self, attr):
        if attr == "name":
            return
        if attr == "value":
            return self._obj.get_display()
        return super(ValueIter, self).get_value(attr)

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
import odml.tools.nodes as nodes
nodes.Section.IterClass  = SectionIter
nodes.Property.IterClass = PropIter
nodes.Value.IterClass    = ValueIter
