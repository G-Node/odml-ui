"""
This module provides gtk.GenericTreeModels and corresponding functionality.

The classes can be made default by importing odmlui.treemodel.mixin.
It provides a PropertyModel class for a list-based view showing Properties and Values
and a SectionModel class for a tree-view showing Sections and Subsections
"""

from . import nodes
from . import PropertyModel
from . import SectionModel
