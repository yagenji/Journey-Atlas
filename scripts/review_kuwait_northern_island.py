#!/usr/bin/env python3
"""Read-only source attribution for Kuwait's one unresolved northern context ring.

Compare it to pinned 2023 geoBoundaries Kuwait (OSM/Wambacher, ODbL)
and Iraq (Natural Earth, public domain). Never delete uncertain land.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon, box, shape
from shapely.ops import transform, unary_union

from reconcile_gulf_foreign import reconcile

ROOT=Path(__file__).resolve().parents[1]
NS='{http://www.w3.org/2000/svg}'
REVISION='9469f09592ced973a3448cf66b6100b741b64c0d'
BASE=f'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/{REVISION}/releaseData/gbOpen'
SOURCE={'KWT':f'{BASE}/KWT/ADM0/geoBoundaries-KWT-ADM0.geojson',
        'IRQ':f'{BASE}/IRQ/ADM0/geoBoundaries-IRQ-ADM0.geojson'}
XY=re.compile(r'(-?(?:\d+(?:\.\d*)?|\.\d+)),(-?(?:\d+(?:\.\d*)?|\.\d+))')


def read_geo(iso, out, override=None):
    if override is not None:
        raw=override.read_bytes()
    else:
        req=urllib.request.Request(SOURCE[iso],headers={'User-Agent':'Journey-Atlas-geographic-QA/1.0'})
        with urllib.request.urlopen(req,timeout=75) as f:
            raw=f.read(14_000_001)
    if len(raw)>14_000_000 or raw.startswith(b'version https://git-lfs'):
        raise RuntimeError(f'Unresolved or oversized {iso} original data')
    data=json.loads(raw)
    if data.get('type')!='FeatureCollection' or len(data.get('features',[]))!=1:
        raise RuntimeError(f'Unexpected {iso} original GeoJSON')
    feature=data['features'][0]
    if feature.get('properties',{}).get('shapeISO') != iso:
        raise RuntimeError(f'Wrong {iso} source identity')
    geom=shape(feature['geometry'])
    if geom.is_empty or not geom.is_valid:raise RuntimeError(f'Invalid {iso} source topology')
    (out/f'{iso}-2023-source.geojson').write_bytes(raw)
    return geom,hashlib.sha256(raw).hexdigest()


def frame_projection(region):
    bounds,rect=region['bounds'],region['rect']
    west,south,east,north=(bounds[k] for k in ('west','south','east','north'))
    x,y,width,height=(rect[k] for k in ('x','y','width','height'))
    factor=math.cos(math.radians((south+north)/2))
    scale=min(width/((east-west)*factor),height/(north-south))
    ox=x+(width-(east-west)*factor*scale)/2
    oy=y+(height-(north-south)*scale)/2
    return (lambda lon,lat,z=None:(ox+(lon-west)*factor*scale,oy+(north-lat)*scale),
            box(x,y,x+width,y+height))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=ROOT)
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--kwt-geojson',type=Path)
    p.add_argument('--irq-geojson',type=Path)
    args=p.parse_args();root=args.repo.resolve();out=args.output_dir.resolve()
    if out==root or root in out.parents:raise RuntimeError('Review outputs must not enter repository')
    out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((root/'data/countries/kuwait.json').read_text())
    source=root/cfg['map']['svg']
    original=source.read_text()
    staged=reconcile(original,source,'kuwait','i')
    before=ET.fromstring(original);after=ET.fromstring(staged)
    land=lambda root:[dict(p.attrib) for p in root.iter(NS+'path') if p.get('fill')=='url(#land)']
    if land(before)!=land(after) or len(land(before))!=2:
        raise RuntimeError('Approved Kuwait national paths changed')
    ctx=[p for p in after.iter(NS+'path') if p.get('data-map-context-region')=='country']
    if len(ctx)!=1:raise RuntimeError('Unreviewed Kuwait foreign context layout')
    rings=[]
    for sub in re.findall(r'M\s*[^M]+',ctx[0].get('d','')):
        poly=Polygon([(float(x),float(y)) for x,y in XY.findall(sub)])
        if not poly.is_valid:raise RuntimeError('Invalid generated Kuwait foreign ring')
        rings.append(poly)
    if len(rings)!=2:raise RuntimeError('Unexpected Kuwait foreign ring count')
    ring=min(rings,key=lambda g:g.area)
    if not 10<ring.area<50 or not 500<ring.centroid.x<580 or not 70<ring.centroid.y<130:
        raise RuntimeError('Kuwait ring changed; attribution must be reviewed again')
    xy,viewport=frame_projection(next(r for r in cfg['map']['regions'] if r['id']=='country'))
    qat={}
    for iso,fixture in [('KWT',args.kwt_geojson),('IRQ',args.irq_geojson)]:
        geo,sha=read_geo(iso,out,fixture)
        projected=transform(xy,geo).intersection(viewport)
        overlap=ring.intersection(projected).area
        qat[iso]={'sourceSha256':sha,'sourceUrl':SOURCE[iso],
                  'overlapWithRingPx2':round(overlap,4),
                  'overlapFraction':round(overlap/ring.area,6),
                  'distanceToSourcePx':round(ring.distance(projected),4)}
    if qat['KWT']['overlapFraction']>=0.95 and qat['IRQ']['overlapFraction']<0.05:
        attribution='KWT_DOMESTIC_SOURCE_MATCH'
    elif qat['IRQ']['overlapFraction']>=0.95 and qat['KWT']['overlapFraction']<0.05:
        attribution='IRQ_FOREIGN_SOURCE_MATCH'
    else:attribution='UNRESOLVED: sources differ or ring is outside both'
    report={'status':'HOLD: source attribution is diagnostic, not approval',
            'islandAreaPx2':round(ring.area,4),
            'islandCentroidSvgPx':[round(ring.centroid.x,4),round(ring.centroid.y,4)],
            'attribution':attribution,'sources':qat,
            'originalNationalPathsIdentical':land(before)==land(after),
            'sourceRevision':REVISION}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
