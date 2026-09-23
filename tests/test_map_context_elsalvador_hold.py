"""El Salvador triage regression, not geographic approval.

The current generator puts several genuine Salvadoran islands into the pale
context while the approved target has no matching paths. Keep this candidate
on Stage 2 HOLD; do not silently erase islands or recolor protected geometry.
"""
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

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'


def rings(path):
    return [Polygon([(float(x), float(y)) for x, y in
                     re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', part)])
            for part in re.findall(r'M\s*([^M]+)', path.get('d', ''))]


class ElSalvadorHold(unittest.TestCase):
    def test_self_islands_in_pale_context_are_not_mistaken_for_foreign_land(self):
        config = json.loads((ROOT/'data/countries/elsalvador.json').read_text(encoding='utf-8'))
        approved = ROOT/config['map']['svg']
        self.assertEqual(hashlib.sha256(approved.read_bytes()).hexdigest(),
                         '37122f7a87b53c53bf651b1d281ffdf8b87114c7d34e4188d51a8a0f9b79f4cb')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'elsalvador.svg'
            subprocess.run([sys.executable, str(ROOT/'scripts/add_country_map_context_existing.py'),
                            '--country-json', str(ROOT/'data/countries/elsalvador.json'),
                            '--input', str(approved), '--output', str(output), '--resolution', 'i'],
                           cwd=ROOT, check=True, capture_output=True, timeout=180)
            rendered = output.read_bytes()
        self.assertEqual(hashlib.sha256(rendered).hexdigest(),
                         '29118519d584d2d36ce465ff0d896231b6cc7be77dd145ee99f16a4458029ea1')
        source = ET.parse(approved).getroot()
        candidate = ET.fromstring(rendered)
        self.assertEqual(candidate.get('viewBox'), '0 0 1200 760')
        original_targets = [dict(p.attrib) for p in source.iter(SVG+'path')
                            if p.get('fill') == 'url(#land)']
        candidate_targets = [dict(p.attrib) for p in candidate.iter(SVG+'path')
                             if p.get('fill') == 'url(#land)']
        self.assertEqual(len(original_targets), 1)
        self.assertEqual(candidate_targets, original_targets)
        pale = candidate.find(f".//{SVG}g[@id='geographic-context']/{SVG}path")
        self.assertIsNotNone(pale)
        context_rings = rings(pale)
        self.assertEqual(len(context_rings), 22)
        target_rings = rings(next(p for p in candidate.iter(SVG+'path')
                                  if p.get('fill') == 'url(#land)'))
        # Two detached pale rings overlap the independent Natural Earth 4.1.0
        # SLV ADM0 polygon by 100%, yet have no approved target island path.
        # The test locks the observable rendering, not a sovereignty finding.
        for x, y in [(807.8, 635.8), (713.2, 630.8)]:
            point = Point(x, y)
            self.assertTrue(any(r.covers(point) for r in context_rings), (x, y))
            self.assertFalse(any(r.covers(point) for r in target_rings), (x, y))
        # Two Gulf islands ARE in the approved target but their GSHHG context
        # rings protrude beyond those protected silhouettes (87.2%, 94.0%
        # target overlap). This requires a source-matched context repair.
        for i, expected in [(16, 0.872), (17, 0.940)]:
            fraction = sum(context_rings[i].intersection(t).area for t in target_rings)
            fraction /= context_rings[i].area
            self.assertAlmostEqual(fraction, expected, delta=0.002)


if __name__ == '__main__':
    unittest.main()
