"""Source-pinned El Salvador island correction and staged foreign context."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from reconcile_elsalvador_foreign import reconcile

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'


def rings(path):
    return [Polygon([(float(x), float(y)) for x, y in
                     re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', part)])
            for part in re.findall(r'M\s*([^M]+)', path.get('d', ''))]


class ElSalvadorSourceReview(unittest.TestCase):
    def test_restored_islands_and_foreign_context_preserve_original_target(self):
        config = json.loads((ROOT/'data/countries/elsalvador.json').read_text(encoding='utf-8'))
        approved = ROOT/config['map']['svg']
        self.assertEqual(hashlib.sha256(approved.read_bytes()).hexdigest(),
                         '28290dca64d3f04a3bc25e5ef1ac7f871d295eb239d21e8b4baf4fcb9eae44dc')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'elsalvador.svg'
            subprocess.run([sys.executable, str(ROOT/'scripts/add_country_map_context_existing.py'),
                            '--country-json', str(ROOT/'data/countries/elsalvador.json'),
                            '--input', str(approved), '--output', str(output), '--resolution', 'i'],
                           cwd=ROOT, check=True, capture_output=True, timeout=180)
            raw = output.read_text(encoding='utf-8')
            rendered = reconcile(raw, approved).encode('utf-8')
        self.assertEqual(hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                         'f6db6273cb5dd97de10ab783e8f415d3552da6035f8cc98c907d66d505ad223f')
        self.assertEqual(hashlib.sha256(rendered).hexdigest(),
                         'ef2df0aba46eb8049f04a02714b2f44b22394fdeecf235c2ea4ec6cf99cdaa53')
        source = ET.parse(approved).getroot()
        candidate = ET.fromstring(rendered)
        self.assertEqual(candidate.get('viewBox'), '0 0 1200 760')
        original_targets = [dict(p.attrib) for p in source.iter(SVG+'path')
                            if p.get('fill') == 'url(#land)']
        candidate_targets = [dict(p.attrib) for p in candidate.iter(SVG+'path')
                             if p.get('fill') == 'url(#land)']
        self.assertEqual(len(original_targets), 2)
        self.assertEqual(candidate_targets, original_targets)
        self.assertEqual(hashlib.sha256(original_targets[0]['d'].encode()).hexdigest(),
                         '8bb899b75af9b1563788a8ee25acfd685ff5d972133a5f3fcd1eeffe7eb4fab8')
        self.assertEqual(hashlib.sha256(original_targets[1]['d'].encode()).hexdigest(),
                         '76e90ff71a8128eef75d6b43c31a8e4735b702f95f146472794a419d6c25e0f6')
        pale = candidate.find(f".//{SVG}g[@id='geographic-context']/{SVG}path")
        self.assertIsNotNone(pale)
        context_rings = rings(pale)
        self.assertEqual(len(context_rings), 13)
        target_rings = [r for p in candidate.iter(SVG+'path')
                        if p.get('fill') == 'url(#land)' for r in rings(p)]
        self.assertEqual(len(target_rings), 10)
        # Formerly omitted islands are now protected target, not foreign land.
        for x, y in [(807.8, 635.8), (713.2, 630.8)]:
            point = Point(x, y)
            self.assertTrue(any(r.covers(point) for r in target_rings), (x, y))
            self.assertFalse(any(r.covers(point) for r in context_rings), (x, y))
        # Source-backed Honduras/Nicaragua Gulf rings remain in pale context.
        for x, y in [(1199.1, 758.3), (1198.0, 623.0),
                     (1189.1, 598.1), (1198.0, 584.5)]:
            point = Point(x, y)
            self.assertTrue(any(r.covers(point) for r in context_rings), (x, y))
            self.assertFalse(any(r.covers(point) for r in target_rings), (x, y))


if __name__ == '__main__':
    unittest.main()
