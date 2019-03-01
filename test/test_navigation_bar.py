"""
Tests for odmlui.navigation_bar class.
"""

import unittest

import odml

# Import is required to use the event capable odmlui implementation
# of odml entities (Document, Section, Property).
import odmlui.treemodel.mixin

from odmlui.helpers import handle_section_import
from odmlui.navigation_bar import NavigationBar


class TestNavigationBar(unittest.TestCase):

    def setUp(self):
        self.nav_bar = NavigationBar()

    def test_init(self):
        self.assertIsNone(self.nav_bar._document)
        self.assertIsNone(self.nav_bar._current_object)
        self.assertEqual([], self.nav_bar._current_hierarchy)

    @staticmethod
    def create_ui_doc(author=""):
        doc = odml.Document(author=author)
        sec = odml.Section(name="sec", parent=doc)
        _ = odml.Property(name="prop", parent=sec)

        for sec in doc.sections:
            handle_section_import(sec)

        return doc
