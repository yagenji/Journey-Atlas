#!/usr/bin/env python3
"""Temporary Travel Scale cross-sectional audit plus existing regression assertions."""
import json
import re
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
counts = {"loop": 0, "open": 0, "non_arrow": 0, "missing_example": 0}

def clean_node(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r"[。．.!！?？、,;；:：]+$", "", value).strip()
    return value

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
        duration = item.get("duration", "") if isinstance(item, dict) else ""
        title = item.get("title", "") if isinstance(item, dict) else ""
        text = item.get("text", "") if isinstance(item, dict) else ""
        flags = []
        for key, value in (("duration", duration), ("title", title), ("text", text)):
            if not isinstance(value, str) or not value.strip():
                flags.append(f"MISSING_{key.upper()}")
        route = ""
        status = ""
        if isinstance(text, str):
            m = re.search(r"例[:：]\s*(.+)$", text)
            if not m:
                flags.append("MISSING_ROUTE_EXAMPLE")
                counts["missing_example"] += 1
                status = "MISSING"
            else:
                route = m.group(1).strip()
                route_expr = route.split("。", 1)[0].strip()
                if re.search(r"[→➡➜]", route_expr):
                    nodes = [clean_node(x) for x in re.split(r"\s*[→➡➜]\s*", route_expr) if clean_node(x)]
                    if len(nodes) < 2:
                        flags.append("ROUTE_TOO_SHORT")
                        status = "SHORT"
                    elif nodes[0] == nodes[-1]:
                        counts["loop"] += 1
                        status = "LOOP"
                    else:
                        counts["open"] += 1
                        flags.append("OPEN_ROUTE")
                        status = "OPEN"
                else:
                    counts["non_arrow"] += 1
                    flags.append("NON_ARROW_ROUTE")
                    status = "NON_ARROW"
        if flags:
            issues.append([slug, i, flags, duration, title, route])
        rows.append([slug, i, duration, title, route, status])

print("TRAVEL_SCALE_AUDIT_SUMMARY=" + json.dumps({
    "published": len(slugs),
    "items": len(rows),
    "counts": counts,
    "issues": issues,
}, ensure_ascii=False))
for row in rows:
    if row[-1] != "LOOP":
        print("TRAVEL_SCALE_REVIEW|" + "|".join(str(x).replace("\n", " ") for x in row))

raise AssertionError("TRAVEL_SCALE_CROSS_SECTION_AUDIT_COMPLETE")
