#!/usr/bin/env python3
"""Source/topology guards for reviewed landlocked Country map-context candidates."""
import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import add_country_map_context as maps  # noqa: E402
from filter_duplicate_target_context import remove_target_land_context  # noqa: E402

SVG = '{http://www.w3.org/2000/svg}'

CASES = {
    'czechia': {
        'source_text': 'Natural Earth 1:10m',
        'min_land_fraction': 0.999,
        'exact_exterior': True,
    },
    'hungary': {
        'source_text': 'Natural Earth 1:10m',
        'min_land_fraction': 0.996,
    },
    'tajikistan': {
        'source_text': 'Basemap intermediate-resolution political boundary',
        'min_land_fraction': 0.996,
        'exact_exterior': True,
    },
    'austria': {
        'source_text': 'Natural Earth 1:10m',
        'min_land_fraction': 0.994,
    },
    'serbia': {
        'source_text': 'Natural Earth 1:10m',
        'min_land_fraction': 0.93,
        'major_water_bounds': (16.09, 42.01, 19.16, 43.56),
    },
    'switzerland': {
        'source_text': 'swisstopo swissBOUNDARIES3D',
        'min_land_fraction': 0.978,
    },
    'bhutan': {
        'source_text': 'Natural Earth 1:10m',
        'min_land_fraction': 0.998,
    },
    'nepal': {
        'source_text': 'Basemap countries_i.dat',
        'min_land_fraction': 0.995,
    },
    'kyrgyz': {
        'source_text': 'Basemap intermediate-resolution political-boundary',
        'min_land_fraction': 0.984,
    },
}

SOURCE_ONLY_CASES = {
    # Mongolia's very wide intermediate-resolution Basemap extraction is already
    # covered by the full inventory workflow; keep the approved source pinned
    # here without duplicating that expensive extraction in the unit suite.
    'mongolia': {
        'source_text': 'Natural Earth 1:10m',
    },
}


def target_paths(svg: str):
    return [
        ET.tostring(path, encoding='unicode')
        for path in ET.fromstring(svg).iter(SVG + 'path')
        if path.get('fill') == 'url(#land)'
    ]


class LandlockedContextSourceTest(unittest.TestCase):
    def test_reviewed_landlocked_context_preserves_source_topology(self):
        for slug, expected in CASES.items():
            with self.subTest(slug=slug):
                country_file = ROOT / 'data/countries' / f'{slug}.json'
                country = json.loads(country_file.read_text(encoding='utf-8'))
                config = country['map']
                source_path = ROOT / config['svg']
                source = source_path.read_text(encoding='utf-8')

                self.assertIn(expected['source_text'], config['source'])

                bounds = tuple(float(config['bounds'][k]) for k in ('west', 'south', 'east', 'north'))
                canvas = maps.canvas_bounds(bounds)
                geometry = maps.context_geometry(canvas, 'i')
                self.assertIsNotNone(geometry)
                self.assertIn(geometry.geom_type, ('Polygon', 'MultiPolygon'))

                # Independent source review establishes these countries as
                # landlocked. GSHHG may still represent inland lakes, islands
                # inside lakes, or water touching a viewport edge, so requiring
                # one perfect rectangle would incorrectly reject valid inland
                # topology. Instead pin that land spans all viewport bounds and
                # remains the dominant physical surface at the reviewed scale.
                viewport = box(*canvas)
                self.assertAlmostEqual(geometry.bounds[0], canvas[0], places=10)
                self.assertAlmostEqual(geometry.bounds[1], canvas[1], places=10)
                self.assertAlmostEqual(geometry.bounds[2], canvas[2], places=10)
                self.assertAlmostEqual(geometry.bounds[3], canvas[3], places=10)
                self.assertGreater(
                    geometry.area / viewport.area,
                    expected['min_land_fraction'],
                )
                if expected.get('exact_exterior'):
                    polygons = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
                    exterior = max(polygons, key=lambda polygon: polygon.area).exterior
                    self.assertLess(
                        Polygon(exterior).symmetric_difference(viewport).area,
                        1e-12,
                    )
                if expected.get('major_water_bounds'):
                    water = viewport.difference(geometry)
                    components = list(water.geoms) if water.geom_type.startswith('Multi') else [water]
                    major = max(components, key=lambda component: component.area)
                    for actual, expected_bound in zip(major.bounds, expected['major_water_bounds']):
                        self.assertLess(abs(actual - expected_bound), 0.02)

                source_root = ET.fromstring(source)
                existing = source_root.find(".//*[@id='geographic-context']")
                if existing is not None and all(
                        color in source for color in ('#eaf2f4', '#dcebf0', '#d0e3eb')):
                    filtered = source
                else:
                    context_path = maps.make_context_path(geometry, bounds, 0.003)
                    preview = maps.add_context(source, bounds, context_path, 'i')
                    filtered, _ = remove_target_land_context(preview)

                self.assertEqual(target_paths(filtered), target_paths(source))
                context = ET.fromstring(filtered).find(".//*[@id='geographic-context']")
                self.assertIsNotNone(context)
                self.assertTrue(any(path.get('d') for path in context.iter(SVG + 'path')))
                for color in ('#eaf2f4', '#dcebf0', '#d0e3eb'):
                    self.assertIn(color, filtered)

                with Image.open(BytesIO(cairosvg.svg2png(
                    bytestring=filtered.encode('utf-8'), output_width=1200, output_height=760
                ))) as png:
                    png.load()
                    self.assertEqual(png.size, (1200, 760))

    def test_slow_reviewed_landlocked_sources_stay_pinned(self):
        for slug, expected in SOURCE_ONLY_CASES.items():
            with self.subTest(slug=slug):
                country = json.loads(
                    (ROOT / 'data/countries' / f'{slug}.json').read_text(encoding='utf-8')
                )
                source_path = ROOT / country['map']['svg']
                self.assertIn(expected['source_text'], country['map']['source'])
                source = source_path.read_text(encoding='utf-8')
                self.assertTrue(target_paths(source))
                self.assertEqual(ET.fromstring(source).get('viewBox'), '0 0 1200 760')


if __name__ == '__main__':
    unittest.main()
