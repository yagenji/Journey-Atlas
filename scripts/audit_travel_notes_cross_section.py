#!/usr/bin/env python3
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
rows = []
structural = []
for path in sorted(COUNTRY_DIR.glob("*.json")):
    d = json.loads(path.read_text(encoding="utf-8"))
    slug = d.get("slug", path.stem)
    name = d.get("nameJa", slug)
    tips = d.get("tips")
    flags = []
    if not isinstance(tips, list):
        structural.append({"slug": slug, "nameJa": name, "flags": ["not_list"], "tips": tips})
        continue
    if len(tips) != 3:
        flags.append(f"count_{len(tips)}")
    seen_keys = set()
    seen_pairs = set()
    for i, item in enumerate(tips):
        item = item if isinstance(item, dict) else {}
        key = str(item.get("topicKey", "")).strip()
        title = str(item.get("title", "")).strip()
        text = str(item.get("text", "")).strip()
        item_flags = []
        if not key: item_flags.append("missing_topicKey")
        if not title: item_flags.append("missing_title")
        if not text: item_flags.append("missing_text")
        if title and len(title) < 6: item_flags.append("short_title")
        if text and len(text) < 20: item_flags.append("short_text")
        if key and key in seen_keys: item_flags.append("duplicate_topicKey_within_country")
        seen_keys.add(key)
        pair = (title, text)
        if title and text and pair in seen_pairs: item_flags.append("duplicate_content_within_country")
        seen_pairs.add(pair)
        # Review candidates for volatile/operational claims that need freshness/source checking.
        volatile = []
        joined = title + " " + text
        for token in ["運休", "時刻", "料金", "予約", "ビザ", "査証", "入国", "国境", "危険レベル", "治安", "閉鎖", "休止", "現金", "カード", "SIM", "eSIM", "許可", "パーミット"]:
            if token in joined:
                volatile.append(token)
        if re.search(r"20(?:2[4-9]|3\d)年", joined):
            volatile.append("dated_claim")
        if volatile:
            item_flags.append("volatile:" + ",".join(sorted(set(volatile))))
        rows.append({"slug": slug, "nameJa": name, "index": i + 1, "topicKey": key, "title": title, "text": text, "flags": item_flags})
        flags.extend(f"item{i+1}_{f}" for f in item_flags if not f.startswith("volatile:"))
    if flags:
        structural.append({"slug": slug, "nameJa": name, "flags": sorted(set(flags)), "tips": tips})

text_uses = defaultdict(list)
pair_uses = defaultdict(list)
title_count = Counter()
for r in rows:
    if r["text"]:
        text_uses[r["text"]].append((r["slug"], r["index"]))
    if r["title"] and r["text"]:
        pair_uses[(r["title"], r["text"])].append((r["slug"], r["index"]))
    if r["title"]:
        title_count[r["title"]] += 1

pair_repeats = [{"title": k[0], "text": k[1], "uses": v} for k, v in pair_uses.items() if len(v) > 1]
text_repeats = [{"text": k, "uses": v} for k, v in text_uses.items() if len(v) > 1]
common_titles = [{"title": t, "count": c} for t, c in title_count.most_common() if c >= 8]
volatile = [r for r in rows if any(f.startswith("volatile:") for f in r["flags"])]

print(json.dumps({
    "countryCount": len(list(COUNTRY_DIR.glob('*.json'))),
    "tipCount": len(rows),
    "structuralCountryCount": len(structural),
    "exactPairRepeatCount": len(pair_repeats),
    "exactTextRepeatCount": len(text_repeats),
    "commonTitleCount": len(common_titles),
    "volatileCandidateCount": len(volatile),
}, ensure_ascii=False))
print("TRAVEL_NOTES_STRUCTURAL " + json.dumps(structural, ensure_ascii=False, separators=(",", ":")))
print("TRAVEL_NOTES_PAIR_REPEATS " + json.dumps(pair_repeats, ensure_ascii=False, separators=(",", ":")))
print("TRAVEL_NOTES_TEXT_REPEATS " + json.dumps(text_repeats, ensure_ascii=False, separators=(",", ":")))
print("TRAVEL_NOTES_COMMON_TITLES " + json.dumps(common_titles, ensure_ascii=False, separators=(",", ":")))
print("TRAVEL_NOTES_VOLATILE_BEGIN")
for r in volatile:
    print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))
print("TRAVEL_NOTES_VOLATILE_END")
