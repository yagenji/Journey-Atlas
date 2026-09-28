#!/usr/bin/env python3
"""Reconcile Singapore/Macau neighboring land from pinned, independently sourced geodata.

PR-only existing-Country migration. Offline; fail closed on changed snapshots,
ambiguous coasts or approved original SVGs. Does not edit national paths.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from io import BytesIO
from pathlib import Path
import cairosvg
from PIL import Image
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import polygonize, transform, unary_union
from shapely.strtree import STRtree

W,H=1200,760
SVG='{http://www.w3.org/2000/svg}'
SEA=('#eaf2f4','#dcebf0','#d0e3eb')
EXPECTED={
 'singapore_osm':'9753ba433e0956363152f68f8371999217adb2c7ffa49d114192b74bf6dcd4df',
 'macau_osm':'654ca2fb2c8f5b3fc192a075441bd2452c0c54b40be781ac9c1f3df9a18987ae',
 'singapore_sla':'9bbe462d3e2da7b67ccdd62e6cf8bfee3a237d0be48504f6c45983c21c15fff1',
 'macau_xiangzhou':'b573325d4d3474a8361e6407c2c96cf05f06028088e7fe295605abcb313904f0',
 'singapore_svg':'d23a4a7558863210fa90cbcaf2ed81d434770b7097e517ba9d7dbecfe0f4d065',
 'macau_svg':'bd4cda722a95f2ef07fce10e0d4809d812cb438528382a1247d98157fd957dce'}

def checked(path,key):
 raw=path.read_bytes();actual=hashlib.sha256(raw).hexdigest()
 if actual!=EXPECTED[key]:raise RuntimeError(f'{key}: snapshot SHA mismatch {actual}')
 return json.loads(raw)

def project(bounds):
 west,south,east,north=(bounds[k] for k in ('west','south','east','north'))
 factor=math.cos(math.radians((south+north)/2))
 scale=min(W/((east-west)*factor),H/(north-south))
 ox=(W-(east-west)*factor*scale)/2;oy=(H-(north-south)*scale)/2
 return lambda lon,lat:(ox+(lon-west)*factor*scale,oy+(north-lat)*scale)

def coast_land(raw,xy,slug):
 ways=[LineString([xy(v['lon'],v['lat']) for v in way.get('geometry',[])])
       for way in raw['elements'] if way.get('type')=='way'
       and way.get('tags',{}).get('natural')=='coastline'
       and len(way.get('geometry',[]))>1]
 if len(ways)!={'singapore':699,'macau':315}[slug]:raise RuntimeError('Missing coastline ways')
 viewport=box(-50,-50,1250,810)
 segments=[v.intersection(viewport) for v in ways if v.intersects(viewport)]
 faces=list(polygonize(unary_union([viewport.boundary,*segments])))
 if len(faces)!={'singapore':123,'macau':21}[slug]:raise RuntimeError('Unexpected coast topology')
 index=STRtree(faces);hits=[Counter() for _ in faces]
 for geometry in segments:
  for line in ([geometry] if geometry.geom_type=='LineString' else geometry.geoms):
   for (x,y),(xx,yy) in zip(line.coords,line.coords[1:]):
    length=math.hypot(xx-x,yy-y)
    if length<1e-5:continue
    mx,my=(x+xx)/2,(y+yy)/2;eps=.0005
    # Land is on the left in WGS84; pixel-Y inversion yields a screen-up offset.
    left=Point(mx+(yy-y)*eps/length,my-(xx-x)*eps/length)
    right=Point(mx-(yy-y)*eps/length,my+(xx-x)*eps/length)
    for pt,kind in ((left,'land'),(right,'water')):
     for pos in index.query(pt):
      if faces[int(pos)].covers(pt):hits[int(pos)][kind]+=1
 result=[]
 for face,h in zip(faces,hits):
  if bool(h['land'])==bool(h['water']):raise RuntimeError(f'Ambiguous coast side {h}')
  if h['land']:result.append(face)
 return result

def sla_classes(data,xy):
 sg=[];my=[]
 for item in data['features']:
  if item['properties'].get('FOLDERPATH')!='Layers/Coastal_Outlines':continue
  name=item['properties'].get('NAME') or ''
  geom=transform(lambda x,y,z=None:xy(x,y),shape(item['geometry']))
  if not geom.is_valid:geom=geom.buffer(0)
  if 'JOHOR' in name:my.append(geom)
  elif not name.startswith('LINKWAY') and 'CAUSEWAY' not in name:sg.append(geom)
 if len(sg)<60 or len(my)<10:raise RuntimeError('Incomplete SLA Singapore/Johor source')
 return unary_union(sg),unary_union(my)

def xiangzhou(data,xy):
 parts={}
 for role in ('outer','inner'):
  edges=[LineString([xy(pt['lon'],pt['lat']) for pt in member['geometry']])
         for member in data['members'] if member['role']==role]
  polygons=list(polygonize(unary_union(edges)))
  if not polygons:raise RuntimeError('Unclosed Xiangzhou '+role)
  parts[role]=unary_union(polygons)
 district=parts['outer'].difference(parts['inner'])
 if not district.is_valid:raise RuntimeError('Invalid Xiangzhou district')
 return district

def draw_path(geom):
 parts=[]
 polys=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
 for poly in polys:
  if poly.area<.2:continue
  for ring in (poly.exterior,*poly.interiors):
   pts=[]
   for x,y in ring.coords:
    point=(round(x,1),round(y,1))
    if not pts or pts[-1]!=point:pts.append(point)
   if len(pts)>=3:parts.append('M '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+' Z')
 if not parts:raise RuntimeError('Empty contextual land')
 return ' '.join(parts)

def target_paths(root):
 parents={child:parent for parent in root.iter() for child in parent};result=[]
 for node in root.iter(SVG+'path'):
  p=node
  while p is not None and 'fill' not in p.attrib:p=parents.get(p)
  if p is not None and p.attrib.get('fill')=='url(#land)':result.append(node.attrib['d'])
 return result

def emit(source,slug,land,credit):
 text=source.read_text(encoding='utf-8')
 if hashlib.sha256(text.encode()).hexdigest()!=EXPECTED[slug+'_svg']:
  raise RuntimeError(f'{slug}: approved original SVG changed')
 original=ET.fromstring(text)
 if original.get('viewBox')!='0 0 1200 760' or original.find(".//*[@id='geographic-context']") is not None:raise RuntimeError('Unexpected SVG')
 approved=target_paths(original)
 if len(approved)!={'singapore':5,'macau':1}[slug]:raise RuntimeError('Unexpected approved target count')
 for before,after in zip(('#eef2ef','#e4eceb','#dce7e7'),SEA):text=text.replace(before,after)
 sea='<rect width="1200" height="760" fill="url(#sea)"/>'
 if text.count(sea)!=1:raise RuntimeError('Unexpected ocean rectangle')
 context='<g id="geographic-context"><desc>'+credit+'</desc><path d="'+draw_path(land)+'" fill="#e4e0ce" fill-rule="evenodd" stroke="#b6bbaf" stroke-width="0.65" stroke-linecap="round" stroke-linejoin="round"/></g>'
 text=text.replace(sea,sea+'\n'+context,1)
 rendered=ET.fromstring(text)
 if target_paths(rendered)!=approved:raise RuntimeError('Original country path changed')
 image=Image.open(BytesIO(cairosvg.svg2png(bytestring=text.encode(),output_width=W,output_height=H)))
 image.load()
 if image.size!=(W,H):raise RuntimeError('Decoded image dimensions invalid')
 source.write_text(text,encoding='utf-8')
 print(slug,'original',EXPECTED[slug+'_svg'],'generated',hashlib.sha256(text.encode()).hexdigest(),'PNG_DECODE_OK',image.size,flush=True)

def main():
 args=argparse.ArgumentParser(description=__doc__)
 for key in ('repo','coast','sla','xiangzhou'):args.add_argument('--'+key,type=Path,required=True)
 a=args.parse_args();root=a.repo.resolve()
 sj=json.loads((root/'data/countries/singapore.json').read_text())
 mj=json.loads((root/'data/countries/macau.json').read_text())
 sxy=project(sj['map']['bounds']);mxy=project(mj['map']['bounds'])
 sla=checked(a.sla,'singapore_sla')
 sg_osm=checked(a.coast/'singapore/ways.json','singapore_osm')
 mc_osm=checked(a.coast/'macau/ways.json','macau_osm')
 district=checked(a.xiangzhou,'macau_xiangzhou')
 official_sg,official_my=sla_classes(sla,sxy)
 singapore_land=coast_land(sg_osm,sxy,'singapore')
 foreign=[];excluded=0;malaysia=0
 for polygon in singapore_land:
  if polygon.area<.35:continue
  if polygon.intersection(official_sg).area/polygon.area>=.05:excluded+=1
  else:
   foreign.append(polygon)
   if polygon.intersection(official_my).area/polygon.area>.5:malaysia+=1
 if excluded<35 or malaysia<2:raise RuntimeError('Singapore islands/foreign mainland classification incomplete')
 sg_land=unary_union(foreign).intersection(box(0,0,W,H))
 mc_land=unary_union(coast_land(mc_osm,mxy,'macau')).intersection(xiangzhou(district,mxy)).intersection(box(0,0,W,H))
 if not sg_land.is_valid or not mc_land.is_valid:raise RuntimeError('Invalid source land')
 print('excluded Singapore islands',excluded,'Malaysia components',malaysia,'foreign land pixels',round(sg_land.area),'Zhuhai land pixels',round(mc_land.area),flush=True)
 emit(root/'assets/images/singapore/map-atlas-v1.svg','singapore',sg_land,'Foreign land: OpenStreetMap coastline ways (2026-09-20), ODbL 1.0. Singapore Land Authority National Map Polygon June 2025 (Singapore Open Data Licence) classifies and excludes Singapore islands; approved original outlines unchanged. https://www.openstreetmap.org/copyright https://data.gov.sg/datasets/d_29f066d67df3eae91df8a42f443863c8/view')
 emit(root/'assets/images/macau/map-atlas-v1.svg','macau',mc_land,'Zhuhai land: OpenStreetMap coastline ways (2026-09-20) intersect Xiangzhou district relation 5405551 (2026-09-21), ODbL 1.0. Approved original Macao SAR outline unchanged. https://www.openstreetmap.org/copyright')

if __name__=='__main__':main()
