#!/usr/bin/env python3
"""Regression coverage for Country browser QA optional Taste contract."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = (ROOT / "scripts" / "qa_country_browser.py").read_text(encoding="utf-8")
MAP_QA = (ROOT / "scripts" / "validate_country_map_v6.py").read_text(encoding="utf-8")

assert 'qa.EXPECTED_COUNTS[".taste-card"] = taste_count' in WRAPPER
assert 'selector != "#taste-section"' in WRAPPER
assert 'scene.get("mapSurface", "land")' in MAP_QA
assert 'surface == "water"' in MAP_QA
print("Optional Taste / water Scene QA regression PASS")

spec = importlib.util.spec_from_file_location("published_audit", ROOT / "scripts" / "audit_published_countries.py")
audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(audit)

structural_codes = {
    "MISSING_ID", "MISSING_NAME", "MISSING_DESCRIPTION", "MISSING_IMAGE",
    "MISSING_MAP_LABEL", "MISSING_COORDINATES", "DUPLICATE_COORDINATES",
    "DUPLICATE_ID", "DUPLICATE_NAME", "DUPLICATE_MAP_LABEL", "DUPLICATE_IMAGE",
}
scene_count = 0
structural = []
country_review = []
for slug in audit.published_slugs():
    data = json.loads((ROOT / "data" / "countries" / f"{slug}.json").read_text(encoding="utf-8"))
    rows, country_flags = audit.scene_rows(slug, data)
    scene_count += len(rows)
    if country_flags:
        country_review.append([slug, country_flags])
    for row in rows:
        flags = [f for f in row["flags"] if f.split(":", 1)[0] in structural_codes]
        if flags:
            structural.append([slug, row["index"], row["name"], flags])

print("SCENES_STRUCTURAL_AUDIT=" + json.dumps({
    "published": len(audit.published_slugs()),
    "scenes": scene_count,
    "structural": structural,
    "countryReview": country_review,
}, ensure_ascii=False, separators=(",", ":")))
