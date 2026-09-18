#!/usr/bin/env python3
"""One-off, narrowly scoped Honduras Country JSON QA corrections.
Run from the Journey-Atlas repository root on the country/honduras branch.
This script must not be committed; only data/countries/honduras.json is changed.
"""
from pathlib import Path
import hashlib, json, math, subprocess

ROOT=Path.cwd()
PATH=ROOT/'data/countries/honduras.json'
EXPECTED_BLOB='fdc07cfb1d7f8ba859e8777a50686ca50c8fec25'
if not PATH.is_file():
 raise SystemExit('Missing data/countries/honduras.json: run from repository root.')
original=PATH.read_bytes()
blob=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
if blob!=EXPECTED_BLOB:
 raise SystemExit(f'Country JSON differs from reviewed GitHub version; expected {EXPECTED_BLOB}, got {blob}. Do not overwrite; request fresh QA.')
data=json.loads(original)
assert data['slug']=='honduras' and data['schemaVersion']==2
assert data['map']['bounds']=={'north':16.7,'south':12.8,'west':-89.5,'east':-82.9}
assert [s['id'] for s in data['scenes']]==[
 'roatan-west-bay','cayos-cochinos','rio-cangrejal-pico-bonito',
 'comayagua-cathedral','lake-yojoa','gracias-celaque',
 'pulhapanzak-falls','isla-del-tigre-amapala']

# Visual-label offsets only; leave actual latitude/longitude and SVG geometry unchanged.
corrections={
 'cayos-cochinos':{'x':2.0,'y':0.0},
 'lake-yojoa':{'x':0.0,'y':1.0},
 'pulhapanzak-falls':{'x':0.0,'y':-4.5},
}
for scene in data['scenes']:
 if scene['id'] in corrections:
  assert 'mapOffset' not in scene or scene['mapOffset']==corrections[scene['id']]
  scene['mapOffset']=corrections[scene['id']]

# SourcesVerifiedAt is the retrieval date; sourceDates describes the period
# represented by the value. Do not label an undated static area as a 2026 fact.
periods=data['sourceDates'];sources=data['sources']
assert periods['population']=='2025 UN estimate'
assert periods['area']=='UNData country profile, checked 2026-09-18'
assert periods['religion']=='2020 CID Gallup poll cited by US Department of State 2023 report'
assert periods['travelAdvisory']=='2026-08-25'
assert {'population','area','languageReligion','security'}<=set(sources)
periods['population']='2025'
del periods['area']
periods['languageReligion']=periods.pop('religion').split()[0]
periods['security']=periods.pop('travelAdvisory')
assert all(k in sources for k in periods)
assert all(__import__('re').fullmatch(r'\d{4}(?:-(?:Q[1-4]|\d{2}(?:-\d{2})?))?',v) for v in periods.values())

# Recalculate the common 1200×760 map marker rule for the full 8-Scene set.
b=data['map']['bounds'];n,s,w,e=b['north'],b['south'],b['west'],b['east']
cos=math.cos(math.radians((n+s)/2))
scale=min(1200/((e-w)*cos),760/(n-s))
xpad=(1200-(e-w)*cos*scale)/2
ypad=(760-(n-s)*scale)/2
points=[]
for scene in data['scenes']:
 p=scene['coordinates']; off=scene.get('mapOffset',{})
 assert math.hypot(float(off.get('x',0)),float(off.get('y',0)))<=5
 x=xpad+(p['longitude']-w)*cos*scale+off.get('x',0)*12
 y=ypad+(n-p['latitude'])*scale+off.get('y',0)*7.6
 assert 18<=x<=1200-18 and 18<=y<=760-18,(scene['id'],x,y)
 points.append((scene['id'],x,y))
for i,(a,x,y) in enumerate(points):
 for c,X,Y in points[i+1:]:
  distance=math.hypot(x-X,y-Y)
  assert distance>=71,(a,c,distance)

# Preserve whole Country data; only three mapOffsets and sourceDates are edited.
PATH.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print('PASS: Updated',PATH,'; eight marker separations >=71px, geographic coordinates untouched.')
print('PASS: Population period 2025; religion 2020 under source languageReligion; security 2026-08-25.')
print('NOTE: Static area has no sourced measurement date; optional sourceDates.area removed, source area retained.')
print('Now run: python3 scripts/validate_country.py --strict data/countries/honduras.json')
