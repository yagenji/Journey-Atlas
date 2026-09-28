#!/usr/bin/env python3
"""Regression tests for the opt-in shared geographic-context stage."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from add_country_map_context import (
    SEA_COLORS, add_context, canvas_bounds, context_geometry, make_context_path,
)
from generate_country_map import project
from shapely.geometry import box

BOUNDS = (44.45, 38.05, 50.72, 42.12)
SAMPLE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" data-map-projection="local-equirectangular-fit-v1"><defs><linearGradient id="sea"><stop stop-color="#eef2ef"/><stop stop-color="#e4eceb"/><stop stop-color="#dce7e7"/></linearGradient><linearGradient id="land"><stop stop-color="#e2dbad"/></linearGradient></defs><rect width="1200" height="760" fill="url(#sea)"/><path id="country" d="M10 10 L20 10 L20 20Z" fill="url(#land)" stroke="#31576a"/></svg>'''


class GeographicContextTest(unittest.TestCase):
    def test_canvas_bands_reach_exact_edges(self):
        west, south, east, north = canvas_bounds(BOUNDS)
        self.assertLess(west, BOUNDS[0])
        self.assertGreater(east, BOUNDS[2])
        self.assertAlmostEqual(project(west, north, BOUNDS)[0], 0)
        self.assertAlmostEqual(project(east, south, BOUNDS)[0], 1200)
        self.assertAlmostEqual(project(west, north, BOUNDS)[1], 0)
        self.assertAlmostEqual(project(east, south, BOUNDS)[1], 760)

    def test_inject_does_not_change_target_geometry(self):
        result = add_context(SAMPLE, BOUNDS, 'M 0,0 L 1200,0 L 1200,760 Z', 'i')
        before, after = ET.fromstring(SAMPLE), ET.fromstring(result)
        namespace = '{http://www.w3.org/2000/svg}'
        self.assertEqual(before.find(f'{namespace}path').attrib, after.find(f'{namespace}path').attrib)
        self.assertEqual(after.attrib['viewBox'], '0 0 1200 760')
        self.assertIn('fill="#e4e0ce"', result)
        self.assertIn('stroke="#b6bbaf"', result)
        for color in SEA_COLORS:
            self.assertIn(color, result)
        self.assertLess(result.index('id="geographic-context"'), result.index('id="country"'))
        with self.assertRaisesRegex(ValueError, 'already has geographic context'):
            add_context(result, BOUNDS, 'M 0,0 L 1200,0 L 1200,760 Z', 'i')

    def test_no_foreign_coastline_is_valid(self):
        result = add_context(SAMPLE, BOUNDS, '', 'i')
        self.assertNotIn('id="geographic-context"', result)
        self.assertIn(SEA_COLORS[0], result)

    def test_transformed_and_unknown_geometry_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'Transformed target'):
            add_context(SAMPLE.replace('id="country"', 'id="country" transform="translate(10,0)"'), BOUNDS, 'M 0,0 Z', 'i')
        with self.assertRaisesRegex(ValueError, 'No approved target-country path'):
            add_context(SAMPLE.replace('fill="url(#land)" stroke=', 'fill="#e2dbad" stroke='), BOUNDS, 'M 0,0 Z', 'i')
        with self.assertRaisesRegex(ValueError, 'Unrecognized sea palette'):
            add_context(SAMPLE.replace('#eef2ef', '#faffff'), BOUNDS, 'M 0,0 Z', 'i')
        with self.assertRaisesRegex(ValueError, 'Unknown map projection'):
            add_context(SAMPLE.replace('local-equirectangular-fit-v1', 'other'), BOUNDS, 'M 0,0 Z', 'i')

    def test_inherited_and_multiple_target_paths_keep_original_markup(self):
        source = SAMPLE.replace('<path id="country" d="M10 10 L20 10 L20 20Z" fill="url(#land)" stroke="#31576a"/>',
                                '<g fill="url(#land)"><path id="one" d="M10 10 L20 10 L20 20Z"/>'
                                '<path id="two" d="M30 10 L40 10 L40 20Z"/></g>'
                                '<g fill="url(#sea)"><path id="water" d="M50 10 L60 10 L60 20Z"/></g>')
        root = ET.fromstring(source)
        result = add_context(source, BOUNDS, 'M 0,0 L 1200,0 L 1200,760 Z', 'i')
        after = ET.fromstring(result)
        for name in ('one', 'two', 'water'):
            self.assertEqual(root.find(f'.//*[@id="{name}"]').attrib,
                             after.find(f'.//*[@id="{name}"]').attrib)
        self.assertLess(result.index('id="geographic-context"'), result.index('id="one"'))

    def test_mixed_target_transforms_and_css_fail_closed(self):
        source = SAMPLE.replace('</svg>', '<path d="M50 50 L60 50 Z" fill="url(#land)" transform="translate(1,1)"/></svg>')
        with self.assertRaisesRegex(ValueError, 'different transforms'):
            add_context(source, BOUNDS, 'M 0,0 Z', 'i')
        with self.assertRaisesRegex(ValueError, 'Styled SVG'):
            add_context(SAMPLE.replace('id="country"', 'id="country" style="fill:url(#land)"'),
                        BOUNDS, 'M 0,0 Z', 'i')

    def test_context_path_uses_real_geometry_and_canvas_fit(self):
        viewport = canvas_bounds(BOUNDS)
        path = make_context_path(box(viewport[0], viewport[1], BOUNDS[0], viewport[3]), BOUNDS, 0)
        self.assertIn('0.0,0.0', path)
        self.assertIn('0.0,760.0', path)
        ET.fromstring(add_context(SAMPLE, BOUNDS, path, 'i'))

    def test_gshhs_coastline_available_for_azerbaijan(self):
        geometry = context_geometry(canvas_bounds(BOUNDS), 'i')
        self.assertIsNotNone(geometry)
        self.assertFalse(geometry.is_empty)
        self.assertTrue(geometry.is_valid)
        self.assertGreater(geometry.area, 1)


if __name__ == '__main__':
    unittest.main()
