#!/usr/bin/env python3
"""Regression coverage for Country browser QA optional Taste contract."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = (ROOT / "scripts" / "qa_country_browser.py").read_text(encoding="utf-8")
MAP_QA = (ROOT / "scripts" / "validate_country_map_v6.py").read_text(encoding="utf-8")

assert 'qa.EXPECTED_COUNTS[".taste-card"] = taste_count' in WRAPPER
assert 'selector != "#taste-section"' in WRAPPER
assert 'scene.get("mapSurface", "land")' in MAP_QA
assert 'surface == "water"' in MAP_QA

spec = importlib.util.spec_from_file_location("published_audit", ROOT / "scripts" / "audit_published_countries.py")
audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(audit)

structural_codes = {
    "MISSING_ID", "MISSING_NAME", "MISSING_DESCRIPTION", "MISSING_IMAGE",
    "MISSING_MAP_LABEL", "MISSING_COORDINATES", "DUPLICATE_COORDINATES",
    "DUPLICATE_ID", "DUPLICATE_NAME", "DUPLICATE_MAP_LABEL", "DUPLICATE_IMAGE",
}
counts = Counter()
review_rows = []
for slug in audit.published_slugs():
    data = json.loads((ROOT / "data" / "countries" / f"{slug}.json").read_text(encoding="utf-8"))
    rows, _ = audit.scene_rows(slug, data)
    for row in rows:
        editorial_flags = [f for f in row["flags"] if f.split(":", 1)[0] not in structural_codes]
        if editorial_flags:
            for flag in editorial_flags:
                counts[flag.split(":", 1)[0]] += 1
            review_rows.append([slug, row["index"], row["name"], editorial_flags])

raise AssertionError("SCENES_EDITORIAL_AUDIT=" + json.dumps({
    "counts": dict(sorted(counts.items())),
    "rows": review_rows,
}, ensure_ascii=False, separators=(",", ":")))