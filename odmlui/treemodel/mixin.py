"""
This module extends the odML base class by adding tree-functionality for
gtk.GenericTreeModels using MixIns

to use it just import this module::

    >>> import odmlui.treemodel.mixin

Alternatively you can import the modified Value/Property/Section/Document
classes manually::

    >>> import odml.tools.nodes as odml
    >>> s = odml.Section("animal_keeping section")

Or get the implementation once it is registered::

    >>> import odml
    >>> import odml.tools.nodes
    >>> odml.getImplementation('nodes').Section("animal_keeping section")

"""
#Please note: tree-functionality is already based on event-functionality.
#Therefore mixin in odml.tools.events will be troublesome / not work.

import odml
from . import nodes
odml.setMinimumImplementation('nodes')

