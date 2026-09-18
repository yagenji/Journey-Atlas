#!/usr/bin/env python3
"""One-off Honduras map QA repair from actual OSM coastline rings (ODbL).

Retains the mainland and Isla del Tigre. Restores Roatán and Cayos from real
coastline coordinates, anchoring Cayos on land; no fabricated land geometry.
Remove this script after the verified one-time Country map repair.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from shapely.geometry import LineString, Point
from shapely.ops import polygonize

ROOT = Path(__file__).resolve().parents[1]
COUNTRY = ROOT / 'data/countries/honduras.json'
MAP = ROOT / 'assets/images/honduras/map-atlas-v1.svg'
URLS = ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter')
QUERY = '[out:json][timeout:100];way["natural"="coastline"](15.89,-86.76,16.49,-86.14);(._;>;);out body;'
SVG_NS = 'http://www.w3.org/2000/svg'


def load_osm():
    payload = urllib.parse.urlencode({'data': QUERY}).encode('utf-8')
    for url in URLS:
        try:
            req = urllib.request.Request(url, data=payload, headers={'User-Agent': 'JourneyAtlasCountryMapQA/1.0 (Honduras single-use)'})
            with urllib.request.urlopen(req, timeout=120) as res:
                blob = res.read(9_000_000)
            if len(blob) > 8_999_999:
                raise ValueError('OSM response exceeded 9 MB')
            obj = json.loads(blob)
            if not obj.get('elements'):
                raise ValueError('No OSM elements')
            print('OSM source', url, 'elements', len(obj['elements']), flush=True)
            return obj
        except Exception as exc:
            print('OSM source failed:', url, repr(exc), flush=True)
    raise RuntimeError('Authoritative coastline not retrieved; no geometry will be invented.')


def get_islands(elements):
    nodes = {el['id']: (el['lon'], el['lat']) for el in elements if el['type']=='node'}
    lines = []
    for el in elements:
        if el['type'] != 'way' or el.get('tags', {}).get('natural') != 'coastline':
            continue
        coords = [nodes[n] for n in el['nodes'] if n in nodes]
        if len(coords) == len(el['nodes']) and len(coords) >= 2:
            lines.append(LineString(coords))
    polys = [p for p in polygonize(lines) if p.is_valid and p.area > 1e-9]
    print('OSM coastline ways',len(lines),'closed polygons',len(polys), flush=True)
    roatan = [p for p in polys if p.intersects(Point(-86.45, 16.36).buffer(0.09))
              and p.bounds[1] > 16.20 and p.bounds[3] < 16.49 and p.area > 0.0001]
    if not roatan:
        raise ValueError('No source-derived closed Roatan coastline polygon; refusing shape invention')
    roi = max(roatan,key=lambda p:p.area)
    cays = [p for p in polys if -86.61 < p.centroid.x < -86.42 and 15.89 < p.centroid.y < 16.05
            and p.area > 1e-8 and p is not roi]
    if not cays:
        raise ValueError('No source-derived closed Cayos Cochinos island polygon; refusing shape invention')
    mayor = max(cays,key=lambda p:p.area)
    if mayor.area < 0.00002:
        raise ValueError('Largest retrieved cay is implausibly small; inspect source rather than inventing geometry')
    print('Roatan geographic bounds', tuple(round(v,5) for v in roi.bounds),
          'Cayos polygons', len(cays), 'largest area degrees²', round(mayor.area,7), flush=True)
    return roi,cays,mayor


def projection(b):
    n,s,w,e = (b[k] for k in ('north','south','west','east'))
    lon_scale = math.cos(math.radians((n+s)/2))
    scale = min(1200 / ((e-w)*lon_scale),760/(n-s))
    ox = (1200 - (e-w)*lon_scale*scale)/2
    oy = (760 - (n-s)*scale)/2
    def project(lon,lat):
        return (ox+(lon-w)*lon_scale*scale, oy+(n-lat)*scale)
    return project


def svg_d(poly,project):
    coords = list(poly.exterior.coords)
    pieces = [f'{project(lon,lat)[0]:.1f},{project(lon,lat)[1]:.1f}' for lon,lat in coords[:-1]]
    return 'M '+' L '.join(pieces)+' Z'


def score_offset(scenes,b,selected):
    proj = projection(b)
    def pt(sc):
        c=sc['coordinates']; o=sc.get('mapOffset',{})
        x,y=proj(c['longitude'],c['latitude'])
        return x+o.get('x',0)*12,y+o.get('y',0)*7.6
    cur=selected.get('mapOffset',{'x':2.0,'y':0.0})
    candidates=[(x/2,y/2) for x in range(-10,11) for y in range(-10,11)
                if math.hypot(x/2,y/2)<=5.0]
    candidates.sort(key=lambda xy:(math.hypot(xy[0]-cur.get('x',0),xy[1]-cur.get('y',0)), math.hypot(*xy)))
    others=[(sc['id'],pt(sc)) for sc in scenes if sc is not selected]
    for dx,dy in candidates:
        selected['mapOffset']={'x':dx,'y':dy}
        x,y=pt(selected)
        if not 18 <= x <=1182 or not 18<=y<=742:continue
        if all(math.hypot(x-u,y-v)>=71.0 for _,(u,v) in others):
            print('Cayos label-only mapOffset',selected['mapOffset'],'minimum separation',
                  round(min(math.hypot(x-u,y-v) for _,(u,v) in others),2),flush=True)
            return
    raise ValueError('No legal Cayos marker-label offset avoids overlap')


def main():
    before_country=COUNTRY.read_bytes()
    before_svg=MAP.read_bytes()
    data=json.loads(before_country)
    if data.get('slug')!='honduras' or data['map']['svg']!='assets/images/honduras/map-atlas-v1.svg':
        raise ValueError('Incorrect target; refusing changes')
    if 'OpenStreetMap coastline' in before_svg.decode('utf-8'):
        raise ValueError('Map was already repaired; inspect rather than overwriting')
    scs=data['scenes']
    s01=next(s for s in scs if s['id']=='roatan-west-bay')
    s02=next(s for s in scs if s['id']=='cayos-cochinos')
    if s02['coordinates'] != {'latitude':15.9736,'longitude':-86.4785}:
        raise ValueError('Cayos anchor changed since preparation; refusing overwrite')
    roi,cays,mayor=get_islands(load_osm()['elements'])
    p=Point(s01['coordinates']['longitude'],s01['coordinates']['latitude'])
    project=projection(data['map']['bounds'])
    xx,yy=project(p.x,p.y)
    def px_distance(p,geo):
        q=geo.boundary.interpolate(geo.boundary.project(p))
        x2,y2=project(q.x,q.y)
        return math.hypot(xx-x2,yy-y2)
    d=px_distance(p,roi)
    if not roi.contains(p) and d>3.2:
        raise ValueError(f'West Bay true coordinate {d:.2f}px from OSM Roatan coastline, outside strict QA; inspect')
    print('West Bay OSM coastline interior',roi.contains(p),'boundary distance px',round(d,2),flush=True)
    anchor=mayor.representative_point()
    s02['coordinates']={'latitude':round(anchor.y,6),'longitude':round(anchor.x,6)}
    score_offset(scs,data['map']['bounds'],s02)
    data['map']['source']=('Basemap GSHHS intermediate-resolution mainland and Isla del Tigre, '
                          'with Roatán and Cayos Cochinos actual OpenStreetMap coastline ways '
                          '(© OpenStreetMap contributors, ODbL), projected from WGS84 at 1200×760; '
                          'Cayos Cochinos Scene anchor lies on actual Cayo Cochino Mayor land.')
    ET.register_namespace('',SVG_NS)
    root=ET.fromstring(before_svg)
    paths=root.findall(f'{{{SVG_NS}}}path')
    if len(paths)!=3 or not paths[1].attrib.get('d','').startswith('M 562.1,71.3'):
        raise ValueError('Unexpected Honduras map paths; refusing target changes')
    paths[1].set('d',svg_d(roi,project))
    insert_at=list(root).index(paths[2])
    for cay in sorted(cays,key=lambda p:p.area,reverse=True):
        if cay.area < 4e-8: continue
        el=ET.Element(f'{{{SVG_NS}}}path', {'d':svg_d(cay,project),
                          'fill':'url(#land)', 'stroke':'#31576a', 'stroke-width':'1.1',
                          'stroke-linejoin':'round','stroke-linecap':'round'})
        root.insert(insert_at,el); insert_at+=1
    meta=root.find(f'{{{SVG_NS}}}metadata')
    if meta is not None:
        meta.text=('Basemap GSHHS intermediate mainland and Natural Earth Isla del Tigre; '
                   'Roatán and Cayos Cochinos polygons are unshifted OpenStreetMap coastline rings '
                   '© OpenStreetMap contributors ODbL, accessed 2026-09-18. '
                   'WGS84, bounds N16.7 S12.8 W-89.5 E-82.9. The Cayos marker is anchored on Cayo Cochino Mayor.')
    new_svg=ET.tostring(root,encoding='unicode').replace(' />','/>')+'\n'
    new_json=json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
    MAP.write_text(new_svg,encoding='utf-8')
    COUNTRY.write_text(new_json,encoding='utf-8')
    try:
        subprocess.run([sys.executable,str(ROOT/'scripts/validate_country_map_v6.py'),str(COUNTRY)],check=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/validate_country.py'),'--strict',str(COUNTRY)],check=True)
    except Exception:
        MAP.write_bytes(before_svg);COUNTRY.write_bytes(before_country)
        raise
    print('PASS: source-derived geometry, two revised files only. Review SVG + Country JSON before committing.',flush=True)

if __name__=='__main__':main()
