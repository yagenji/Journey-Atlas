#!/usr/bin/env python3
"""Validate the canonical JOURNEY ATLAS 201-destination scope."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "atlas-destinations.json"
SCOPE = ROOT / "data" / "atlas-scope.json"
REGIONS = ROOT / "data" / "region-taxonomy.json"
EXPECTED_COUNT = 201
REQUIRED_SPECIAL_ISO2 = {"TW", "HK", "MO", "AQ"}
CANONICAL_SLUG_EXCEPTIONS = {"hong-kong"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    registry = load(REGISTRY)
    scope = load(SCOPE)
    regions = load(REGIONS)

    destinations = registry.get("destinations", [])
    iso2 = [item.get("iso2") for item in destinations]
    slugs = [item.get("slug") for item in destinations]
    orders = [item.get("order") for item in destinations]

    if registry.get("count") != EXPECTED_COUNT:
        errors.append(f"atlas-destinations.json count must be {EXPECTED_COUNT}")
    if len(destinations) != EXPECTED_COUNT:
        errors.append(f"atlas-destinations.json must contain {EXPECTED_COUNT} destinations, found {len(destinations)}")
    if len(set(iso2)) != len(iso2):
        errors.append("atlas-destinations.json contains duplicate iso2 values")
    if len(set(slugs)) != len(slugs):
        errors.append("atlas-destinations.json contains duplicate slugs")
    if len(set(orders)) != len(orders):
        errors.append("atlas-destinations.json contains duplicate order values")
    if set(orders) != set(range(1, EXPECTED_COUNT + 1)):
        errors.append("destination order values must be exactly 1..201")

    declared_slug_exceptions = {
        item.get("slug")
        for item in registry.get("slugPolicy", {}).get("exceptions", [])
        if isinstance(item, dict) and isinstance(item.get("slug"), str)
    }
    if declared_slug_exceptions != CANONICAL_SLUG_EXCEPTIONS:
        errors.append(
            "slugPolicy.exceptions must declare exactly the existing Hong Kong route exception: hong-kong"
        )

    missing_special = sorted(REQUIRED_SPECIAL_ISO2 - set(iso2))
    if missing_special:
        errors.append("canonical registry is missing required travel destinations: " + ", ".join(missing_special))

    by_iso = {item.get("iso2"): item for item in destinations}
    for code in ("HK", "MO"):
        item = by_iso.get(code)
        if not item:
            continue
        if item.get("atlasPublished") is not True:
            errors.append(f"{code} must remain atlasPublished:true in the canonical 201 registry")
        if not item.get("href") or not item.get("image"):
            errors.append(f"{code} must retain its published href and hero image")
    if by_iso.get("HK", {}).get("slug") != "hong-kong":
        errors.append("Hong Kong must retain canonical published slug hong-kong")
    if by_iso.get("MO", {}).get("slug") != "macau":
        errors.append("Macao destination must retain canonical published slug macau")

    if scope.get("counts", {}).get("totalAtlasPages") != EXPECTED_COUNT:
        errors.append("atlas-scope.json counts.totalAtlasPages must be 201")
    for key in ("taiwan", "hongKong", "macao", "antarctica"):
        if scope.get("counts", {}).get(key) != 1:
            errors.append(f"atlas-scope.json counts.{key} must be 1")

    top_level_codes: list[str] = []
    for region in regions.get("regions", []):
        top_level_codes.extend(region.get("iso2", []))
    counts = Counter(top_level_codes)
    duplicate_region_codes = sorted(code for code, count in counts.items() if count != 1)
    if duplicate_region_codes:
        errors.append("region-taxonomy top-level membership must be exactly once per destination: " + ", ".join(duplicate_region_codes))
    if set(top_level_codes) != set(iso2):
        missing_from_regions = sorted(set(iso2) - set(top_level_codes))
        extra_in_regions = sorted(set(top_level_codes) - set(iso2))
        if missing_from_regions:
            errors.append("canonical destinations missing from region-taxonomy: " + ", ".join(missing_from_regions))
        if extra_in_regions:
            errors.append("region-taxonomy contains destinations outside canonical registry: " + ", ".join(extra_in_regions))

    asia = next((region for region in regions.get("regions", []) if region.get("id") == "asia"), None)
    if not asia:
        errors.append("region-taxonomy is missing Asia")
    else:
        asia_codes = asia.get("iso2", [])
        if len(asia_codes) != 49:
            errors.append(f"Asia must contain 49 destinations, found {len(asia_codes)}")
        for code in ("HK", "MO"):
            if code not in asia_codes:
                errors.append(f"Asia must contain {code}")

    if errors:
        print("Canonical destination scope validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Canonical destination scope PASS: 201 destinations; Asia 49; Hong Kong and Macao included.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
