#!/usr/bin/env python3
"""Regression: SVG group translations must affect land geometry during map QA."""
import unittest
import xml.etree.ElementTree as ET
from validate_country_map_v6 import collect_transformed_land_paths, on_land_in_path

class TranslatedLandTest(unittest.TestCase):
    def test_nested_group_translation_and_negative_offsets(self):
        root = ET.fromstring("<svg><g transform='translate(10 20)'><g transform='translate(-3 5)'><path d='M0 0 L10 0 L10 10 L0 10 Z'/></g></g></svg>")
        groups, errors = collect_transformed_land_paths(root)
        self.assertEqual(errors, [])
        self.assertEqual(len(groups), 1)
        self.assertTrue(on_land_in_path(groups[0], (12, 30)))
        self.assertFalse(on_land_in_path(groups[0], (2, 3)))
    def test_untranslated_land_still_valid(self):
        root = ET.fromstring("<svg><path d='M0 0 L10 0 L10 10 L0 10 Z'/></svg>")
        groups, errors = collect_transformed_land_paths(root)
        self.assertEqual(errors, [])
        self.assertTrue(on_land_in_path(groups[0], (5, 5)))
    def test_unsupported_transform_fails_closed(self):
        root = ET.fromstring("<svg><g transform='rotate(10)'><path d='M0 0 L10 0 L10 10 L0 10 Z'/></g></svg>")
        groups, errors = collect_transformed_land_paths(root)
        self.assertFalse(groups)
        self.assertEqual(errors, ['rotate(10)'])

if __name__ == '__main__':
    unittest.main()
