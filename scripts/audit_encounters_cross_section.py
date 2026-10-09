#!/usr/bin/env python3
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
rows=[]; structural=[]
for path in sorted(COUNTRY_DIR.glob("*.json")):
    d=json.loads(path.read_text(encoding="utf-8")); slug=d.get("slug",path.stem); name=d.get("nameJa",slug)
    items=d.get("encounters")
    flags=[]
    if not isinstance(items,list):
        structural.append({"slug":slug,"nameJa":name,"flags":["not_list"]}); continue
    if len(items)!=8: flags.append(f"count_{len(items)}")
    seen=set()
    for i,item in enumerate(items):
        item=item if isinstance(item,dict) else {}
        title=str(item.get("title","")).strip(); cat=str(item.get("category","")).strip(); icon=str(item.get("icon","")).strip(); f=[]
        if not title:f.append("missing_title")
        if not cat:f.append("missing_category")
        if not icon:f.append("missing_icon")
        if title and title in seen:f.append("duplicate_title_within_country")
        seen.add(title)
        rows.append({"slug":slug,"nameJa":name,"index":i+1,"title":title,"category":cat,"icon":icon,"flags":f})
        flags.extend(f"item{i+1}_{x}" for x in f)
    if flags: structural.append({"slug":slug,"nameJa":name,"flags":sorted(set(flags))})

uses=defaultdict(list); cats=Counter(); icons=Counter()
for r in rows:
    if r["title"]: uses[r["title"]].append((r["slug"],r["index"]))
    if r["category"]:cats[r["category"]]+=1
    if r["icon"]:icons[r["icon"]]+=1
repeats=[{"title":t,"uses":u} for t,u in uses.items() if len(u)>=4]
print(json.dumps({"countryCount":len(list(COUNTRY_DIR.glob('*.json'))),"encounterCount":len(rows),"structuralCountryCount":len(structural),"repeatedTitleCount":len(repeats)},ensure_ascii=False))
print("ENCOUNTERS_STRUCTURAL "+json.dumps(structural,ensure_ascii=False,separators=(",",":")))
print("ENCOUNTERS_REPEATED_TITLES "+json.dumps(repeats,ensure_ascii=False,separators=(",",":")))
print("ENCOUNTERS_CATEGORIES "+json.dumps(cats,ensure_ascii=False,separators=(",",":")))
print("ENCOUNTERS_ICONS "+json.dumps(icons,ensure_ascii=False,separators=(",",":")))
