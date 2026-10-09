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
    personas = d.get("personas")
    flags = []
    if not isinstance(personas, list):
        structural.append({"slug": slug, "nameJa": name, "flags": ["not_list"], "personas": personas})
        continue
    if len(personas) != 3:
        flags.append(f"count_{len(personas)}")
    seen = set()
    for i, item in enumerate(personas):
        item = item if isinstance(item, dict) else {}
        title = str(item.get("title", "")).strip()
        text = str(item.get("text", "")).strip()
        item_flags = []
        if not title: item_flags.append("missing_title")
        if not text: item_flags.append("missing_text")
        if title and len(title) < 6: item_flags.append("short_title")
        if text and len(text) < 20: item_flags.append("short_text")
        key = (title, text)
        if key in seen and title and text: item_flags.append("duplicate_within_country")
        seen.add(key)
        rows.append({"slug": slug, "nameJa": name, "index": i + 1, "title": title, "text": text, "flags": item_flags})
        flags.extend(f"item{i+1}_{f}" for f in item_flags)
    if flags:
        structural.append({"slug": slug, "nameJa": name, "flags": sorted(set(flags)), "personas": personas})

exact_text = defaultdict(list)
exact_pair = defaultdict(list)
title_count = Counter()
for r in rows:
    if r["text"]:
        exact_text[r["text"]].append((r["slug"], r["index"]))
    if r["title"] and r["text"]:
        exact_pair[(r["title"], r["text"])].append((r["slug"], r["index"]))
    if r["title"]:
        title_count[r["title"]] += 1

pair_repeats = [
    {"title": title, "text": text, "uses": uses}
    for (title, text), uses in exact_pair.items() if len(uses) > 1
]
text_repeats = [
    {"text": text, "uses": uses}
    for text, uses in exact_text.items() if len(uses) > 1
]
common_titles = [{"title": t, "count": c} for t, c in title_count.most_common() if c >= 8]

print(json.dumps({
    "countryCount": len(list(COUNTRY_DIR.glob('*.json'))),
    "personaCount": len(rows),
    "structuralCountryCount": len(structural),
    "exactPairRepeatCount": len(pair_repeats),
    "exactTextRepeatCount": len(text_repeats),
    "commonTitleCount": len(common_titles),
}, ensure_ascii=False))
print("PERSONA_STRUCTURAL " + json.dumps(structural, ensure_ascii=False, separators=(",", ":")))
print("PERSONA_PAIR_REPEATS " + json.dumps(pair_repeats, ensure_ascii=False, separators=(",", ":")))
print("PERSONA_TEXT_REPEATS " + json.dumps(text_repeats, ensure_ascii=False, separators=(",", ":")))
print("PERSONA_COMMON_TITLES " + json.dumps(common_titles, ensure_ascii=False, separators=(",", ":")))
