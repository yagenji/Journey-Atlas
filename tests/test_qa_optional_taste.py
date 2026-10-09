#!/usr/bin/env python3
"""Temporary cross-sectional Travel Scale audit plus existing regression assertions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = (ROOT / "scripts" / "qa_country_browser.py").read_text(encoding="utf-8")
MAP_QA = (ROOT / "scripts" / "validate_country_map_v6.py").read_text(encoding="utf-8")

assert 'qa.EXPECTED_COUNTS[".taste-card"] = taste_count' in WRAPPER
assert 'selector != "#taste-section"' in WRAPPER
assert 'scene.get("mapSurface", "land")' in MAP_QA
assert 'surface == "water"' in MAP_QA

registry = json.loads((ROOT / "data" / "atlas-destinations.json").read_text(encoding="utf-8"))
slugs = [x["slug"] for x in registry.get("destinations", []) if x.get("atlasPublished")]
issues = []
rows = []

for slug in slugs:
    path = ROOT / "data" / "countries" / f"{slug}.json"
    if not path.exists():
        issues.append([slug, "COUNTRY_JSON_MISSING"])
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    scale = data.get("travelScale")
    if not isinstance(scale, dict):
        issues.append([slug, "TRAVEL_SCALE_MISSING"])
        continue
    items = scale.get("items")
    if not isinstance(items, list):
        issues.append([slug, "ITEMS_MISSING"])
        continue
    if len(items) != 3:
        issues.append([slug, f"ITEM_COUNT:{len(items)}"])
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            issues.append([slug, i, "ITEM_NOT_OBJECT"])
            continue
        duration = item.get("duration", "")
        title = item.get("title", "")
        text = item.get("text", "")
        route = ""
        if isinstance(text, str) and "例：" in text:
            route = text.split("例：", 1)[1].strip()
        flags = []
        if not route:
            flags.append("EXAMPLE_ROUTE_MISSING")
        else:
            nodes = [x.strip() for x in route.split("→") if x.strip()]
            if len(nodes) < 2:
                flags.append("ROUTE_TOO_SHORT")
            if len(nodes) >= 2 and nodes[0] != nodes[-1]:
                flags.append("OPEN_ROUTE_REVIEW")
        if not isinstance(duration, str) or not duration.strip():
            flags.append("DURATION_MISSING")
        if not isinstance(title, str) or not title.strip():
            flags.append("TITLE_MISSING")
        if not isinstance(text, str) or not text.strip():
            flags.append("TEXT_MISSING")
        if flags:
            issues.append([slug, i, duration, title, route, flags])
        rows.append([slug, i, duration, title, route])

print("TRAVEL_SCALE_AUDIT_SUMMARY=" + json.dumps({
    "published": len(slugs),
    "items": len(rows),
    "issues": issues,
}, ensure_ascii=False))
for row in rows:
    print("TRAVEL_SCALE|" + "|".join(str(x).replace("\n", " ") for x in row))

raise AssertionError("TRAVEL_SCALE_CROSS_SECTION_AUDIT_COMPLETE")
