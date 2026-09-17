#!/usr/bin/env python3
"""Regression checks for the Content QA v6 land fill rule."""
from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from validate_country_map_v6 import collect_path_groups, on_land_in_path, translate_offset


class LandFillParityTest(unittest.TestCase):
    def test_mainland_close_to_offshore_island_is_not_cancelled(self):
        mainland = [(0, 0), (30, 0), (30, 30), (0, 30)]
        island = [(31, 14), (35, 14), (35, 18), (31, 18)]
        self.assertTrue(on_land_in_path([mainland, island], (29, 16)))

    def test_offshore_point_remains_water(self):
        mainland = [(0, 0), (30, 0), (30, 30), (0, 30)]
        island = [(31, 14), (35, 14), (35, 18), (31, 18)]
        self.assertFalse(on_land_in_path([mainland, island], (50, 50)))

    def test_coastline_tolerance_is_preserved(self):
        mainland = [(0, 0), (30, 0), (30, 30), (0, 30)]
        self.assertTrue(on_land_in_path([mainland], (32, 15)))

    def test_true_hole_remains_water(self):
        mainland = [(0, 0), (30, 0), (30, 30), (0, 30)]
        hole = [(5, 5), (20, 5), (20, 20), (5, 20)]
        self.assertFalse(on_land_in_path([mainland, hole], (12, 12)))

    def test_island_in_hole_remains_land(self):
        mainland = [(0, 0), (30, 0), (30, 30), (0, 30)]
        hole = [(5, 5), (20, 5), (20, 20), (5, 20)]
        island = [(10, 10), (14, 10), (14, 14), (10, 14)]
        self.assertTrue(on_land_in_path([mainland, hole, island], (12, 12)))

    def test_translate_parser_accepts_svg_comma_and_space_forms(self):
        self.assertEqual(translate_offset("translate(260 0)"), (260.0, 0.0))
        self.assertEqual(translate_offset("translate(-906, 12)"), (-906.0, 12.0))
        self.assertEqual(translate_offset("translate(10) translate(5 -3)"), (15.0, -3.0))

    def test_translate_parser_rejects_other_transform_types(self):
        self.assertIsNone(translate_offset("scale(2)"))
        self.assertIsNone(translate_offset("translate(10 0) rotate(5)"))

    def test_ancestor_translate_moves_land_geometry_into_rendered_position(self):
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g transform="translate(260 0)">'
            '<path d="M 0 0 L 100 0 L 100 100 L 0 100 Z"/>'
            '</g></svg>'
        )
        groups = collect_path_groups(root)
        self.assertEqual(len(groups), 1)
        self.assertTrue(on_land_in_path(groups[0], (310, 50)))
        self.assertFalse(on_land_in_path(groups[0], (50, 50)))

    def test_nested_translate_is_accumulated(self):
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g transform="translate(100 20)"><g transform="translate(30 -5)">'
            '<path d="M 0 0 L 20 0 L 20 20 L 0 20 Z"/>'
            '</g></g></svg>'
        )
        groups = collect_path_groups(root)
        self.assertTrue(on_land_in_path(groups[0], (140, 25)))
        self.assertFalse(on_land_in_path(groups[0], (10, 10)))


if __name__ == "__main__":
    unittest.main()
