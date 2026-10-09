#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
rows = []
for path in sorted(COUNTRY_DIR.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    slug = data.get("slug", path.stem)
    name = data.get("nameJa", slug)
    transport = data.get("transport")
    flags = []
    if not isinstance(transport, dict):
        flags.append("missing_transport")
        title = text = ""
    else:
        title = str(transport.get("title", "")).strip()
        text = str(transport.get("text", "")).strip()
        if not title:
            flags.append("missing_title")
        if not text:
            flags.append("missing_text")
        if len(title) < 6:
            flags.append("short_title")
        if len(text) < 35:
            flags.append("short_text")
        if title and not any(k in title for k in ("鉄道","列車","電車","地下鉄","バス","車","レンタカー","タクシー","フェリー","船","飛行機","航空","徒歩","自転車","国内線","道路","移動")):
            flags.append("title_without_mode")
        if text and not any(k in text for k in ("鉄道","列車","電車","地下鉄","バス","車","レンタカー","タクシー","フェリー","船","飛行機","航空","徒歩","自転車","国内線","道路","4WD","ボート","乗合")):
            flags.append("text_without_mode")
    source_dates = data.get("sourceDates") or {}
    sources = data.get("sources") or {}
    if isinstance(transport, dict):
        if "transport" not in source_dates:
            flags.append("missing_transport_source_date")
        if "transport" not in sources:
            flags.append("missing_transport_source")
    if flags:
        rows.append({"slug":slug,"nameJa":name,"flags":flags,"transport":transport})

print(json.dumps({"countryCount": len(list(COUNTRY_DIR.glob('*.json'))), "candidateCount": len(rows)}, ensure_ascii=False))
print("TRANSPORT_CANDIDATES_BEGIN")
for row in rows:
    print(json.dumps(row, ensure_ascii=False, separators=(",",":")))
print("TRANSPORT_CANDIDATES_END")
