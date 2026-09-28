#!/usr/bin/env python3
"""Source-backed *diagnostic only* for the Bahrain Hawar inset.

Compare the existing GSHHG foreign preview with Qatar gbOpen ADM0 from the
same 2023 geoBoundaries/OSM-Wambacher series as the approved Bahrain national SVG.
Output lives outside this repository; never edits protected geometry or deploys.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import re
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image
from shapely.geometry import Polygon, box, shape
from shapely.ops import transform, unary_union

import add_country_map_context_existing as existing
import add_country_map_context_legacy as legacy

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
REF = '9469f09592ced973a3448cf66b6100b741b64c0d'
SOURCE = (f'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/{REF}'
          '/releaseData/gbOpen/QAT/ADM0/geoBoundaries-QAT-ADM0.geojson')
CONTEXT = re.compile(r'(<path\s+data-map-context-legacy="hawar"\s+d=")([^"]+)("[^>]*/>)')
POINT = re.compile(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)')


def load_source(source_file: Path | None):
    if source_file:
        raw = source_file.read_bytes()
    else:
        req = urllib.request.Request(SOURCE, headers={'User-Agent':'Journey-Atlas-geoQA/1.0'})
        with urllib.request.urlopen(req, timeout=75) as reply:
            raw = reply.read(14_000_001)
    if len(raw) > 14_000_000 or raw.startswith(b'version https://git-lfs'):
        raise RuntimeError('Qatar source unresolved or exceeds guarded size')
    doc = json.loads(raw)
    if doc.get('type') != 'FeatureCollection' or not doc.get('features'):
        raise RuntimeError('Unexpected QAT geoBoundaries source structure')
    geo = unary_union([shape(f['geometry']) for f in doc['features']])
    if geo.is_empty or not geo.is_valid or geo.bounds[0] < 50 or geo.bounds[2] > 53:
        raise RuntimeError('Unreviewed QAT geometry or invalid coordinates')
    return raw, geo


def projection(region):
    bounds, rect = region['bounds'], region['rect']
    west, south, east, north = (bounds[k] for k in ('west','south','east','north'))
    x, y, width, height = (rect[k] for k in ('x','y','width','height'))
    factor = math.cos(math.radians((south+north)/2))
    scale = min(width/((east-west)*factor), height/(north-south))
    ox = x+(width-(east-west)*factor*scale)/2
    oy = y+(height-(north-south)*scale)/2
    frame = box(x,y,x+width,y+height)
    return lambda lon,lat,z=None: (ox+(lon-west)*factor*scale, oy+(north-lat)*scale),frame


def polygons(g):
    if g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    if hasattr(g, 'geoms'):
        return [p for component in g.geoms for p in polygons(component)]
    return []


def as_svg(g):
    parts=[]
    for p in polygons(g):
        if p.area < 0.05: continue
        p = p.simplify(0.035,preserve_topology=True)
        for ring in (p.exterior, *p.interiors):
            pts=[]
            for x,y in ring.coords:
                point = (round(x,1),round(y,1))
                if not pts or pts[-1] != point: pts.append(point)
            if len(pts) >= 4:
                parts.append('M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+' Z')
    if not parts: raise RuntimeError('No sibling Qatar land in Hawar frame')
    return ' '.join(parts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=ROOT)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--source-json',type=Path)
    args=parser.parse_args()
    root=args.repo.resolve();out=args.output_dir.resolve()
    if root == out or root in out.parents: raise RuntimeError('Review output must be outside repository')
    out.mkdir(parents=True,exist_ok=True)
    config=json.loads((root/'data/countries/bahrain.json').read_text())
    source=(root/config['map']['svg']).read_text()
    if 'boundaryID=BHR-ADM0-88433195' not in source or 'buildDate=Dec 12, 2023' not in source:
        raise RuntimeError('Approved Bahrain source vintage unexpectedly changed')
    source_root=ET.fromstring(source)
    approved=[dict(p.attrib) for p in source_root.iter(SVG+'path') if p.get('fill')=='url(#land)']
    if len(approved)!=2: raise RuntimeError('Unexpected approved Bahrain national paths')
    old=existing.reconcile_reviewed_bahrain_hawar(legacy._loose_multi_region(source,config,'i'),'i')
    matches=list(CONTEXT.finditer(old))
    if len(matches)!=1:raise RuntimeError('Unexpected approved Hawar foreign context layout')
    old_rings=[]
    for part in re.split(r'(?=\bM\s)',matches[0].group(2)):
        if not part.strip():continue
        pts=[(float(x),float(y)) for x,y in POINT.findall(part)]
        poly=Polygon(pts)
        if not poly.is_valid:raise RuntimeError('Unreviewed existing foreign ring')
        old_rings.append(poly)
    if len(old_rings)!=2:raise RuntimeError('Existing reviewed Hawar rings have changed')
    raw,qatar=load_source(args.source_json)
    region=next(r for r in config['map']['regions'] if r['id']=='hawar')
    xy,viewport=projection(region)
    sibling=transform(xy,qatar).intersection(viewport)
    if sibling.is_empty or not sibling.is_valid:
        raise RuntimeError('Qatar sibling source invalid in Hawar frame')
    original=unary_union(old_rings)
    proposed_d=as_svg(sibling)
    candidate=old[:matches[0].start(2)]+proposed_d+old[matches[0].end(2):]
    note=('<desc>Diagnostic foreign Qatar land: geoBoundaries gbOpen QAT ADM0 '
          'QAT-ADM0-15585745, same OSM/Wambacher 2023 vintage as approved Bahrain; '
          'ODbL 1.0; '+SOURCE+'; original Bahrain national paths unmodified.</desc>')
    candidate=candidate.replace('<g id="geographic-context" ',
                                '<g id="geographic-context" ',1)
    group=re.search(r'<g id="geographic-context"[^>]*>',candidate)
    if group is None:raise RuntimeError('Missing foreign context group')
    candidate=candidate[:group.end()]+note+candidate[group.end():]
    updated=ET.fromstring(candidate)
    after=[dict(p.attrib) for p in updated.iter(SVG+'path') if p.get('fill')=='url(#land)']
    if updated.get('viewBox')!='0 0 1200 760' or after!=approved:
        raise RuntimeError('Sibling diagnostic modified approved Bahrain national paths/canvas')
    raster=cairosvg.svg2png(bytestring=candidate.encode(),output_width=1200,output_height=760)
    with Image.open(io.BytesIO(raster)) as image:
        image.load()
        if image.size!=(1200,760):raise RuntimeError('Unexpected preview PNG size')
    (out/'qatar-2023-source.geojson').write_bytes(raw)
    (out/'hawar-qatar-sibling-diagnostic.svg').write_text(candidate)
    (out/'hawar-qatar-sibling-diagnostic.png').write_bytes(raster)
    report={'status':'HOLD: source comparison only; no foreign-context promotion',
            'source':SOURCE,'upstreamRevision':REF,'sourceSha256':hashlib.sha256(raw).hexdigest(),
            'sourceBytes':len(raw),'sourceLicense':'ODbL 1.0, OSM/Wambacher via geoBoundaries gbOpen',
            'qatarSameVintageSourceAreaPx2':round(sibling.area,3),
            'previousGshhgAreaPx2':round(original.area,3),
            'symmetricDifferencePx2':round(sibling.symmetric_difference(original).area,3),
            'projectedSourceIslands':len(polygons(sibling)),
            'protectedNationalPathsExact':after==approved,'canvas':[1200,760],
            'candidateSha256':hashlib.sha256(candidate.encode()).hexdigest()}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
