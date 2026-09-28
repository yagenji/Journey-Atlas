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
        self.assertEqual(hashlib.sha256(rendered).hexdigest(),
                         'bf26342c6bcb7aa60312efe4997c1e6c9eaf31d4db930abbdcc15f77c4941ea3')
        context = next(g for g in final.iter(SVG+'g') if g.get('id')=='geographic-context')
        parts = [p for p in context.iter(SVG+'path') if p.get('data-map-context-region')]
        self.assertEqual([(p.get('data-map-context-region'),p.get('d')) for p in parts], [('mainland',pinned)])
        note = ''.join(context.itertext())
        self.assertIn('01ec685ca5739b63292e01380ff36287413508b5',note)
        self.assertIn('ce02dabb0ea17eba11923f78ed1525d8989c9b58',note)
        frames = [r.get('data-map-context-frame') for r in final.iter(SVG+'rect')
                  if r.get('data-map-context-frame')]
        self.assertEqual(frames, ['mainland', 'azores', 'madeira'])

    def test_bahrain_western_land_is_connected_to_saudi_mainland(self):
        with tempfile.TemporaryDirectory() as temp:
            config, final, _ = generate('bahrain',Path(temp))
        original = ET.parse(ROOT/config['map']['svg']).getroot()
        self.assertEqual([dict(p.attrib) for p in original.iter(SVG+'path') if p.get('fill')=='url(#land)'],
                         [dict(p.attrib) for p in final.iter(SVG+'path') if p.get('fill')=='url(#land)'])
        main = next(r for r in config['map']['regions'] if r['id']=='main')
        bounds = tuple(main['bounds'][k] for k in ('west','south','east','north'))
        rect = tuple(main['rect'][k] for k in ('x','y','width','height'))
        canvas = core.canvas_bounds(bounds,rect)
        self.assertAlmostEqual(canvas[0],50.16066598094097,places=7)
        context = next(p.get('d') for p in final.iter(SVG+'path') if p.get('data-map-context-legacy')=='main')
        rings = []
        for chunk in re.split(r'(?=\bM\s)',context):
            pairs = [tuple(map(float,p)) for p in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',chunk)]
            if len(pairs)>=3:
                rings.append(Polygon(pairs))
        wedge = next((p for p in rings if p.bounds[0]==10 and p.bounds[2]<100 and p.area>15000),None)
        self.assertIsNotNone(wedge,'West-side Saudi source land disappeared or changed')
        factor,scale,ox,oy=core.frame(bounds,rect)
        west,south,east,north=bounds
        candidate_geo=transform(lambda x,y,z=None:(west+(x-ox)/(factor*scale),north-(y-oy)/scale),wedge)
        # Query a substantially wider, independent source extent.  Never infer a
        # coast from the rectangular clipping edge of the local 1200px viewport.
        mapdata=Basemap(projection='cyl',llcrnrlon=49.5,llcrnrlat=25.5,
                        urcrnrlon=51,urcrnrlat=26.9,resolution='i',area_thresh=0.1)
        mainland = [Polygon(zip(xs,ys)) for (xs,ys),level in zip(mapdata.coastpolygons,mapdata.coastpolygontypes)
                    if level==1 and len(xs)>=3]
        source=next((p for p in mainland if p.covers(Point(50.2,26.2))),None)
        self.assertIsNotNone(source)
        self.assertTrue(source.covers(Point(49.7,26.2)), 'The west wedge must connect to Saudi mainland outside viewport')
        self.assertLess(candidate_geo.difference(source).area,0.00001)
        self.assertGreater(candidate_geo.area,0.008)
        self.assertLess(candidate_geo.area,0.009)


if __name__=='__main__':unittest.main()
