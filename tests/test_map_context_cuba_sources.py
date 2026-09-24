#!/usr/bin/env python3
"""Resolve Cuba minor-cay affiliation against pinned Natural Earth 1:10m."""
import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
import numpy as np
from PIL import Image, ImageFilter
from shapely.geometry import box, shape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import add_country_map_context as maps  # noqa: E402

SVG='{http://www.w3.org/2000/svg}'
FIXTURE_BLOB='e48463f4fae8fd6dd7374e818cdb8e6e84af3f82'
SOURCE_COMMIT='5120290da88f3f205f74aa55f3c8fa1f19d1bc8b'
SOURCE_BLOB='75a393f84ad41181d39be9de26ddfdb33deb7d56'


def alpha(svg):
    with Image.open(BytesIO(cairosvg.svg2png(
        bytestring=svg.encode('utf-8'),output_width=1200,output_height=760
    ))) as image:
        image.load()
        return np.asarray(image.convert('RGBA').getchannel('A')) >= 128


def components(mask):
    h,w=mask.shape
    seen=np.zeros_like(mask,dtype=bool)
    result=[]
    for y in range(h):
        for x in range(w):
            if not mask[y,x] or seen[y,x]:
                continue
            stack=[(y,x)]; seen[y,x]=True; pixels=[]
            while stack:
                yy,xx=stack.pop(); pixels.append((yy,xx))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True; stack.append((ny,nx))
            result.append(pixels)
    return result


class CubaCayAffiliationTest(unittest.TestCase):
    def test_all_rendered_cuba_components_match_ne10m_cuba(self):
        country=json.loads((ROOT/'data/countries/cuba.json').read_text(encoding='utf-8'))
        source=ROOT/country['map']['svg']
        root=ET.parse(source).getroot()
        target=[p for p in root.iter(SVG+'path') if p.get('fill')=='url(#land)']
        self.assertEqual(len(target),1)
        self.assertIsNone(target[0].get('transform'))

        fixture=ROOT/'ops/map-context-sources/cuba/cuba-ne10m-v4.1.0.geojson'
        raw=fixture.read_bytes()
        import hashlib
        git_blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        self.assertEqual(git_blob,FIXTURE_BLOB)
        payload=json.loads(raw)
        self.assertEqual(payload['properties']['ISO_A3'],'CUB')

        b=country['map']['bounds']
        bounds=tuple(float(b[k]) for k in ('west','south','east','north'))
        reference=shape(payload['geometry']).intersection(box(*maps.canvas_bounds(bounds)))
        ref_path=maps.make_context_path(reference,bounds,0.0)
        self.assertTrue(ref_path)

        target_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760">'
            f'<path d="{target[0].get("d")}" fill="white" '
            f'fill-rule="{target[0].get("fill-rule","nonzero")}"/></svg>'
        )
        ref_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760">'
            f'<path d="{ref_path}" fill="white" fill-rule="evenodd"/></svg>'
        )
        target_mask=alpha(target_svg)
        ref_mask=alpha(ref_svg)
        self.assertGreater(int(target_mask.sum()),10000)
        self.assertGreater(int(ref_mask.sum()),10000)

        ref_expanded=np.asarray(
            Image.fromarray(ref_mask.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(13))
        )>0
        target_expanded=np.asarray(
            Image.fromarray(target_mask.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(13))
        )>0

        # Every visible Cuban target component >=4 px must coincide with the
        # independent 1:10m CUB polygon after a 6 px source-vintage tolerance.
        checked=0
        for pixels in components(target_mask):
            if len(pixels)<4:
                continue
            checked+=1
            covered=sum(ref_expanded[y,x] for y,x in pixels)/len(pixels)
            self.assertGreaterEqual(covered,0.90)
        self.assertGreaterEqual(checked,10)

        # Conversely, the pinned 1:10m reference's meaningful rendered land is
        # represented by the approved target at this map scale.
        self.assertGreaterEqual(float((ref_mask & target_expanded).sum())/float(ref_mask.sum()),0.92)


if __name__=='__main__':
    unittest.main()
