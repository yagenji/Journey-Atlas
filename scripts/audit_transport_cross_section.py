#!/usr/bin/env python3
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
MODE = re.compile(r"鉄道|列車|電車|地下鉄|メトロ|バス|車|レンタカー|タクシー|配車|フェリー|船|飛行機|航空|徒歩|自転車|国内線|道路|4WD|ボート|乗合|トラム|路面電車|モノレール|ロープウェイ")
GENERIC_TIP = re.compile(r"事前に確認|最新情報を確認|余裕を持|注意する|気をつけ")
report={"transport":[],"tips":[],"nextRoutes":[],"relatedCountries":[]}
for path in sorted(COUNTRY_DIR.glob("*.json")):
    d=json.loads(path.read_text(encoding="utf-8")); slug=d.get("slug",path.stem)
    t=d.get("transport"); flags=[]
    if not isinstance(t,dict): flags=["missing"]
    else:
        title=str(t.get("title","")).strip(); text=str(t.get("text","")).strip()
        if not title: flags.append("missing_title")
        if not text: flags.append("missing_text")
        if len(text)<35: flags.append("short_text")
        if not MODE.search(title+text): flags.append("no_mode")
    if flags: report["transport"].append({"slug":slug,"flags":flags,"value":t})

    tips=d.get("tips"); flags=[]
    if not isinstance(tips,list) or not tips: flags=["missing"]
    else:
        if len(tips)!=3: flags.append(f"count_{len(tips)}")
        seen=set()
        for i,x in enumerate(tips):
            x=x or {}; title=str(x.get("title","")).strip(); text=str(x.get("text","")).strip(); key=str(x.get("topicKey","")).strip()
            if not title or not text or not key: flags.append(f"item{i+1}_missing_field")
            if len(text)<35: flags.append(f"item{i+1}_short")
            if (title,text) in seen: flags.append(f"item{i+1}_duplicate")
            seen.add((title,text))
        if all(GENERIC_TIP.search(str((x or {}).get("text",""))) for x in tips): flags.append("all_generic_check_advice")
    if flags: report["tips"].append({"slug":slug,"flags":sorted(set(flags)),"value":tips})

    nr=d.get("nextRoutes"); flags=[]
    if not isinstance(nr,list): flags=["not_list"]
    else:
        seen=set()
        for i,x in enumerate(nr):
            x=x or {}; vals=[str(x.get(k,"")).strip() for k in ("flag","countryEn","countryJa","path","description")]
            if not all(vals): flags.append(f"item{i+1}_missing_field")
            key=tuple(vals[1:3])
            if key in seen: flags.append(f"item{i+1}_duplicate_country")
            seen.add(key)
            if vals[4] and len(vals[4])<30: flags.append(f"item{i+1}_short_description")
    if flags: report["nextRoutes"].append({"slug":slug,"flags":sorted(set(flags)),"value":nr,"source":(d.get("sources") or {}).get("nextRoutes")})

    rc=d.get("relatedCountries"); flags=[]
    if not isinstance(rc,list) or not rc: flags=["missing"]
    else:
        seen=set()
        for i,x in enumerate(rc):
            x=x or {}; rslug=str(x.get("slug","")).strip()
            if not all(str(x.get(k,"")).strip() for k in ("slug","nameEn","nameJa","flag","reason")): flags.append(f"item{i+1}_missing_field")
            if rslug==slug: flags.append(f"item{i+1}_self")
            if rslug in seen: flags.append(f"item{i+1}_duplicate")
            seen.add(rslug)
            if rslug and not (COUNTRY_DIR/f"{rslug}.json").exists(): flags.append(f"item{i+1}_missing_target:{rslug}")
    if flags: report["relatedCountries"].append({"slug":slug,"flags":sorted(set(flags)),"value":rc})

hist=Counter(f for x in report["transport"] for f in x["flags"])
print("TRANSPORT_HIST "+json.dumps(hist,ensure_ascii=False,sort_keys=True))
for key in ("transport","tips","nextRoutes","relatedCountries"):
    print(key.upper()+" "+json.dumps(report[key],ensure_ascii=False,separators=(",",":")))
