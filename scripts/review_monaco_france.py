#!/usr/bin/env python3
"""Inspect actual PR-head Monaco/France SVG, not stale GSHHG diagonal previews.

Final targeted QA: preserve the approved Monaco outline, measure the
independent French land, and require an exact target-negative display clip.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
import cairosvg
from PIL import Image
from shapely.geometry import Polygon

ROOT=Path(__file__).resolve().parents[1]
NS='{http://www.w3.org/2000/svg}'
TARGET_SHA='6338d1de050b6cf8ae063e5c6e64cf582500b0f6117f84ad69976690691171fe'
SOURCE_SHA='680fa76e8a1cf451315178ff4486081b956af8bfdca7ff2616a82c8d4eadbf0e'
OLD_GSHHG='M 302.2,760.0 L -0.0,760.0 L -0.0,0.0 L 979.8,0.0 L 302.2,760.0 Z'


def polygon_rings(path):
    polygons=[]
    for segment in re.split(r'(?=\bM\s)',path):
        xy=[tuple(map(float,p)) for p in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',segment)]
        if len(xy)>3:
            poly=Polygon(xy)
            if not poly.is_valid:raise RuntimeError('Invalid Monaco/French polygon topology')
            if poly.area>.01:polygons.append(poly)
    return polygons


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--repo',type=Path,default=ROOT)
    cli.add_argument('--output-dir',type=Path,required=True)
    args=cli.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    path=args.repo/'assets/images/monaco/map-atlas-v1.svg'
    raw=path.read_bytes();root=ET.fromstring(raw)
    if root.get('viewBox')!='0 0 1200 760':raise RuntimeError('Monaco canvas changed')
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise RuntimeError('Reviewed Monaco/French source changed: recheck boundary')
    targets=[p for p in root.iter(NS+'path') if p.get('fill')=='url(#land)']
    if len(targets)!=1 or hashlib.sha256(targets[0].get('d','').encode()).hexdigest()!=TARGET_SHA:
        raise RuntimeError('Protected Monaco original national path differs from reviewed source')
    context=root.find('.//*[@id="geographic-context"]')
    if context is None:raise RuntimeError('Missing Monaco neighboring land')
    clip_id='monaco-foreign-only'
    if context.get('clip-path')!='url(#'+clip_id+')':
        raise RuntimeError('Monaco foreign land is not protected by exact national exclusion')
    clip=root.find(".//*[@id='"+clip_id+"']")
    if clip is None or len(list(clip.iter(NS+'path')))!=1:
        raise RuntimeError('Missing Monaco target-negative clip')
    expected_clip='M 0,0 L 1200,0 L 1200,760 L 0,760 Z '+targets[0].get('d')
    clip_path=next(clip.iter(NS+'path'))
    if (clip_path.get('d')!=expected_clip or clip_path.get('fill-rule')!='evenodd'
            or clip_path.get('clip-rule')!='evenodd'):
        raise RuntimeError('Monaco exclusion clip is not the exact protected target complement')
    desc=''.join(context.itertext())
    if not ('OpenStreetMap' in desc and 'ODbL' in desc):
        raise RuntimeError('Monaco French-land provenance/visible-credit input missing')
    contextual=[p for p in context.iter(NS+'path') if p.get('d')]
    french_fill=[p for p in contextual if p.get('fill')=='#e4e0ce']
    if len(french_fill)!=1:raise RuntimeError('Unexpected French mainland land polygon')
    if len(contextual)==1 and contextual[0].get('d').strip()==OLD_GSHHG:
        raise RuntimeError('Stale rectangular/diagonal GSHHG context still present')
    target_rings=polygon_rings(targets[0].get('d'))
    french_rings=polygon_rings(french_fill[0].get('d'))
    if len(target_rings)!=2 or len(french_rings)!=1:
        raise RuntimeError('Monaco island/mainland or French land source changed')
    monaco=max(target_rings,key=lambda p:p.area)
    france=french_rings[0]
    overlap=monaco.intersection(france).area
    # Sample the unchanged Monaco mainland outline every SVG pixel. Only
    # compare the portions lying within 5px of the independently sourced
    # French polygon boundary: the rest is Monaco's actual seaward coastline.
    # A few endpoints near open water are not permission to bridge the water.
    close=[france.boundary.distance(monaco.exterior.interpolate(float(i)))
           for i in range(int(monaco.exterior.length))]
    near=[d for d in close if d<5]
    within_quarter=sum(d<=.25 for d in near)
    if not (1200<=len(near)<=1240 and within_quarter>=1200
            and 0<=overlap<20 and monaco.is_valid and france.is_valid):
        raise RuntimeError('Monaco–France coast/border geometry requires new geographic QA')
    image=cairosvg.svg2png(bytestring=raw,output_width=1200,output_height=760)
    with Image.open(io.BytesIO(image)) as im:
        im.load()
        if im.size!=(1200,760):raise RuntimeError('Monaco PNG decode failed')
    (out/'monaco-current.svg').write_bytes(raw)
    (out/'monaco-current.png').write_bytes(image)
    report={'status':'PASS: Stage 2 individual geographic QA accepted for reviewed Monaco migration candidate',
            'sourceSha256':SOURCE_SHA,
            'originalMonacoPathSha256':TARGET_SHA,'protectedPaths':1,
            'source':desc,'contextPathCount':len(contextual),
            'contextRingCount':len(french_rings),
            'targetRingCount':len(target_rings),
            'nearFrenchBorderSamplesUnder5px':len(near),
            'borderSamplesWithinQuarterSvgPixel':within_quarter,
            'frenchOverlapWithProtectedMonacoSvgPx2':round(overlap,3),
            'displayForeignOverlapAfterExactClipSvgPx2':0.0,
            'displayForeignClipExactTargetComplement':True,
            'dispositionScope':'JOURNEY ATLAS 1200x760 migration candidate; not cadastral/legal boundary certification',
            'fullRaster':[1200,760]}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
