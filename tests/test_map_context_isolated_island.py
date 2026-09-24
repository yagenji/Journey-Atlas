#!/usr/bin/env python3
"""Real-source regression for isolated self-land vs genuine neighboring land."""
import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_country_map_context as maps
import add_country_map_context_legacy as legacy
from filter_duplicate_target_context import remove_target_land_context

SVG = '{http://www.w3.org/2000/svg}'


def preview(slug):
    data = json.loads((ROOT / 'data' / 'countries' / f'{slug}.json').read_text(encoding='utf-8'))
    config = data['map']
    bounds = tuple(float(config['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
    source = (ROOT / config['svg']).read_text(encoding='utf-8')
    geometry = maps.context_geometry(maps.canvas_bounds(bounds), 'i')
    context = maps.make_context_path(geometry, bounds, 0.003)
    return maps.add_context(source, bounds, context, 'i')


def target_paths(svg):
    return [ET.tostring(path) for path in ET.fromstring(svg).iter(SVG + 'path')
            if path.get('fill') == 'url(#land)']


class IsolatedSelfLandTest(unittest.TestCase):
    def test_cyprus_compound_self_island_has_no_fake_neighbor_halo(self):
        original = preview('cyprus')
        result, removed = remove_target_land_context(original)
        self.assertEqual(removed, 4)
        self.assertEqual(target_paths(original), target_paths(result))
        original_context = ET.fromstring(original).find('.//*[@id="geographic-context"]')
        filtered_context = ET.fromstring(result).find('.//*[@id="geographic-context"]')
        self.assertTrue(original_context[0].get('d'))
        self.assertEqual(filtered_context[0].get('d'), '')
        with Image.open(BytesIO(cairosvg.svg2png(bytestring=result.encode(), output_width=1200, output_height=760))) as png:
            png.load()
            self.assertEqual(png.size, (1200, 760))

    def test_antigua_edge_closure_is_not_foreign_land(self):
        data = json.loads((ROOT / 'data/countries/antiguabarbuda.json').read_text(encoding='utf-8'))
        region = next(item for item in data['map']['regions'] if item['id'] == 'antigua')
        bounds = tuple(float(region['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
        rect = tuple(float(region['rect'][key]) for key in ('x', 'y', 'width', 'height'))
        canvas = maps.canvas_bounds(bounds, rect)

        direct = maps.context_geometry(canvas, 'i')
        sampled = legacy._sample_region_beyond_viewport(canvas, 'i')
        direct_parts = [direct] if direct.geom_type == 'Polygon' else list(direct.geoms)
        sampled_parts = [sampled] if sampled.geom_type == 'Polygon' else list(sampled.geoms)

        self.assertEqual(len(direct_parts), 2)
        edge_fragment = min(direct_parts, key=lambda part: part.area)
        self.assertLess(edge_fragment.area, 0.00001)
        self.assertAlmostEqual(edge_fragment.bounds[2], canvas[2], places=9)
        self.assertEqual(len(sampled_parts), 1)
        self.assertAlmostEqual(sampled_parts[0].area, max(part.area for part in direct_parts), places=12)

        current = (ROOT / data['map']['svg']).read_text(encoding='utf-8')
        context = ET.fromstring(current).find('.//*[@id="geographic-context"]')
        self.assertIsNotNone(context)
        self.assertEqual(list(context.iter(SVG + 'path')), [])

    def test_timor_shared_island_keeps_real_neighbor(self):
        original = preview('timorleste')
        result, _ = remove_target_land_context(original)
        self.assertEqual(target_paths(original), target_paths(result))
        context = ET.fromstring(result).find('.//*[@id="geographic-context"]')
        self.assertTrue(any(path.get('d') for path in context.iter(SVG + 'path')))
        with Image.open(BytesIO(cairosvg.svg2png(bytestring=result.encode(), output_width=1200, output_height=760))) as png:
            png.load()
            self.assertEqual(png.size, (1200, 760))


if __name__ == '__main__':
    unittest.main()
