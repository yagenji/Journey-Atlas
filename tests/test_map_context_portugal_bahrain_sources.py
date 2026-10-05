"""Focused geographic-source regressions for existing-map migration only.

These tests check source identity/topology, NOT approval for the full 109-map rollout.
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

from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, box
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_country_map_context as core

SVG = '{http://www.w3.org/2000/svg}'


def generate(slug, folder):
    config = json.loads((ROOT / 'data/countries' / (slug+'.json')).read_text(encoding='utf-8'))
    source = ROOT / config['map']['svg']
    target = folder / (slug+'.svg')
    source_text = source.read_text(encoding='utf-8')
    if ('id="geographic-context"' in source_text and
            all(color in source_text for color in ('#eaf2f4', '#dcebf0', '#d0e3eb'))):
        target.write_bytes(source.read_bytes())
    else:
        subprocess.run([sys.executable, str(ROOT / 'scripts/add_country_map_context_existing.py'),
                        '--country-json', str(ROOT/'data/countries'/(slug+'.json')),
                        '--input', str(source), '--output', str(target),
                        '--resolution', 'i'], cwd=ROOT, check=True, timeout=180)
    return config, ET.parse(target).getroot(), target.read_bytes()


class GeographicSourceRegressions(unittest.TestCase):
    def test_portugal_uses_source_matched_spain_and_keeps_all_targets(self):
        pinned = (ROOT/'ops/map-context-sources/portugal/spain-natural-earth-mainland-context.path').read_text(encoding='utf-8').rstrip('\n')
        self.assertEqual(hashlib.sha256(pinned.encode()).hexdigest(),
                         '2c475f224a4bea0b3c83deacc006edf6a121b8e896badd2b10dcfb91f09e7356')
        with tempfile.TemporaryDirectory() as temp:
            config, final, rendered = generate('portugal',Path(temp))
        source = ET.parse(ROOT/config['map']['svg']).getroot()
        original = [dict(p.attrib) for p in source.iter(SVG+'path') if p.get('fill') == 'url(#land)']
        targets = [dict(p.attrib) for p in final.iter(SVG+'path') if p.get('fill') == 'url(#land)']
        self.assertEqual(len(targets), 15)
        self.assertEqual(targets, original)
        self.assertEqual(final.get('viewBox'), '0 0 1200 760')
        # 2026-10-06: inset frames in the shared style (no reduced opacity)
        self.assertEqual(hashlib.sha256(rendered).hexdigest(),
                         '10bfa63aac9058edfeebb028e6c1cf1a12ce99abd07c164d901bd4dca615430b')
        context = next(g for g in final.iter(SVG+'g') if g.get('id')=='geographic-context')
        parts = [p for p in context.iter(SVG+'path') if p.get('data-map-context-region')]
        self.assertEqual([(p.get('data-map-context-region'),p.get('d')) for p in parts], [('mainland',pinned)])
        note = ''.join(context.itertext())
        self.assertIn('01ec685ca5739b63292e01380ff36287413508b5',note)
        self.assertIn('ce02dabb0ea17eba11923f78ed1525d8989c9b58',note)
        frames = [r.get('data-map-context-frame') for r in final.iter(SVG+'rect')
                  if r.get('data-map-context-frame')]
        self.assertEqual(frames, ['mainland', 'azores', 'madeira'])

    def test_bahrain_main_view_matches_marker_projection(self):
        """The main view is drawn exactly as app.js projects markers (2026-10-06).

        The earlier main view was stretched about 2.4x horizontally, so markers
        fell away from their places. Every main-region Scene must now sit on
        Bahrain land at its real coordinates, and Saudi land stays in view west
        of Umm Nasan.
        """
        import normalize_country_map_lakes as lakes
        config = json.loads((ROOT/'data/countries/bahrain.json').read_text(encoding='utf-8'))
        root = ET.parse(ROOT/config['map']['svg']).getroot()
        main_group = next(g for g in root.iter(SVG+'g') if g.get('data-map-region') == 'main')
        target = lakes._target_geometry(main_group)
        main = next(r for r in config['map']['regions'] if r['id'] == 'main')
        bounds = tuple(main['bounds'][k] for k in ('west','south','east','north'))
        rect = tuple(main['rect'][k] for k in ('x','y','width','height'))
        factor, scale, ox, oy = core.frame(bounds, rect)
        west, south, east, north = bounds
        checked = 0
        for scene in config['scenes']:
            if scene.get('mapRegion') != 'main':
                continue
            c = scene['coordinates']
            point = Point(ox + (c['longitude'] - west) * factor * scale, oy + (north - c['latitude']) * scale)
            with self.subTest(scene=scene['id']):
                self.assertLess(target.distance(point), 3.0)
            checked += 1
        self.assertGreaterEqual(checked, 6)
        context = next(g for g in main_group.iter(SVG+'g') if g.get('id') == 'geographic-context')
        saudi = Point(ox + (50.157 - west) * factor * scale, oy + (north - 26.119) * scale)  # Al Khobar coast
        rings = [Polygon(pairs) for d in (p.get('d') for p in context.iter(SVG+'path'))
                 for chunk in re.split(r'(?=M)', d)
                 for pairs in [[tuple(map(float, xy)) for xy in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', chunk)]]
                 if len(pairs) >= 3]
        self.assertTrue(any(r.buffer(0).covers(saudi) for r in rings), 'Saudi land west of Bahrain must stay in view')

if __name__=='__main__':unittest.main()
