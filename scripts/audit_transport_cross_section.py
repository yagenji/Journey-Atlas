#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
MODE = re.compile(r"鉄道|列車|電車|地下鉄|メトロ|バス|車|レンタカー|タクシー|配車|フェリー|船|飛行機|航空|徒歩|自転車|国内線|道路|4WD|ボート|乗合|トラム|路面電車|モノレール|ロープウェイ")
GENERIC_TIP = re.compile(r"事前に確認|最新情報を確認|余裕を持|注意する|気をつけ")

report = {"countryCount": 0, "transport": [], "tips": [], "nextRoutes": [], "relatedCountries": []}
for path in sorted(COUNTRY_DIR.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    report["countryCount"] += 1
    slug = data.get("slug", path.stem)
    name = data.get("nameJa", slug)

    t = data.get("transport")
    flags=[]
    if not isinstance(t, dict): flags.append("missing")
    else:
        title=str(t.get("title","")).strip(); text=str(t.get("text","")).strip()
        if not title: flags.append("missing_title")
        if not text: flags.append("missing_text")
        if len(text)<35: flags.append("short_text")
        if not MODE.search(title+text): flags.append("no_mode")
        if "transport" not in (data.get("sources") or {}): flags.append("no_source")
        if "transport" not in (data.get("sourceDates") or {}): flags.append("no_source_date")
    if flags: report["transport"].append({"slug":slug,"nameJa":name,"flags":flags,"value":t})

    tips=data.get("tips")
    flags=[]
    if not isinstance(tips,list) or not tips: flags.append("missing")
    else:
        if len(tips)!=3: flags.append(f"count_{len(tips)}")
        seen=set()
        for i,item in enumerate(tips):
            title=str((item or {}).get("title","")).strip(); text=str((item or {}).get("text","")).strip(); key=str((item or {}).get("topicKey","")).strip()
            if not title or not text or not key: flags.append(f"item{i+1}_missing_field")
            if len(text)<35: flags.append(f"item{i+1}_short")
            sig=(title,text)
            if sig in seen: flags.append(f"item{i+1}_duplicate")
            seen.add(sig)
        if all(GENERIC_TIP.search(str((x or {}).get("text",""))) for x in tips): flags.append("all_generic_check_advice")
    if flags: report["tips"].append({"slug":slug,"nameJa":name,"flags":sorted(set(flags)),"value":tips})

    nr=data.get("nextRoutes")
    flags=[]
    if not isinstance(nr,list): flags.append("not_list")
    else:
        if len(nr) not in (0,3): flags.append(f"count_{len(nr)}")
        seen=set()
        for i,item in enumerate(nr):
            vals=[str((item or {}).get(k,"")).strip() for k in ("flag","countryEn","countryJa","path","description")]
            if not all(vals): flags.append(f"item{i+1}_missing_field")
            key=vals[1:3]
            if tuple(key) in seen: flags.append(f"item{i+1}_duplicate_country")
            seen.add(tuple(key))
            if len(vals[4])<30: flags.append(f"item{i+1}_short_description")
    if flags: report["nextRoutes"].append({"slug":slug,"nameJa":name,"flags":sorted(set(flags)),"value":nr,"source":(data.get("sources") or {}).get("nextRoutes")})

    rc=data.get("relatedCountries")
    flags=[]
    if not isinstance(rc,list) or not rc: flags.append("missing")
    else:
        if len(rc)!=3: flags.append(f"count_{len(rc)}")
        seen=set()
        for i,item in enumerate(rc):
            rslug=str((item or {}).get("slug","")).strip(); reason=str((item or {}).get("reason","")).strip()
            if not all(str((item or {}).get(k,"")).strip() for k in ("slug","nameEn","nameJa","flag","reason")): flags.append(f"item{i+1}_missing_field")
            if rslug==slug: flags.append(f"item{i+1}_self")
            if rslug in seen: flags.append(f"item{i+1}_duplicate")
            seen.add(rslug)
            if len(reason)<30: flags.append(f"item{i+1}_short_reason")
            if rslug and not (COUNTRY_DIR/f"{rslug}.json").exists(): flags.append(f"item{i+1}_missing_target:{rslug}")
    if flags: report["relatedCountries"].append({"slug":slug,"nameJa":name,"flags":sorted(set(flags)),"value":rc})

out=ROOT/"horizontal-audit-report.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({k:(v if isinstance(v,int) else len(v)) for k,v in report.items()}, ensure_ascii=False))
