#!/usr/bin/env python3
"""Temporary cross-sectional Taste audit plus existing regression assertions."""
import hashlib
import json
from collections import defaultdict
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
structural = []
review = []
rows = []
hashes = defaultdict(list)

for slug in slugs:
    path = ROOT / "data" / "countries" / f"{slug}.json"
    if not path.exists():
        structural.append([slug, "COUNTRY_JSON_MISSING"])
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    taste = data.get("taste")
    if not isinstance(taste, dict):
        structural.append([slug, "TASTE_MISSING"])
        continue
    items = taste.get("items")
    if not isinstance(items, list):
        structural.append([slug, "ITEMS_MISSING"])
        continue
    if len(items) != 4:
        structural.append([slug, f"ITEM_COUNT:{len(items)}"])

    seen = {"id": {}, "name": {}, "nameLocal": {}, "image": {}}
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            structural.append([slug, i, "ITEM_NOT_OBJECT"])
            continue
        flags = []
        for key in ("id", "name", "nameLocal", "text", "image"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                flags.append(f"MISSING_{key.upper()}")
        for key in seen:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                norm = " ".join(value.lower().split())
                if norm in seen[key]:
                    flags.append(f"DUPLICATE_{key.upper()}:FOOD{seen[key][norm]:02d}")
                else:
                    seen[key][norm] = i
        image = item.get("image")
        if isinstance(image, str) and image.strip():
            image_path = ROOT / image
            if not image_path.exists():
                flags.append("IMAGE_FILE_MISSING")
            elif image_path.is_file():
                try:
                    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
                    hashes[digest].append((slug, i, image))
                except OSError:
                    flags.append("IMAGE_READ_ERROR")
        if flags:
            structural.append([slug, i, item.get("name", ""), flags])

        text = item.get("text", "") if isinstance(item.get("text"), str) else ""
        if text and len(text.strip()) < 20:
            review.append([slug, i, item.get("name", ""), f"SHORT_TEXT:{len(text.strip())}"])
        rows.append([slug, i, item.get("name", ""), item.get("nameLocal", ""), text, image or ""])

for digest, refs in hashes.items():
    if len(refs) > 1:
        structural.append(["CROSS_TASTE_DUPLICATE_IMAGE", digest[:12], refs])

print("TASTE_AUDIT_SUMMARY=" + json.dumps({
    "published": len(slugs),
    "tasteItems": len(rows),
    "structural": structural,
    "review": review,
}, ensure_ascii=False))
for row in rows:
    print("TASTE|" + "|".join(str(x).replace("\n", " ") for x in row))

raise AssertionError("TASTE_CROSS_SECTION_AUDIT_COMPLETE")
