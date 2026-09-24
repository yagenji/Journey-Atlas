#!/usr/bin/env python3
"""Regression guards for Timor-Leste source-aligned Indonesian context."""
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

from reconcile_timorleste_foreign import (  # noqa: E402
    CLIP_ID,
    EXPECTED_BOUNDS,
    FIXTURE_GIT_BLOB,
    SOURCE_COMMIT,
    SOURCE_COMPONENTS,
    SOURCE_GIT_BLOB,
    git_blob_sha,
    reconcile,
)

SVG = '{http://www.w3.org/2000/svg}'


class TimorLesteContextSourceTest(unittest.TestCase):
    def setUp(self):
        self.country_file = ROOT / 'data/countries/timorleste.json'
        self.country = json.loads(self.country_file.read_text(encoding='utf-8'))
        self.source = ROOT / self.country['map']['svg']
        self.fixture = ROOT / 'ops/map-context-sources/timorleste/indonesia-ne10m-v4.1.0.geojson'
        self.target_sibling = ROOT / 'ops/map-context-sources/timorleste/timorleste-ne10m-v4.1.0.geojson'

    def test_pinned_source_and_exact_target_exclusion(self):
        self.assertEqual(self.country['map']['bounds'], EXPECTED_BOUNDS)
        self.assertIn('Natural Earth 1:10m', self.country['map']['source'])
        self.assertEqual(git_blob_sha(self.fixture.read_bytes()), FIXTURE_GIT_BLOB)

        payload = json.loads(self.fixture.read_text(encoding='utf-8'))
        props = payload['properties']
        self.assertEqual(props['sourceCommit'], SOURCE_COMMIT)
        self.assertEqual(props['naturalEarthVersion'], '4.1.0')
        self.assertEqual(props['sourceComponentIndices'], SOURCE_COMPONENTS)
        self.assertEqual(props['license'], 'Natural Earth public domain')
        self.assertEqual(payload['geometry']['type'], 'MultiPolygon')
        self.assertEqual(len(payload['geometry']['coordinates']), 5)
        self.assertEqual(git_blob_sha(self.target_sibling.read_bytes()),
                         '1c529b951e6d5c5af2a2ef3bbaaf2da0b3239719')

        sibling = json.loads(self.target_sibling.read_text(encoding='utf-8'))
        idn_segments = set()
        for polygon in payload['geometry']['coordinates']:
            for ring in polygon:
                for a, b in zip(ring, ring[1:]):
                    idn_segments.add((tuple(a), tuple(b)))
                    idn_segments.add((tuple(b), tuple(a)))
        shared = 0
        for polygon in sibling['geometry']['coordinates']:
            for ring in polygon:
                for a, b in zip(ring, ring[1:]):
                    if (tuple(a), tuple(b)) in idn_segments:
                        shared += 1
        self.assertEqual(shared, 101)

        source_text = self.source.read_text(encoding='utf-8')
        before = ET.fromstring(source_text)
        protected_before = [
            path.get('d') for path in before.iter(SVG + 'path')
            if path.get('fill') == 'url(#land)'
        ]
        self.assertEqual(len(protected_before), 1)

        if ('id="geographic-context"' in source_text
                and f'id="{CLIP_ID}"' in source_text):
            result = source_text
        else:
            result = reconcile(source_text, self.source, self.country_file, self.fixture, 'i')
        after = ET.fromstring(result)
        protected_after = [
            path.get('d') for path in after.iter(SVG + 'path')
            if path.get('fill') == 'url(#land)'
        ]
        self.assertEqual(protected_after, protected_before)

        context = after.find(".//*[@id='geographic-context']")
        self.assertIsNotNone(context)
        self.assertEqual(context.get('clip-path'), f'url(#{CLIP_ID})')
        context_paths = list(context.iter(SVG + 'path'))
        self.assertEqual(len(context_paths), 1)
        self.assertTrue(context_paths[0].get('d'))

        clip = after.find(f".//*[@id='{CLIP_ID}']")
        self.assertIsNotNone(clip)
        clip_paths = list(clip.iter(SVG + 'path'))
        self.assertEqual(len(clip_paths), 1)
        self.assertEqual(clip_paths[0].get('clip-rule'), 'evenodd')
        self.assertEqual(clip_paths[0].get('fill-rule'), 'evenodd')
        self.assertIn(protected_before[0], clip_paths[0].get('d', ''))

        for color in ('#eaf2f4', '#dcebf0', '#d0e3eb'):
            self.assertIn(color, result)
        self.assertIn('Natural Earth 1:10m v4.1.0', result)
        self.assertIn(SOURCE_COMMIT, result)

        with Image.open(BytesIO(cairosvg.svg2png(
            bytestring=result.encode('utf-8'), output_width=1200, output_height=760
        ))) as png:
            png.load()
            self.assertEqual(png.size, (1200, 760))


if __name__ == '__main__':
    unittest.main()
