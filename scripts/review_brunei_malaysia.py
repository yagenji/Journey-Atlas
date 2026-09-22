#!/usr/bin/env python3
"""Review Brunei/Malaysia candidate against original GSHHG and pinned national SVG.

Do not edit the approved national paths or silently turn domestic Pulau Muara
Besar into foreign land. This is a QA preview, never permission to release.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Point
from shapely.ops import unary_union
from reconcile_brunei_foreign import APPROVED_SHA, reconcile, rings

ROOT=Path(__file__).resolve().parents[1]
NS='{http://www.w3.org/2000/svg}'


def generate(root,config,source,out,script):
    subprocess.run([sys.executable,str(root/'scripts'/script),
                    '--country-json',str(config),'--input',str(source),
                    '--output',str(out),'--resolution','i'],
                   cwd=root,check=True,timeout=180)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,default=ROOT)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    root=args.repo.resolve();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    config=root/'data/countries/brunei.json'
    source=root/json.loads(config.read_text())['map']['svg']
    original=source.read_bytes()
    if hashlib.sha256(original).hexdigest()!=APPROVED_SHA:
        raise RuntimeError('Approved Brunei source changed')
    raw_candidate=out/'candidate.svg'
    generate(root,config,source,raw_candidate,'add_country_map_context_legacy.py')
    candidate=raw_candidate.read_text()
    checked=reconcile(candidate,source,'i')
    staged=out/'brunei-reviewed.svg'
    generate(root,config,source,staged,'add_country_map_context_existing.py')
    actual=staged.read_text()
    if actual!=checked:
        raise RuntimeError('Staging adapter deviates from geographic-source review')
    original_shape=next(p.get('d') for p in ET.fromstring(original).iter(NS+'path')
                        if p.get('fill')=='url(#country)')
    national=next(p.get('d') for p in ET.fromstring(actual).iter(NS+'path')
                  if p.get('fill')=='url(#country)')
    if original_shape!=national:
        raise RuntimeError('Approved Brunei national outline modified')
    from_source=next(ET.fromstring(candidate).find('.//*[@id="geographic-context"]').iter(NS+'path')).get('d')
    source_rings=rings(from_source)
    mainland=max(source_rings,key=lambda p:p.area)
    island=min(source_rings,key=lambda p:p.area)
    country=unary_union(rings(original_shape))
    source_diff=mainland.difference(country)
    foreign=max(source_diff.geoms,key=lambda p:p.area)
    if not island.covers(Point(855,90)):
        raise RuntimeError('Unrecognized offshore island')
    image=cairosvg.svg2png(bytestring=actual.encode(),output_width=1200,output_height=760)
    with Image.open(io.BytesIO(image)) as decoded:
        decoded.load()
        if decoded.size!=(1200,760):raise RuntimeError('Full-resolution decode failed')
    (out/'brunei-reviewed.png').write_bytes(image)
    report={'status':'HOLD: protected target omits domestic Pulau Muara Besar',
            'approvedSha256':APPROVED_SHA,
            'candidateForeignArea':round(foreign.area,2),
            'originalContextOverlap':round(unary_union(source_rings).intersection(country).area,2),
            'domesticIslandRemovedFromForeignContextSvgPx2':round(island.area,2),
            'shorelineSliversRemovedSvgPx2':round(source_diff.area-foreign.area,2),
            'nationalPathsIdentical':True,'decodedSize':[1200,760],
            'reviewSvgSha256':hashlib.sha256(actual.encode()).hexdigest(),
            'adapterMatchesIndependentSourceReview':True}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
