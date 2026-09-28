#!/usr/bin/env python3
"""Regression for geometry-preserving duplicate self-land suppression."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from filter_duplicate_target_context import remove_target_land_context

SAMPLE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760">
<defs><linearGradient id="land"><stop offset="0" stop-color="#e2dbad"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient></defs>
<rect width="1200" height="760" fill="#eaf2f4"/>
<g id="geographic-context" fill="#e4e0ce"><path d="M 95,95 L 205,95 L 205,205 L 95,205 Z M 700,100 L 900,100 L 900,180 L 700,180 Z"/></g>
<path id="approved-target" d="M 100,100 L 200,100 L 200,200 L 100,200 Z" fill="url(#land)"/>
</svg>'''


class DuplicateContextTest(unittest.TestCase):
    def test_removes_only_duplicate_and_preserves_original_path(self):
        output, removed = remove_target_land_context(SAMPLE)
        self.assertEqual(removed, 1)
        self.assertNotIn('M 95,95 L 205,95', output)
        self.assertIn('M 700,100 L 900,100 L 900,180 L 700,180 Z', output)
        before = ET.fromstring(SAMPLE).find('.//*[@id="approved-target"]')
        after = ET.fromstring(output).find('.//*[@id="approved-target"]')
        self.assertEqual(ET.tostring(before), ET.tostring(after))

    def test_compound_hole_is_preserved(self):
        nested = SAMPLE.replace('M 700,100 L 900,100 L 900,180 L 700,180 Z',
                                'M 120,120 L 180,120 L 180,180 L 120,180 Z')
        output, removed = remove_target_land_context(nested)
        self.assertEqual((output, removed), (nested, 0))

    def test_unrecognized_curved_context_is_preserved(self):
        curved = SAMPLE.replace('M 95,95 L 205,95 L 205,205 L 95,205 Z',
                                'M 95,95 C 205,95 205,205 95,205 Z')
        output, removed = remove_target_land_context(curved)
        self.assertEqual((output, removed), (curved, 0))

    def test_unknown_land_gradient_is_preserved(self):
        unknown = SAMPLE.replace('id="land"', 'id="country"').replace('url(#land)', 'url(#country)')
        output, removed = remove_target_land_context(unknown)
        self.assertEqual((output, removed), (unknown, 0))


if __name__ == '__main__':
    unittest.main()
