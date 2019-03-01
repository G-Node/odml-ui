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

    def test_document(self):
        self.assertIsNone(self.nav_bar.document)

        doc = self.create_ui_doc("Author")

        # make sure the change handler is empty
        self.assertIsInstance(doc, odmlui.treemodel.nodes.Document)
        self.assertIsNone(doc._change_handler)

        self.nav_bar.document = doc

        # check that the document has been set on the nav_bar
        self.assertEqual(doc, self.nav_bar.document)

        # make sure the proper nav_bar method has been set
        # on the documents change handler
        self.assertEqual(1, len(doc._change_handler))
        self.assertEqual(doc._change_handler.handlers[0], self.nav_bar.on_section_changed)

        # test that the document root is selected
        self.assertEqual(1, len(self.nav_bar._current_hierarchy))
        self.assertEqual(doc, self.nav_bar._current_hierarchy[0])
        self.assertEqual(doc, self.nav_bar._current_object)

        # test label text
        self.assertEqual(self.nav_bar.get_label(),
                         "Attributes | <a href=\"\"><b>Document</b></a> ")

        # test reset with a different document
        other_doc = self.create_ui_doc("Other author")
        self.nav_bar.document = other_doc

        self.assertNotEqual(doc, self.nav_bar.document)
        self.assertNotEqual(doc, self.nav_bar._current_hierarchy[0])
        self.assertNotEqual(doc, self.nav_bar._current_object)
        self.assertEqual(other_doc, self.nav_bar.document)
        self.assertEqual(other_doc, self.nav_bar._current_hierarchy[0])
        self.assertEqual(other_doc, self.nav_bar._current_object)

    @staticmethod
    def create_ui_doc(author=""):
        doc = odml.Document(author=author)
        sec = odml.Section(name="sec", parent=doc)
        _ = odml.Property(name="prop", parent=sec)

        for sec in doc.sections:
            handle_section_import(sec)

        return doc
