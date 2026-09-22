"""Migration-only Brunei/Sarawak reconciliation; approved national SVG is immutable.

Only the sourced GSHHG Malaysian mainland is pale. Pulau Muara Besar belongs
inside Brunei, so its GSHHG ring is not foreign context. The already-approved
Brunei SVG omits that island; adding it to the protected target requires separate
review and is NOT silently done by this migration.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

N='{http://www.w3.org/2000/svg}'
APPROVED_SHA='57fcee91d44f7d27052ba0ac96b209f0c465a447277d6dcdc970c4dec047978d'
TARGET_SHA='63b4004c45a49e06ce9fa46c78a7807d88bf4ce8b9b0d06c74dab9bd487a64fd'
GSHHG_SHA='b61c98a983cd8166e156e3f0791c2fb0da467d1f3070a998ea778716f666ef8f'


def rings(path):
    if re.search(r'(?<![A-Za-z])[CQSTA H V](?=[\s\d.,-])',path):
        raise ValueError('Brunei path commands changed')
    polygons=[]
    for chunk in re.split(r'(?=\bM\s)',path):
        pairs=[tuple(map(float,match)) for match in
               re.findall(r'(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',chunk)]
        if len(pairs)>3:
            polygon=Polygon(pairs)
            if not polygon.is_valid or polygon.area<=0:
                raise ValueError('Invalid original Brunei or source ring')
            polygons.append(polygon)
    return polygons


def path_data(poly):
    result=[]
    for ring in (poly.exterior,*poly.interiors):
        pairs=[(round(x,2),round(y,2)) for x,y in ring.coords]
        pairs=[p for i,p in enumerate(pairs) if not i or p!=pairs[i-1]]
        if len(pairs)>=4:
            result.append('M '+' L '.join(f'{x:.2f},{y:.2f}' for x,y in pairs)+' Z')
    return ' '.join(result)


def reconcile(svg:str, source_path:Path, resolution:str)->str:
    original=source_path.read_bytes()
    if hashlib.sha256(original).hexdigest()!=APPROVED_SHA or resolution!='i':
        raise ValueError('Brunei approved national source or GSHHG resolution changed')
    source=ET.fromstring(original)
    candidate=ET.fromstring(svg)
    original_targets=[p.get('d') for p in source.iter(N+'path') if p.get('fill')=='url(#country)']
    candidate_targets=[p.get('d') for p in candidate.iter(N+'path') if p.get('fill')=='url(#country)']
    if (len(original_targets)!=1 or original_targets!=candidate_targets
            or hashlib.sha256(original_targets[0].encode()).hexdigest()!=TARGET_SHA
            or candidate.get('viewBox')!='0 0 1200 760'):
        raise ValueError('Protected Brunei paths/canvas do not match approved source')
    context=candidate.find('.//*[@id="geographic-context"]')
    paths=list(context.iter(N+'path')) if context is not None else []
    if len(paths)!=1 or hashlib.sha256(paths[0].get('d','').encode()).hexdigest()!=GSHHG_SHA:
        raise ValueError('Brunei GSHHG candidate changed: independent geographic review required')
    generated=paths[0].get('d')
    source_rings=rings(generated)
    national_rings=rings(original_targets[0])
    if len(source_rings)!=2 or len(national_rings)!=2:
        raise ValueError('Brunei geometry component count changed')
    main=max(source_rings,key=lambda p:p.area)
    island=min(source_rings,key=lambda p:p.area)
    # Geographic check uses the independent Brunei government identification
    # of Pulau Muara Besar; do not color its offshore ring as Malaysia.
    if not (island.covers(Point(855,90)) and 400<island.area<500):
        raise ValueError('Domestic Pulau Muara Besar topology has changed')
    brunei=unary_union(national_rings)
    if not 191080<main.intersection(brunei).area<191110:
        raise ValueError('Brunei/Malaysia source overlap changed')
    diff=main.difference(brunei)
    if diff.is_empty or not diff.is_valid or diff.geom_type!='MultiPolygon':
        raise ValueError('Unverified Brunei/Malaysia foreign-land topology')
    components=sorted(diff.geoms,key=lambda p:p.area,reverse=True)
    foreign=components[0]
    slivers=components[1:]
    if not (420000<foreign.area<430000
            and sum(p.area for p in slivers)<20
            and all(p.distance(brunei)<0.02 for p in slivers)):
        raise ValueError('Unexpected foreign coast or unverified small islands')
    replacement=path_data(foreign)
    if not replacement or svg.count('d="'+generated+'"')!=1:
        raise ValueError('Generated context cannot be replaced safely')
    result=svg.replace('d="'+generated+'"','d="'+replacement+'"',1)
    label=('<desc>Malaysia Sarawak neighboring mainland: GSHHG 2.3.6 '
           'intermediate, WGS84, LGPL; clip against unchanged approved Brunei '
           'national source. Pulau Muara Besar is domestic, not Malaysian land. '
           'https://www.ngdc.noaa.gov/mgg/shorelines/shorelines.html</desc>')
    group='<g id="geographic-context">'
    if result.count(group)!=1:raise ValueError('Brunei context layout changed')
    result=result.replace(group,group+label,1)
    checked=ET.fromstring(result)
    if [p.get('d') for p in checked.iter(N+'path') if p.get('fill')=='url(#country)']!=original_targets:
        raise ValueError('Brunei approved national path was modified')
    return result
