"""
Tests for odmlui.helpers functions.
"""

import os
import unittest

import odml

from odmlui import helpers
from odmlui.treemodel.value_model import Value as PseudoValue


class TestHelpers(unittest.TestCase):
    def setUp(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.basepath = os.path.join(dir_path, "resources")

    def test_get_extension(self):
        filename = "testextension.xml"
        ext = "XML"

        filepath = os.path.join(self.basepath, filename)
        self.assertEqual(ext, helpers.get_extension(filepath))

        filename = "IdoNotExist"
        filepath = os.path.join(self.basepath, filename)
        self.assertEqual("", helpers.get_extension(filepath))

    def test_get_parser_for_uri(self):
        xml_uri = os.path.join(self.basepath, "IdoNotExist.xml")
        self.assertEqual("XML", helpers.get_parser_for_uri(xml_uri))

        json_uri = os.path.join(self.basepath, "IdoNotExist.json")
        self.assertEqual("JSON", helpers.get_parser_for_uri(json_uri))

        yaml_uri = os.path.join(self.basepath, "IdoNotExist.yaml")
        self.assertEqual("YAML", helpers.get_parser_for_uri(yaml_uri))

        default_uri = os.path.join(self.basepath, "IdoNotExist.odml")
        self.assertEqual("XML", helpers.get_parser_for_uri(default_uri))

        default_uri = os.path.join(self.basepath, "IdoNotExist")
        self.assertEqual("XML", helpers.get_parser_for_uri(default_uri))

    def test_get_parser_for_file_type(self):
        x_type = "xml"
        y_type = "yaml"
        j_type = "json"
        default_type = "odml"

        self.assertEqual("XML", helpers.get_parser_for_file_type(x_type))
        self.assertEqual("YAML", helpers.get_parser_for_file_type(y_type))
        self.assertEqual("JSON", helpers.get_parser_for_file_type(j_type))
        self.assertEqual("XML", helpers.get_parser_for_file_type(default_type))

        default_type = ""
        self.assertEqual("XML", helpers.get_parser_for_file_type(default_type))

    def test_create_pseudo_values(self):
        # Test create empty pseudo value
        prop_empty = odml.Property()
        self.assertFalse(hasattr(prop_empty, "pseudo_values"))
        helpers.create_pseudo_values([prop_empty])
        self.assertTrue(hasattr(prop_empty, "pseudo_values"))
        self.assertEqual([], prop_empty.pseudo_values)

        # Test create pseudo values
        single = [1]
        multiple = ["a", "b", "c"]
        prop_single = odml.Property(name="single", value=single)
        prop_multiple = odml.Property(name="multiple", value=multiple)

        helpers.create_pseudo_values([prop_single, prop_multiple])
        self.assertIsInstance(prop_single.pseudo_values[0], PseudoValue)
        self.assertEqual(prop_single.pseudo_values[0].value, prop_single.values[0])

        self.assertEqual(len(prop_multiple.pseudo_values), len(multiple))
        self.assertIsInstance(prop_multiple.pseudo_values[1], PseudoValue)
        self.assertEqual(prop_multiple.pseudo_values[1].value, prop_multiple.values[1])

    def test_handle_property_import(self):

        # Test empty property imported with one string default value
        prop = odml.Property(name="empty test")
        self.assertEqual([], prop.values)
        helpers.handle_property_import(prop)
        self.assertEqual(1, len(prop.values))
        self.assertEqual([odml.dtypes.default_values("string")], prop.values)

        # Test empty property with dtype imported with one appropriate default value
        prop_dtype = odml.Property(name="dtype test", dtype="int")
        self.assertEqual([], prop_dtype.values)
        helpers.handle_property_import(prop_dtype)
        self.assertEqual(1, len(prop_dtype.values))
        self.assertEqual([odml.dtypes.default_values("int")], prop_dtype.values)

        vals = [1.0, 2.0, 3.0]
        prop_val = odml.Property(name="value test", values=vals)
        helpers.handle_property_import(prop_val)
        self.assertEqual(vals, prop_val.values)
        self.assertEqual("float", prop_val.dtype)
