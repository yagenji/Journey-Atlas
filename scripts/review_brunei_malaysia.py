#!/usr/bin/env python3
"""Review-only Brunei/Sarawak context; never edit approved national geometry.

GSHHG's small offshore ring is Brunei's Pulau Muara Besar, not Malaysia.
Source review must distinguish it from Malaysian mainland before promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
SOURCE_SHA = '57fcee91d44f7d27052ba0ac96b209f0c465a447277d6dcdc970c4dec047978d'


def rings(d):
    chunks = [s for s in re.split(r'(?=\bM\s)', d) if s.strip()]
    if any(re.sub(r'[MLZ\s\d.,-]', '', s) for s in chunks):
        raise RuntimeError('Unreviewed SVG path commands')
    parts = [Polygon([tuple(map(float, xy)) for xy in
                     re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', s)])
             for s in chunks]
    if not parts or not all(p.is_valid and p.area > 0 for p in parts):
        raise RuntimeError('Invalid source polygon')
    return parts


def fmt(poly):
    parts = []
    for ring in [poly.exterior, *poly.interiors]:
        pts = [(round(x, 2), round(y, 2)) for x, y in ring.coords]
        pts = [p for i, p in enumerate(pts) if not i or p != pts[i-1]]
        if len(pts) >= 4:
            parts.append('M ' + ' L '.join(f'{x:.2f},{y:.2f}' for x, y in pts) + ' Z')
    return ' '.join(parts)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--repo', type=Path, default=ROOT)
    cli.add_argument('--output-dir', type=Path, required=True)
    a = cli.parse_args()
    root = a.repo.resolve()
    out = a.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    config_path = root / 'data/countries/brunei.json'
    config = json.loads(config_path.read_text())
    source = root / config['map']['svg']
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise RuntimeError('Approved Brunei SVG changed; independent re-review required')
    preview = out/'candidate.svg'
    subprocess.run([sys.executable, str(root/'scripts/add_country_map_context_existing.py'),
                    '--country-json', str(config_path), '--input', str(source),
                    '--output', str(preview), '--resolution', 'i'],
                   cwd=root, check=True, timeout=180)
    before = ET.fromstring(raw)
    result = preview.read_text()
    parsed = ET.fromstring(result)
    original = next(p.get('d') for p in before.iter(SVG+'path') if p.get('fill')=='url(#country)')
    target = next(p.get('d') for p in parsed.iter(SVG+'path') if p.get('fill')=='url(#country)')
    if original != target or parsed.get('viewBox')!='0 0 1200 760':
        raise RuntimeError('Approved national path or map canvas changed')
    ctx = parsed.find('.//*[@id="geographic-context"]')
    if ctx is None or len(list(ctx.iter(SVG+'path'))) != 1:
        raise RuntimeError('Expected exactly one generated contextual land path')
    path = next(ctx.iter(SVG+'path'))
    candidate = path.get('d')
    source_polygons = rings(candidate)
    target_polygons = rings(original)
    if len(source_polygons)!=2 or len(target_polygons)!=2:
        raise RuntimeError('Brunei/GSHHG source ring structure changed')
    brunei = unary_union(target_polygons)
    # The isolated SVG ring (836..873,78..100) reverse-projects to
    # Pulau Muara Besar, Brunei, ~5.00374N,115.10385E (GeoNames 1820361).
    mainland = max(source_polygons, key=lambda p:p.area)
    domestic_island = min(source_polygons, key=lambda p:p.area)
    if (not domestic_island.covers(Point(855, 90)) or
            not 400 < domestic_island.area < 500):
        raise RuntimeError('Domestic Pulau Muara Besar source changed')
    foreign = mainland.difference(brunei)
    if not foreign.is_valid:
        raise RuntimeError('Source difference invalid')
    components = sorted(foreign.geoms, key=lambda p:p.area, reverse=True)
    if not 420_000 < components[0].area < 430_000:
        raise RuntimeError('Malaysia mainland source extent changed')
    slivers = components[1:]
    if (sum(p.area for p in slivers) > 20 or
            any(p.distance(brunei) > 0.02 for p in slivers)):
        raise RuntimeError('Unverified isolated land; do not delete real islands')
    new_path = fmt(components[0])
    if not new_path or result.count('d="'+candidate+'"') != 1:
        raise RuntimeError('Unexpected context path')
    result = result.replace('d="'+candidate+'"', 'd="'+new_path+'"', 1)
    provenance = ('<desc>Malaysia/Sarawak neighboring mainland: GSHHG 2.3.6 '
                  'intermediate, WGS84, LGPL; exact difference against preserved '
                  'Brunei source country path. Pulau Muara Besar is Bruneian, '
                  'not foreign land; approved target omission requires separate '
                  'approval. https://www.ngdc.noaa.gov/mgg/shorelines/shorelines.html</desc>')
    result = result.replace('<g id="geographic-context">',
                            '<g id="geographic-context">'+provenance, 1)
    checked = ET.fromstring(result)
    if original != next(p.get('d') for p in checked.iter(SVG+'path')
                        if p.get('fill')=='url(#country)'):
        raise RuntimeError('Target path changed during correction')
    image = cairosvg.svg2png(bytestring=result.encode(),output_width=1200,output_height=760)
    with Image.open(io.BytesIO(image)) as im:
        im.load()
        if im.size!=(1200,760):raise RuntimeError('Full-size decode failed')
    (out/'brunei-reviewed.svg').write_text(result)
    (out/'brunei-reviewed.png').write_bytes(image)
    report = {'status':'HOLD: Pulau Muara Besar omitted from approved target; no unauthorized path edit',
              'approvedSha256':SOURCE_SHA,'candidateForeignArea':round(components[0].area,2),
              'originalContextOverlap':round(unary_union(source_polygons).intersection(brunei).area,2),
              'domesticIslandRemovedFromForeignContextSvgPx2':round(domestic_island.area,2),
              'shorelineSliversRemovedSvgPx2':round(sum(p.area for p in slivers),2),
              'nationalPathsIdentical':True,'decodedSize':[1200,760],
              'reviewSvgSha256':hashlib.sha256(result.encode()).hexdigest()}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
