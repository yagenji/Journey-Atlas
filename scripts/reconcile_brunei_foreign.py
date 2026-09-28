"""Migration-only Brunei/Sarawak reconciliation with source-pinned domestic PMB.

The existing mainland/Temburong target path stays exact. Pulau Muara Besar is
an explicitly added protected Brunei target sourced from current OSM coastline
way 28531951 v9 (2025-03-01, ODbL). Only sourced Malaysian/Sarawak mainland is
rendered as pale foreign context.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

N='{http://www.w3.org/2000/svg}'
ORIGINAL_TARGET_SHA='63b4004c45a49e06ce9fa46c78a7807d88bf4ce8b9b0d06c74dab9bd487a64fd'
PMB_TARGET_SHA='b638398ba246e951a88e590a4cfc2f557a5cc9ad1c85b948fe2c93fb55655fa1'
GSHHG_SHA='b61c98a983cd8166e156e3f0791c2fb0da467d1f3070a998ea778716f666ef8f'
PMB_OSM_RAW_SHA='dd1bb1fbab630eb793b2c855f678fbc5a01f5ff21c1bdfdaf1410577669993d3'


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
    if resolution!='i':
        raise ValueError('Brunei reviewed migration requires intermediate GSHHG resolution')
    source=ET.fromstring(source_path.read_bytes())
    candidate=ET.fromstring(svg)
    original_targets=[p.get('d') for p in source.iter(N+'path') if p.get('fill')=='url(#country)']
    candidate_targets=[p.get('d') for p in candidate.iter(N+'path') if p.get('fill')=='url(#country)']
    hashes=[hashlib.sha256(p.encode()).hexdigest() for p in original_targets]
    metadata=''.join(source.find(N+'metadata').itertext()) if source.find(N+'metadata') is not None else ''
    if (candidate.get('viewBox')!='0 0 1200 760'
            or len(original_targets)!=2 or original_targets!=candidate_targets
            or hashes!=[ORIGINAL_TARGET_SHA,PMB_TARGET_SHA]
            or 'OpenStreetMap way 28531951 version 9' not in metadata
            or 'ODbL 1.0' not in metadata or PMB_OSM_RAW_SHA not in metadata):
        raise ValueError('Protected Brunei target/canvas/provenance changed')
    context=candidate.find('.//*[@id="geographic-context"]')
    paths=list(context.iter(N+'path')) if context is not None else []
    if len(paths)!=1 or hashlib.sha256(paths[0].get('d','').encode()).hexdigest()!=GSHHG_SHA:
        raise ValueError('Brunei GSHHG candidate changed: independent geographic review required')
    generated=paths[0].get('d')
    source_rings=rings(generated)
    national_rings=[]
    for target in original_targets:
        national_rings.extend(rings(target))
    if len(source_rings)!=2 or len(national_rings)!=3:
        raise ValueError('Brunei geometry component count changed')
    main=max(source_rings,key=lambda p:p.area)
    old_pmb=min(source_rings,key=lambda p:p.area)
    pmb=rings(original_targets[1])[0]
    if not (pmb.covers(Point(855,90)) and 600<pmb.area<650
            and old_pmb.covers(Point(855,90)) and 400<old_pmb.area<500
            and old_pmb.intersection(pmb).area/old_pmb.area>.90
            and old_pmb.hausdorff_distance(pmb)<18):
        raise ValueError('Pulau Muara Besar source identity/topology changed')
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
           'intermediate, WGS84, LGPL; clipped against protected Brunei target. '
           'Pulau Muara Besar is protected domestic land sourced separately from '
           'OpenStreetMap way 28531951 v9, ODbL 1.0. '
           'https://www.ngdc.noaa.gov/mgg/shorelines/shorelines.html '
           'https://www.openstreetmap.org/copyright</desc>')
    group='<g id="geographic-context">'
    if result.count(group)!=1:raise ValueError('Brunei context layout changed')
    result=result.replace(group,group+label,1)
    checked=ET.fromstring(result)
    if [p.get('d') for p in checked.iter(N+'path') if p.get('fill')=='url(#country)']!=original_targets:
        raise ValueError('Brunei protected national geometry was modified')
    return result
