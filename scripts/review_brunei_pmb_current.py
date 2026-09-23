#!/usr/bin/env python3
"""One-shot current OSM source capture for Pulau Muara Besar.

Temporary Stage-2 evidence generator. It downloads one named OSM coastline way,
projects it onto the approved Brunei 1200x760 frame, writes a source snapshot and
read-only preview, and never edits repository production assets.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Polygon

ROOT=Path(__file__).resolve().parents[1]
WAY_ID=28531951
URL=f'https://www.openstreetmap.org/api/0.6/way/{WAY_ID}/full.json'
W,H=1200,760


def project(bounds, lon, lat):
    west,south,east,north=(bounds[k] for k in ('west','south','east','north'))
    factor=math.cos(math.radians((south+north)/2))
    scale=min(W/((east-west)*factor), H/(north-south))
    ox=(W-(east-west)*factor*scale)/2
    oy=(H-(north-south)*scale)/2
    return ox+(lon-west)*factor*scale, oy+(north-lat)*scale


def svg_path(poly):
    pts=[(round(x,2),round(y,2)) for x,y in poly.exterior.coords]
    pts=[p for i,p in enumerate(pts) if not i or p!=pts[i-1]]
    return 'M '+' L '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+' Z'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=ROOT)
    ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args()
    repo=args.repo.resolve()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)

    req=urllib.request.Request(URL,headers={'User-Agent':'JOURNEY-ATLAS-source-QA/1.0'})
    with urllib.request.urlopen(req,timeout=45) as response:
        raw=response.read()
    data=json.loads(raw)
    elements=data.get('elements',[])
    way=next((e for e in elements if e.get('type')=='way' and e.get('id')==WAY_ID),None)
    if way is None:
        raise RuntimeError('Pulau Muara Besar OSM way missing')
    tags=way.get('tags',{})
    if tags.get('natural')!='coastline' or tags.get('place')!='island' or 'Muara Besar' not in tags.get('name',''):
        raise RuntimeError('OSM Pulau Muara Besar identity/tags changed')
    timestamp=way.get('timestamp','')
    if timestamp < '2025-03-01':
        raise RuntimeError('OSM Pulau Muara Besar source unexpectedly old')
    nodes={e['id']:(e['lon'],e['lat']) for e in elements if e.get('type')=='node'}
    node_ids=way.get('nodes',[])
    if len(node_ids)<50 or node_ids[0]!=node_ids[-1] or any(n not in nodes for n in node_ids):
        raise RuntimeError('OSM Pulau Muara Besar coastline is incomplete/unclosed')
    coords=[nodes[n] for n in node_ids]
    lons=[p[0] for p in coords];lats=[p[1] for p in coords]
    if not (115.05<min(lons)<115.09 and 115.12<max(lons)<115.16 and 4.97<min(lats)<5.00 and 5.02<max(lats)<5.05):
        raise RuntimeError('OSM Pulau Muara Besar bounds changed unexpectedly')

    config=json.loads((repo/'data/countries/brunei.json').read_text())
    projected=[project(config['map']['bounds'],lon,lat) for lon,lat in coords]
    poly=Polygon(projected)
    if not poly.is_valid or not (500<poly.area<900):
        raise RuntimeError(f'Unexpected projected PMB geometry area {poly.area}')
    simplified=poly.simplify(.35,preserve_topology=True)
    if not simplified.is_valid or simplified.geom_type!='Polygon':
        raise RuntimeError('PMB simplification invalid')
    if abs(simplified.area-poly.area)/poly.area>.003:
        raise RuntimeError('PMB simplification changed area too much')
    path=svg_path(simplified)
    source=(repo/config['map']['svg']).read_text()
    root=ET.fromstring(source)
    if root.get('viewBox')!='0 0 1200 760':
        raise RuntimeError('Brunei approved canvas changed')
    addition=(f'<path data-source="osm-pulau-muara-besar-{WAY_ID}" d="{path}" '
              'fill="url(#country)" fill-rule="evenodd" stroke="#31576a" '
              'stroke-width="2.0" stroke-linejoin="round"/>')
    preview=source.replace('</svg>',addition+'\n</svg>')
    png=cairosvg.svg2png(bytestring=preview.encode(),output_width=W,output_height=H)
    with Image.open(io.BytesIO(png)) as im:
        im.load()
        if im.size!=(W,H): raise RuntimeError('Preview decode failed')

    (out/'pmb-osm-source.json').write_text(json.dumps({
        'sourceUrl':URL,
        'retrievedAt':dt.datetime.now(dt.timezone.utc).isoformat(),
        'rawSha256':hashlib.sha256(raw).hexdigest(),
        'wayId':WAY_ID,
        'wayVersion':way.get('version'),
        'wayTimestamp':timestamp,
        'changeset':way.get('changeset'),
        'nodeCount':len(node_ids),
        'tags':tags,
        'wgs84Bounds':{'west':min(lons),'south':min(lats),'east':max(lons),'north':max(lats)},
        'projectedAreaSvgPx2':round(poly.area,3),
        'simplifiedAreaSvgPx2':round(simplified.area,3),
        'pathSha256':hashlib.sha256(path.encode()).hexdigest(),
        'path':path,
        'licence':'OpenStreetMap contributors, ODbL 1.0',
    },ensure_ascii=False,indent=2)+'\n')
    (out/'pmb-osm-source-raw.json').write_bytes(raw)
    (out/'brunei-pmb-source-preview.svg').write_text(preview)
    (out/'brunei-pmb-source-preview.png').write_bytes(png)
    print(json.dumps({
        'wayId':WAY_ID,'wayTimestamp':timestamp,'nodeCount':len(node_ids),
        'rawSha256':hashlib.sha256(raw).hexdigest(),
        'pathSha256':hashlib.sha256(path.encode()).hexdigest(),
        'projectedAreaSvgPx2':round(poly.area,3),
        'simplifiedAreaSvgPx2':round(simplified.area,3),
        'decoded':[W,H]
    },indent=2))


if __name__=='__main__':
    main()
