"""Review-only source/topology tests for existing approved Country maps.

No production SVG substitution or blanket geographic QA approval.
"""
from __future__ import annotations
import json
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.affinity import affine_transform
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/journey-atlas-map-context-real-previews/priority-review')
sys.path.insert(0,str(ROOT/'scripts'))
import add_country_map_context_existing as existing
import add_country_map_context_legacy as legacy

SVG='{http://www.w3.org/2000/svg}'
POINT=re.compile(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)')


def rings(d, *, permit_approved_self_intersection=False):
    """Read existing M/L/Z paths, without altering any approved SVG bytes."""
    parts=re.findall(r'M\s*[^M]+',d)
    result=[]
    for part in parts:
        coords=[(float(x),float(y)) for x,y in POINT.findall(part)]
        if len(coords)<4 or not part.strip().endswith('Z'):
            raise ValueError('Unreviewed country SVG path syntax')
        poly=Polygon(coords)
        if not poly.is_valid:
            if not permit_approved_self_intersection:
                raise ValueError('Invalid foreign/source ring: independent review required')
            # Approved Hawar source contains an unmodified self-intersecting ring.
            # Repair the temporary measurement geometry only; never write it to SVG.
            poly=poly.buffer(0)
        result.append(poly)
    return result


def frame(bounds,rect):
    west,south,east,north=(bounds[k] for k in ('west','south','east','north'))
    x,y,width,height=(rect[k] for k in ('x','y','width','height'))
    factor=math.cos(math.radians((south+north)/2))
    scale=min(width/((east-west)*factor),height/(north-south))
    return factor,scale,x+(width-(east-west)*factor*scale)/2,y+(height-(north-south)*scale)/2


class PriorityGeographyReview(unittest.TestCase):
    def _run(self,slug,script):
        folder=OUT/slug
        folder.mkdir(parents=True,exist_ok=True)
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),
                        '--repo',str(ROOT),'--output-dir',str(folder)],
                       cwd=ROOT,check=True,timeout=240)
        report=json.loads((folder/'report.json').read_text())
        self.assertIn('HOLD', report['status'])
        self.assertTrue((folder/(slug+'-reviewed.png' if slug=='brunei' else 'monaco-current.png')).is_file())
        return report

    def test_bahrain_hawar_foreign_land_matches_approved_qatar(self):
        """Independently compare retained Hawar context to Qatar's national SVG.

        Small residual is source-vintage/simplification, not permission to
        stretch approved Bahrain or Qatar coastlines for cosmetic continuity.
        """
        config=json.loads((ROOT/'data/countries/bahrain.json').read_text())
        qatar_config=json.loads((ROOT/'data/countries/qatar.json').read_text())
        source=(ROOT/config['map']['svg']).read_text()
        qatar=(ROOT/qatar_config['map']['svg']).read_text()
        raw=legacy._loose_multi_region(source,config,'i')
        reviewed=existing.reconcile_reviewed_bahrain_hawar(raw,'i')
        before=ET.fromstring(source)
        after=ET.fromstring(reviewed)
        own=lambda root:[dict(node.attrib) for node in root.iter(SVG+'path')
                         if node.get('fill')=='url(#land)']
        self.assertEqual(own(before),own(after))
        self.assertEqual(after.get('viewBox'),'0 0 1200 760')
        hawar=[node for node in after.iter(SVG+'path')
               if node.get('data-map-context-legacy')=='hawar']
        self.assertEqual(len(hawar),1)
        foreign=rings(hawar[0].get('d'))
        self.assertEqual(len(foreign),2)
        qatar_root=ET.fromstring(qatar)
        qatar_paths=[p for p in qatar_root.iter(SVG+'path') if p.get('fill')=='url(#land)']
        self.assertEqual(len(qatar_paths),2)
        qatar_national=rings(qatar_paths[0].get('d'))
        self.assertEqual(len(qatar_national),1)
        qf,qs,qx,qy=frame(qatar_config['map']['bounds'],
                           {'x':0,'y':0,'width':1200,'height':760})
        hawar_region=next(r for r in config['map']['regions'] if r['id']=='hawar')
        hf,hs,hx,hy=frame(hawar_region['bounds'],hawar_region['rect'])
        a=hf*hs/(qf*qs)
        b=hs/qs
        west=qatar_config['map']['bounds']['west']
        north=qatar_config['map']['bounds']['north']
        hw=hawar_region['bounds']['west']
        hn=hawar_region['bounds']['north']
        target=affine_transform(qatar_national[0],
                 [a,0,0,b,hx+(west-hw)*hf*hs-a*qx,hy+(hn-north)*hs-b*qy])
        rect=hawar_region['rect']
        viewport=box(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height'])
        qatar_inset=target.intersection(viewport)
        foreign_union=unary_union(foreign)
        self.assertGreater(qatar_inset.area,3000)
        self.assertTrue(all(p.intersection(qatar_inset).area/p.area>.99 for p in foreign))
        self.assertLess(foreign_union.symmetric_difference(qatar_inset).area,35)
        own_hawar=[p for p in before.iter(SVG+'path') if p.get('fill')=='url(#land)'][1]
        own_rings=rings(own_hawar.get('d'),permit_approved_self_intersection=True)
        self.assertLess(sum(qatar_inset.intersection(poly).area for poly in own_rings),8)

    def test_brunei_malaysia_source_and_original_path(self):
        result=self._run('brunei','review_brunei_malaysia.py')
        self.assertTrue(result['nationalPathsIdentical'])
        self.assertGreater(result['domesticIslandRemovedFromForeignContextSvgPx2'],400)
        self.assertEqual(result['decodedSize'],[1200,760])

    def test_monaco_latest_osm_french_context_and_original_path(self):
        result=self._run('monaco','review_monaco_france.py')
        self.assertEqual(result['protectedPaths'],1)
        self.assertEqual(result['fullRaster'],[1200,760])
        self.assertGreater(result['contextRingCount'],0)


if __name__=='__main__':unittest.main()
