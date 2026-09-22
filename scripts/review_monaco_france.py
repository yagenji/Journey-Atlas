#!/usr/bin/env python3
"""Inspect actual PR-head Monaco/France SVG, not stale GSHHG diagonal previews.

Read-only targeted QA: approved Monaco outline must stay byte identical;
OSM French source credit must be present, and full 1200x760 must decode.
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
OLD_GSHHG='M 302.2,760.0 L -0.0,760.0 L -0.0,0.0 L 979.8,0.0 L 302.2,760.0 Z'


def polygon_rings(path):
    polygons=[]
    for segment in re.split(r'(?=\bM\s)',path):
        xy=[tuple(map(float,p)) for p in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',segment)]
        if len(xy)>3:
            poly=Polygon(xy)
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
    targets=[p for p in root.iter(NS+'path') if p.get('fill')=='url(#land)']
    if len(targets)!=1 or hashlib.sha256(targets[0].get('d','').encode()).hexdigest()!=TARGET_SHA:
        raise RuntimeError('Protected Monaco original national path differs from reviewed source')
    context=root.find('.//*[@id="geographic-context"]')
    if context is None:raise RuntimeError('Missing Monaco neighboring land')
    desc=''.join(context.itertext())
    if not ('OpenStreetMap' in desc and 'ODbL' in desc):
        raise RuntimeError('Monaco French-land provenance/visible-credit input missing')
    contextual=[p for p in context.iter(NS+'path') if p.get('d')]
    if not contextual:raise RuntimeError('Missing actual French-land source geometry')
    # The earlier coarse five-vertex GSHHG diagonal is a known *exact* bad case;
    # file-length thresholds falsely reject real, short, separately sourced rings.
    france=' '.join(p.get('d') for p in contextual)
    if len(contextual)==1 and contextual[0].get('d').strip()==OLD_GSHHG:
        raise RuntimeError('Stale rectangular/diagonal GSHHG context still present')
    image=cairosvg.svg2png(bytestring=raw,output_width=1200,output_height=760)
    with Image.open(io.BytesIO(image)) as im:
        im.load()
        if im.size!=(1200,760):raise RuntimeError('Monaco PNG decode failed')
    (out/'monaco-current.svg').write_bytes(raw)
    (out/'monaco-current.png').write_bytes(image)
    target_rings=polygon_rings(targets[0].get('d'))
    french_rings=polygon_rings(france)
    report={'status':'HOLD: OSM target/French land rendered; independently review coastal seams',
            'sourceSha256':hashlib.sha256(raw).hexdigest(),
            'originalMonacoPathSha256':TARGET_SHA,'protectedPaths':1,
            'source':desc,'contextPathCount':len(contextual),
            'contextRingCount':len(french_rings),
            'targetRingCount':len(target_rings),'fullRaster':[1200,760]}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
