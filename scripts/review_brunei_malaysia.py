#!/usr/bin/env python3
"""Final Brunei/Malaysia Stage-2 review including Pulau Muara Besar."""
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
from reconcile_brunei_foreign import (
    ORIGINAL_TARGET_SHA, PMB_TARGET_SHA, PMB_OSM_RAW_SHA, reconcile, rings
)

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
    source_root=ET.fromstring(original)
    original_shapes=[p.get('d') for p in source_root.iter(NS+'path')
                     if p.get('fill')=='url(#country)']
    if (len(original_shapes)!=2
            or [hashlib.sha256(p.encode()).hexdigest() for p in original_shapes]
               !=[ORIGINAL_TARGET_SHA,PMB_TARGET_SHA]):
        raise RuntimeError('Protected Brunei target set changed')
    metadata=''.join(source_root.find(NS+'metadata').itertext())
    if PMB_OSM_RAW_SHA not in metadata or 'OpenStreetMap way 28531951 version 9' not in metadata:
        raise RuntimeError('PMB source provenance missing')

    raw_candidate=out/'candidate.svg'
    generate(root,config,source,raw_candidate,'add_country_map_context_legacy.py')
    candidate=raw_candidate.read_text()
    checked=reconcile(candidate,source,'i')
    staged=out/'brunei-reviewed.svg'
    generate(root,config,source,staged,'add_country_map_context_existing.py')
    actual=staged.read_text()
    if actual!=checked:
        raise RuntimeError('Staging adapter deviates from geographic-source review')

    actual_root=ET.fromstring(actual)
    national=[p.get('d') for p in actual_root.iter(NS+'path') if p.get('fill')=='url(#country)']
    if original_shapes!=national:
        raise RuntimeError('Protected Brunei national geometry modified')

    from_source=next(ET.fromstring(candidate).find('.//*[@id="geographic-context"]').iter(NS+'path')).get('d')
    source_rings=rings(from_source)
    mainland=max(source_rings,key=lambda p:p.area)
    older_pmb=min(source_rings,key=lambda p:p.area)
    country=unary_union([ring for path in original_shapes for ring in rings(path)])
    source_diff=mainland.difference(country)
    foreign=max(source_diff.geoms,key=lambda p:p.area)
    pmb=rings(original_shapes[1])[0]
    pmb_intersection=older_pmb.intersection(pmb).area
    if not (pmb.covers(Point(855,90)) and 600<pmb.area<650
            and pmb_intersection/older_pmb.area>.90
            and older_pmb.hausdorff_distance(pmb)<18):
        raise RuntimeError('PMB current OSM target does not match independently identified domestic island')

    image=cairosvg.svg2png(bytestring=actual.encode(),output_width=1200,output_height=760)
    with Image.open(io.BytesIO(image)) as decoded:
        decoded.load()
        if decoded.size!=(1200,760):raise RuntimeError('Full-resolution decode failed')
    (out/'brunei-reviewed.png').write_bytes(image)
    report={
        'status':'PASS: Stage 2 individual geographic QA accepted for reviewed Brunei migration candidate',
        'protectedTargetPathCount':2,
        'existingMainlandTargetSha256':ORIGINAL_TARGET_SHA,
        'pulauMuaraBesarPathSha256':PMB_TARGET_SHA,
        'pulauMuaraBesarOsmRawSha256':PMB_OSM_RAW_SHA,
        'pulauMuaraBesarPresent':True,
        'pulauMuaraBesarProjectedAreaSvgPx2':round(pmb.area,2),
        'olderGshhgPmbAreaSvgPx2':round(older_pmb.area,2),
        'olderGshhgOverlapWithCurrentPmbPct':round(100*pmb_intersection/older_pmb.area,2),
        'olderGshhgVsCurrentPmbHausdorffSvgPx':round(older_pmb.hausdorff_distance(pmb),3),
        'candidateForeignArea':round(foreign.area,2),
        'originalContextOverlap':round(unary_union(source_rings).intersection(country).area,2),
        'shorelineSliversRemovedSvgPx2':round(source_diff.area-foreign.area,2),
        'nationalPathsIdentical':True,
        'decodedSize':[1200,760],
        'reviewSvgSha256':hashlib.sha256(actual.encode()).hexdigest(),
        'adapterMatchesIndependentSourceReview':True,
        'dispositionScope':'JOURNEY ATLAS 1200x760 migration candidate; not cadastral/legal boundary certification'
    }
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
