"""
Tests for odmlui.navigation_bar class.
"""

import unittest

from odmlui.navigation_bar import NavigationBar


class TestNavigationBar(unittest.TestCase):

    def setUp(self):
        self.nav_bar = NavigationBar()

    def test_init(self):
        self.assertIsNone(self.nav_bar._document)
        self.assertIsNone(self.nav_bar._current_object)
        self.assertEqual([], self.nav_bar._current_hierarchy)

