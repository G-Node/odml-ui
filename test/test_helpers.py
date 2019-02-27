"""
Tests for odmlui.helpers functions.
"""

import os
import unittest

from odmlui import helpers


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
