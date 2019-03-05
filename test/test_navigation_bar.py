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
        self.nav_bar = None
        self.nav_bar = NavigationBar()

    def test_init(self):
        self.assertIsNone(self.nav_bar._document)
        self.assertIsNone(self.nav_bar._current_object)
        self.assertEqual([], self.nav_bar._current_hierarchy)

    def test_update_display(self):
        self.assertEqual("", self.nav_bar.get_label())

        self.nav_bar.update_display()
        self.assertEqual("Attributes |  ", self.nav_bar.get_label())

        # manually set selected objects and object hierarchy
        # to simulate test case.
        doc = self.create_ui_doc()

        # test document root selected
        self.nav_bar._current_object = doc
        self.nav_bar._current_hierarchy = [doc]
        self.assertEqual("Attributes |  ", self.nav_bar.get_label())

        self.nav_bar.update_display()
        self.assertEqual(self.nav_bar.get_label(),
                         "Attributes | <a href=\"\"><b>Document</b></a> ")

        # test property selected
        sec = doc.sections[0]
        prop = doc.sections[0].properties[0]
        self.nav_bar._current_object = prop
        self.nav_bar._current_hierarchy = [prop, sec, doc]

        self.nav_bar.update_display()

        wanted = "Attributes | <a href=\"\">Document</a>: " + \
                 "<a href=\"0\">sec</a>: " + \
                 "<a href=\"0:1:0\"><b>prop</b></a> "

        self.assertEqual(self.nav_bar.get_label(), wanted)

    def test_current_object(self):
        self.assertIsNone(self.nav_bar.current_object)
        self.assertEqual(self.nav_bar.get_label(), "")

        doc = self.create_ui_doc()

        # the current_object setter ignores the '_current_hierarchy'
        # attribute, we need to deal with this manually.
        self.nav_bar._current_hierarchy = [doc]

        self.nav_bar.current_object = doc
        self.assertEqual(doc, self.nav_bar.current_object)
        self.assertEqual(self.nav_bar.get_label(),
                         "Attributes | <a href=\"\"><b>Document</b></a> ")

        sec = doc.sections[0]
        prop = doc.sections[0].properties[0]
        self.nav_bar._current_hierarchy = [prop, sec, doc]

        self.nav_bar.current_object = prop
        self.assertEqual(prop, self.nav_bar.current_object)

        wanted = "Attributes | <a href=\"\">Document</a>: " + \
                 "<a href=\"0\">sec</a>: " + \
                 "<a href=\"0:1:0\"><b>prop</b></a> "
        self.assertEqual(self.nav_bar.get_label(), wanted)

    def test_set_model(self):
        self.assertIsNone(self.nav_bar.current_object)
        self.assertEqual(self.nav_bar.get_label(), "")

        doc = self.create_ui_doc()
        self.nav_bar.set_model(doc)

        self.assertEqual(doc, self.nav_bar.current_object)
        self.assertEqual([doc], self.nav_bar._current_hierarchy)
        self.assertEqual(self.nav_bar.get_label(),
                         "Attributes | <a href=\"\"><b>Document</b></a> ")

        sec = doc.sections[0]
        prop = doc.sections[0].properties[0]
        self.nav_bar.set_model(prop)
        self.assertEqual(prop, self.nav_bar.current_object)
        self.assertEqual([prop, sec, doc], self.nav_bar._current_hierarchy)
        wanted = "Attributes | <a href=\"\">Document</a>: " + \
                 "<a href=\"0\">sec</a>: " + \
                 "<a href=\"0:1:0\"><b>prop</b></a> "
        self.assertEqual(self.nav_bar.get_label(), wanted)

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

    def test_switch(self):
        doc = self.create_ui_doc()
        self.nav_bar.document = doc

        self.assertEqual(self.nav_bar.current_object, doc)

        prop = doc.sections[0].properties[0]

        self.nav_bar.emit("activate-link", "0:1:0")
        self.assertEqual(self.nav_bar.current_object, prop)

        sec = doc.sections[0]
        self.nav_bar.emit("activate-link", "0")
        self.assertEqual(self.nav_bar.current_object, sec)

        self.nav_bar.emit("activate-link", "")
        self.assertEqual(self.nav_bar.current_object, doc)

    @staticmethod
    def create_ui_doc(author=""):
        doc = odml.Document(author=author)
        sec = odml.Section(name="sec", parent=doc)
        _ = odml.Property(name="prop", parent=sec)

        for sec in doc.sections:
            handle_section_import(sec)

        return doc
