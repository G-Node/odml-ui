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
