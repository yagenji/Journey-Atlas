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
    root = ET.fromstring(source)
    existing = root.find('.//*[@id="geographic-context"]')
    if existing is not None and any(
            (path.get('d') or '').strip() for path in existing.iter(SVG + 'path')):
        return source
    geometry = maps.context_geometry(maps.canvas_bounds(bounds), 'i')
    context = maps.make_context_path(geometry, bounds, 0.003)
    return maps.add_context(source, bounds, context, 'i')


def target_paths(svg):
    return [ET.tostring(path) for path in ET.fromstring(svg).iter(SVG + 'path')
            if path.get('fill') == 'url(#land)']


class IsolatedSelfLandTest(unittest.TestCase):
    def test_cyprus_compound_self_island_has_no_fake_neighbor_halo(self):
        data = json.loads((ROOT / 'data/countries/cyprus.json').read_text(encoding='utf-8'))
        self.assertEqual(data['map']['bounds'], {
            'north': 35.836, 'south': 34.422, 'west': 32.07025, 'east': 34.79973,
        })
        self.assertIn('dtrihinas/cyprus-geojson', data['map']['source'])

        original = preview('cyprus')
        result, removed = remove_target_land_context(original)
        self.assertEqual(removed, 4)
        self.assertEqual(target_paths(original), target_paths(result))
        self.assertEqual(len(target_paths(result)), 1)
        original_context = ET.fromstring(original).find('.//*[@id="geographic-context"]')
        filtered_context = ET.fromstring(result).find('.//*[@id="geographic-context"]')
        self.assertTrue(original_context[0].get('d'))
        self.assertEqual(filtered_context[0].get('d'), '')
        for color in ('#eaf2f4', '#dcebf0', '#d0e3eb'):
            self.assertIn(color, result)
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

    def test_malta_has_only_domestic_context_components(self):
        data = json.loads((ROOT / 'data/countries/malta.json').read_text(encoding='utf-8'))
        bounds = tuple(float(data['map']['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
        geometry = maps.context_geometry(maps.canvas_bounds(bounds), 'i')
        parts = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)

        self.assertEqual(len(parts), 3)
        centroids = sorted((round(part.centroid.x, 3), round(part.centroid.y, 3)) for part in parts)
        self.assertEqual(centroids, [(14.252, 36.046), (14.333, 36.011), (14.438, 35.89)])

        current = (ROOT / data['map']['svg']).read_text(encoding='utf-8')
        root = ET.fromstring(current)
        context = root.find('.//*[@id="geographic-context"]')
        self.assertIsNotNone(context)
        self.assertEqual(list(context.iter(SVG + 'path')), [])
        self.assertIn('#eaf2f4', current)
        self.assertIn('#dcebf0', current)
        self.assertIn('#d0e3eb', current)

    def test_landlocked_microstates_have_full_land_context(self):
        for slug in ('andorra', 'liechtenstein', 'sanmarino', 'vaticancity'):
            with self.subTest(slug=slug):
                data = json.loads((ROOT / 'data/countries' / f'{slug}.json').read_text(encoding='utf-8'))
                bounds = tuple(float(data['map']['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
                canvas = maps.canvas_bounds(bounds)
                geometry = maps.context_geometry(canvas, 'i')

                self.assertEqual(geometry.geom_type, 'Polygon')
                self.assertEqual(len(geometry.interiors), 0)
                for actual, expected in zip(geometry.bounds, canvas):
                    self.assertAlmostEqual(actual, expected, places=12)
                expected_area = (canvas[2] - canvas[0]) * (canvas[3] - canvas[1])
                self.assertAlmostEqual(geometry.area, expected_area, places=12)

                current = (ROOT / data['map']['svg']).read_text(encoding='utf-8')
                context = ET.fromstring(current).find('.//*[@id="geographic-context"]')
                self.assertIsNotNone(context)
                context_paths = list(context.iter(SVG + 'path'))
                self.assertEqual(len(context_paths), 1)
                d = context_paths[0].get('d', '')
                self.assertIn('1200.0,0.0', d)
                self.assertIn('1200.0,760.0', d)
                self.assertIn('760.0', d)

    def test_luxembourg_viewport_is_continuous_surrounding_land(self):
        data = json.loads((ROOT / 'data/countries/luxembourg.json').read_text(encoding='utf-8'))
        self.assertEqual(data['map']['bounds'], {
            'north': 50.18, 'south': 49.38, 'west': 5.55, 'east': 6.55,
        })
        self.assertIn('Natural Earth 1:10m', data['map']['source'])
        bounds = tuple(float(data['map']['bounds'][key]) for key in ('west', 'south', 'east', 'north'))
        canvas = maps.canvas_bounds(bounds)
        geometry = maps.context_geometry(canvas, 'i')

        self.assertEqual(geometry.geom_type, 'Polygon')
        self.assertEqual(len(geometry.interiors), 0)
        for actual, expected in zip(geometry.bounds, canvas):
            self.assertAlmostEqual(actual, expected, places=12)
        expected_area = (canvas[2] - canvas[0]) * (canvas[3] - canvas[1])
        self.assertAlmostEqual(geometry.area, expected_area, places=12)

        source = (ROOT / data['map']['svg']).read_text(encoding='utf-8')
        result = preview('luxembourg')
        self.assertEqual(target_paths(source), target_paths(result))
        self.assertEqual(len(target_paths(result)), 1)
        context = ET.fromstring(result).find('.//*[@id="geographic-context"]')
        self.assertIsNotNone(context)
        paths = list(context.iter(SVG + 'path'))
        self.assertEqual(len(paths), 1)
        d = paths[0].get('d', '')
        self.assertIn('1200.0,0.0', d)
        self.assertIn('1200.0,760.0', d)
        self.assertIn('-0.0,760.0', d)
        with Image.open(BytesIO(cairosvg.svg2png(
            bytestring=result.encode(), output_width=1200, output_height=760
        ))) as png:
            png.load()
            self.assertEqual(png.size, (1200, 760))

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
