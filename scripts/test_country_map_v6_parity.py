#!/usr/bin/env python3
"""Regression checks for the Content QA v6 land fill rule."""
from __future__ import annotations

import unittest

from validate_country_map_v6 import on_land_in_path


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


if __name__ == "__main__":
    unittest.main()
