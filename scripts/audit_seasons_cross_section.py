#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; COUNTRY_DIR=ROOT/'data'/'countries'
LARGE_VARIATION={'argentina','australia','brazil','canada','chile','china','india','indonesia','kazakhstan','russia','unitedstates'}
REGION_HINTS=('北部','南部','東部','西部','内陸','沿岸','海岸','高地','山岳','地域','地方','島','北','南','東','西')
def norm(v): return re.sub(r'\s+','',str(v or '')).replace('～','〜').replace('-','〜')
def expand_range(a,b):
 out={a}; c=a
 while c!=b:
  c=c%12+1; out.add(c)
  if len(out)>12: break
 return out
def parse_months(raw):
 t=norm(raw)
 if not t:return set()
 if any(x in t for x in ('通年','一年中','年間')):return set(range(1,13))
 nums=[int(x) for x in re.findall(r'(?<!\d)(1[0-2]|[1-9])(?=月|〜|・|,|、|/|$)',t)]
 m=re.search(r'(1[0-2]|[1-9])月?〜(1[0-2]|[1-9])月',t)
 if m:return expand_range(int(m.group(1)),int(m.group(2)))
 return set(nums) if nums else None
def expected(lat,label):
 if abs(lat)<15:return None
 n={'春':{3,4,5},'夏':{6,7,8},'秋':{9,10,11},'冬':{12,1,2}}
 s={'春':{9,10,11},'夏':{12,1,2},'秋':{3,4,5},'冬':{6,7,8}}
 return (n if lat>=0 else s).get(label)
def capital_lat(p):
 try:return float(p['capital']['coordinates']['latitude'])
 except Exception:
  vals=[]
  for sc in p.get('scenes') or []:
   try: vals.append(float(sc['coordinates']['latitude']))
   except Exception: pass
  return sum(vals)/len(vals) if vals else 0.0
def audit(path):
 p=json.loads(path.read_text(encoding='utf-8')); slug=p.get('slug') or path.stem; seasons=p.get('seasons'); flags=[]; lat=capital_lat(p)
 if not isinstance(seasons,list): seasons=[]; flags.append('seasons_not_list')
 if len(seasons)!=4: flags.append(f'season_count_{len(seasons)}')
 month_keys=[]; text_keys=[]; parsed=[]
 for i,item in enumerate(seasons,1):
  if not isinstance(item,dict): flags.append(f'item_{i}_not_object'); parsed.append(None); continue
  months=str(item.get('months') or '').strip(); color=str(item.get('color') or '').strip(); text=str(item.get('text') or '').strip()
  if not months: flags.append(f'item_{i}_missing_months')
  if not color: flags.append(f'item_{i}_missing_color')
  if not text: flags.append(f'item_{i}_missing_text')
  month_keys.append(norm(months)); text_keys.append(norm(text)); ms=parse_months(months); parsed.append(ms)
  for label in ('春','夏','秋','冬'):
   if label in text:
    exp=expected(lat,label)
    if exp is not None and ms and ms.isdisjoint(exp): flags.append(f'item_{i}_{label}_hemisphere_mismatch')
 if len(month_keys)!=len(set(month_keys)): flags.append('duplicate_month_label')
 if len(text_keys)!=len(set(text_keys)): flags.append('duplicate_text')
 if parsed and all(x is not None for x in parsed):
  counts={m:0 for m in range(1,13)}
  for ms in parsed:
   for m in ms: counts[m]+=1
  gaps=[m for m,c in counts.items() if c==0]; overlaps=[m for m,c in counts.items() if c>1]
  if gaps: flags.append('month_gaps:'+','.join(map(str,gaps)))
  if overlaps: flags.append('month_overlaps:'+','.join(map(str,overlaps)))
 combined=' '.join(str(x.get('text') or '') for x in seasons if isinstance(x,dict))
 if abs(lat)<15 and all(x in combined for x in ('春','夏','秋','冬')): flags.append('tropical_four_season_framing')
 if slug in LARGE_VARIATION and not any(h in combined for h in REGION_HINTS): flags.append('large_country_no_regional_qualifier')
 return {'slug':slug,'nameJa':p.get('nameJa'),'lat':round(lat,3),'seasons':seasons},sorted(set(flags))
def main():
 rows=[]; cand=[]; structural=[]
 for path in sorted(COUNTRY_DIR.glob('*.json')):
  row,flags=audit(path); rows.append(row)
  if flags:
   c={'slug':row['slug'],'nameJa':row['nameJa'],'flags':flags,'seasons':row['seasons']}; cand.append(c)
   if any(f.startswith(('seasons_','season_count_','item_','duplicate_','month_gaps','month_overlaps')) for f in flags): structural.append(c)
 print(json.dumps({'countryCount':len(rows),'seasonItemCount':sum(len(r['seasons']) for r in rows),'candidateCount':len(cand),'structuralCandidateCount':len(structural)},ensure_ascii=False))
 print('SEASON_CANDIDATES_BEGIN')
 for x in cand: print(json.dumps(x,ensure_ascii=False,separators=(',',':')))
 print('SEASON_CANDIDATES_END')
 return 0
if __name__=='__main__': raise SystemExit(main())
