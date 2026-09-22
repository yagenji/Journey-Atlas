#!/usr/bin/env python3
"""Disposable, source-pinned Portugal/Spain geography comparison; never writes to the repository."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Polygon, box, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import add_country_map_context as core

OUT = Path('/tmp/journey-atlas-portugal-spain-diagnostic')
SVG = '{http://www.w3.org/2000/svg}'
SOURCES = {
    'PRT': 'ce02dabb0ea17eba11923f78ed1525d8989c9b58',
    'ESP': '01ec685ca5739b63292e01380ff36287413508b5',
}


def pinned_source(country: str):
    url = f'https://raw.githubusercontent.com/LonnyGomes/CountryGeoJSONCollection/master/geojson/{country}.geojson'
    with urllib.request.urlopen(url, timeout=45) as response:
        raw = response.read(15_000_000)
    digest = hashlib.sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()
    if digest != SOURCES[country]:
        raise RuntimeError(f'{country} Natural Earth upstream changed: expected {SOURCES[country]}, got {digest}')
    return shape(json.loads(raw)['geometry']), url


def rings(d: str):
    parts = []
    for segment in re.split(r'(?=\bM\s)', d):
        coords = [tuple(map(float, pair)) for pair in re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', segment)]
        if len(coords) >= 3:
            parts.append(Polygon(coords))
    return parts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / 'data/countries/portugal.json').read_text(encoding='utf-8'))
    regions = cfg['map']['regions']
    mainland = next(r for r in regions if r['id'] == 'mainland')
    bounds = tuple(float(mainland['bounds'][k]) for k in ('west','south','east','north'))
    rect = tuple(float(mainland['rect'][k]) for k in ('x','y','width','height'))
    original = ROOT / cfg['map']['svg']
    draft = OUT / 'original-stage.svg'
    subprocess.run([sys.executable, str(ROOT / 'scripts/add_country_map_context_existing.py'),
                    '--country-json', str(ROOT / 'data/countries/portugal.json'),
                    '--input', str(original), '--output', str(draft), '--resolution', 'i'],
                   cwd=ROOT, timeout=180, check=True)
    prior = draft.read_text(encoding='utf-8')
    root = ET.fromstring(prior)
    approved = [p.get('d') for p in root.iter(SVG+'path') if p.get('fill') == 'url(#land)']
    if len(approved) != 15: raise RuntimeError('Portugal approved path count has changed')
    main_target = max((p for d in approved for p in rings(d)), key=lambda p: p.area)
    if not main_target.is_valid: raise RuntimeError('Portugal mainland target is not a valid polygon')
    factor, scale, ox, oy = core.frame(bounds, rect)
    west, south, east, north = bounds
    target_geo = transform(lambda x, y, z=None: (west+(x-ox)/(factor*scale), north-(y-oy)/scale), main_target)
    prt, prt_url = pinned_source('PRT')
    esp, esp_url = pinned_source('ESP')
    prt_main = max((prt.geoms if hasattr(prt,'geoms') else [prt]), key=lambda p:p.area)
    country_hausdorff_degrees = target_geo.boundary.hausdorff_distance(prt_main.boundary)
    viewport = box(*core.canvas_bounds(bounds, rect))
    es_view = esp.intersection(viewport)
    es_in_pt = es_view.intersection(target_geo).area
    esp_path = core.make_context_path(es_view, bounds, .003, rect)
    if not esp_path or len(esp_path) < 100: raise RuntimeError('Spain closed land polygon absent')
    pat = re.compile(r'(<path data-map-context-region="mainland" d=")([^"]+)("[^>]*/>)')
    matches = list(pat.finditer(prior))
    if len(matches) != 1: raise RuntimeError('Expected one main context path')
    previous_mainland_path = matches[0].group(2)
    candidate = prior[:matches[0].start(2)] + esp_path + prior[matches[0].end(2):]
    candidate = candidate.replace('<g id="geographic-context"',
       '<g id="geographic-context"', 1)
    candidate = candidate.replace('id="geographic-context" fill=',
       'id="geographic-context" fill=', 1)
    updated = ET.fromstring(candidate)
    after = [p.get('d') for p in updated.iter(SVG+'path') if p.get('fill') == 'url(#land)']
    if after != approved or updated.get('viewBox') != '0 0 1200 760':
        raise RuntimeError('Spain replacement changed approved Portugal geometry or canvas')
    out_svg = OUT / 'portugal-spain-same-natural-earth.svg'
    out_svg.write_text(candidate, encoding='utf-8')
    out_png = OUT / 'portugal-spain-same-natural-earth.png'
    cairosvg.svg2png(bytestring=candidate.encode('utf-8'),write_to=str(out_png))
    with Image.open(out_png) as image:
        image.load()
        if image.size != (1200,760):raise RuntimeError('Invalid raster size')
    metrics = dict(prtGitBlob=SOURCES['PRT'], espGitBlob=SOURCES['ESP'],
       prtUrl=prt_url, espUrl=esp_url, targetVsSourceHausdorffDegrees=country_hausdorff_degrees,
       spainInApprovedPortugalGeoDegrees2=es_in_pt,
       oldMainlandSha256=hashlib.sha256(previous_mainland_path.encode()).hexdigest(),
       spanishMainlandSvgPathSha256=hashlib.sha256(esp_path.encode()).hexdigest(),
       oldMainlandBytes=len(previous_mainland_path), spanishMainlandBytes=len(esp_path),
       targetPathCount=len(approved), svgViewBox=updated.get('viewBox'))
    (OUT/'report.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metrics, indent=2),flush=True)

if __name__ == '__main__':main()
