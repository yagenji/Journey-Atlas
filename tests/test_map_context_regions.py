#!/usr/bin/env python3
"""Regression for explicit geographic regions and checked legacy projection."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from add_country_map_context import add_context, canvas_bounds, context_geometry, frame, make_context_path
from shapely.geometry import Point, box

ICELAND = (-25.8, 62.8, -12.2, 67.1)
US = (-180, 18, -66, 72.5)
REGIONS = [
    {"id": "lower48", "bounds": {"west": -125.5, "south": 24, "east": -66, "north": 50.5},
     "rect": {"x": 290, "y": 65, "width": 900, "height": 630}},
    {"id": "alaska", "bounds": {"west": -190, "south": 50.5, "east": -129, "north": 72.5},
     "rect": {"x": 49, "y": 75, "width": 220, "height": 300}},
    {"id": "hawaii", "bounds": {"west": -161.5, "south": 18.5, "east": -154.3, "north": 22.8},
     "rect": {"x": 39, "y": 485, "width": 240, "height": 180}},
]
BEGIN = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" data-map-projection="{}"><defs><linearGradient id="sea"><stop stop-color="#eef2ef"/><stop stop-color="#e4eceb"/><stop stop-color="#dce7e7"/></linearGradient></defs><rect width="1200" height="760" fill="url(#sea)"/>'
END = '</svg>'


class RegionContextTest(unittest.TestCase):
    def test_iceland_aspect_matrix_kept_and_mismatch_rejected(self):
        correct = 'matrix(0.848131 0 0 1.000000 91.121 0.000)'
        source = BEGIN.format('local-equirectangular-fit-v1') + '<path transform="' + correct + '" d="M10 10L20 10Z" fill="url(#land)"/>' + END
        output = add_context(source, ICELAND, 'M 0,0 L 1200,0 L 1200,760 Z', 'i')
        self.assertIn('transform="' + correct + '"', output)
        self.assertIn('id="geographic-context"', output)
        with self.assertRaisesRegex(ValueError, 'does not match canonical'):
            add_context(source.replace('91.121', '92.121'), ICELAND, '', 'i')
        with self.assertRaisesRegex(ValueError, 'does not match canonical'):
            add_context(source.replace('transform="' + correct + '"', 'transform="translate(1)"'), ICELAND, '', 'i')

    def test_regional_clips_keep_existing_target_paths(self):
        source = BEGIN.format('multi-region-local-equirectangular-fit-v1')
        for name in ('lower48', 'alaska', 'hawaii'):
            source += f'<g data-map-region="{name}" transform="translate(260 0)"><path id="target-{name}" d="M10 10L20 20Z" fill="url(#land)"/></g>'
        source += END
        paths = {region['id']: 'M 0,0 L 1200,0 L 1200,760 Z' for region in REGIONS}
        output = add_context(source, US, paths, 'i', REGIONS)
        root = ET.fromstring(output)
        for name in ('lower48', 'alaska', 'hawaii'):
            self.assertIn(f'id="map-context-clip-{name}"', output)
            self.assertIn(f'data-map-context-region="{name}"', output)
            self.assertEqual(root.find(f".//*[@id='target-{name}']").attrib['d'], 'M10 10L20 20Z')
            self.assertLess(output.index('id="geographic-context"'), output.index(f'data-map-region="{name}"'))
        self.assertEqual(root.attrib['viewBox'], '0 0 1200 760')

    def test_full_region_sidebands_project_to_rect_edges(self):
        for region in REGIONS:
            b = tuple(region['bounds'][key] for key in ('west', 'south', 'east', 'north'))
            rect = tuple(region['rect'][key] for key in ('x', 'y', 'width', 'height'))
            west, south, east, north = canvas_bounds(b, rect)
            factor, scale, ox, oy = frame(b, rect)
            self.assertAlmostEqual(ox + (west - b[0]) * factor * scale, rect[0])
            self.assertAlmostEqual(ox + (east - b[0]) * factor * scale, rect[0] + rect[2])
            self.assertAlmostEqual(oy + (b[3] - north) * scale, rect[1])
            self.assertAlmostEqual(oy + (b[3] - south) * scale, rect[1] + rect[3])
            path = make_context_path(box(west, south, east, north), b, 0, rect)
            self.assertIn(f'{rect[0]:.1f},{rect[1]:.1f}', path)
            self.assertIn(f'{rect[0] + rect[2]:.1f},{rect[1] + rect[3]:.1f}', path)

    def test_alaska_wrapped_longitudes_resolve_real_land(self):
        region = REGIONS[1]
        bounds = tuple(region['bounds'][key] for key in ('west', 'south', 'east', 'north'))
        rect = tuple(region['rect'][key] for key in ('x', 'y', 'width', 'height'))
        coast = context_geometry(canvas_bounds(bounds, rect), 'i')
        self.assertIsNotNone(coast)
        self.assertTrue(coast.is_valid)
        self.assertTrue(coast.contains(Point(-150, 64)))

    def test_mismatch_and_overlap_fail_closed(self):
        source = BEGIN.format('multi-region-local-equirectangular-fit-v1')
        source += '<g data-map-region="alaska"><path d="M1 1L2 2Z" fill="url(#land)"/></g>' + END
        with self.assertRaisesRegex(ValueError, 'must match JSON'):
            add_context(source, US, {'alaska': ''}, 'i', REGIONS)
        other = {'id': 'other', 'bounds': REGIONS[0]['bounds'], 'rect': REGIONS[0]['rect']}
        source = source.replace('alaska', 'lower48').replace(END, '<g data-map-region="other"><path d="M1 1L2 2Z" fill="url(#land)"/></g>' + END)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            add_context(source, US, {'lower48': '', 'other': ''}, 'i', [REGIONS[0], other])
        with self.assertRaisesRegex(ValueError, 'must match all'):
            add_context(source, US, {'lower48': ''}, 'i', [REGIONS[0], {**REGIONS[1], 'id': 'other'}])


if __name__ == '__main__':
    unittest.main()
