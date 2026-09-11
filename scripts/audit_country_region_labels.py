#!/usr/bin/env python3
"""Audit Country hero region labels against JOURNEY ATLAS region taxonomy."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]
TAXONOMY_PATH = ROOT / "data" / "region-taxonomy.json"

REGION_RE = re.compile(r"^(.+?) / (\d{1,2})°([NS])$")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def expected_region_by_iso2(taxonomy: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for region in taxonomy.get("regions", []):
        subregions = region.get("subregions") or []
        if subregions:
            for subregion in subregions:
                label = subregion.get("labelEn")
                for iso2 in subregion.get("iso2", []):
                    if iso2 in result:
                        raise ValueError(f"duplicate taxonomy assignment for {iso2}")
                    result[iso2] = label
        else:
            label = region.get("labelEn")
            for iso2 in region.get("iso2", []):
                if iso2 in result:
                    raise ValueError(f"duplicate taxonomy assignment for {iso2}")
                result[iso2] = label
    return result


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    slug_to_iso2: dict[str, str] = {}
    for registry_path in REGISTRY_PATHS:
        registry = load_json(registry_path)
        for row in registry.get("destinations", []):
            slug = row.get("slug")
            iso2 = row.get("iso2")
            if slug and iso2:
                slug_to_iso2[slug] = iso2
    expected_by_iso2 = expected_region_by_iso2(taxonomy)

    errors: list[str] = []
    checked = 0
    labels: dict[str, int] = {}

    for path in sorted(COUNTRY_DIR.glob("*.json")):
        data = load_json(path)
        if data.get("schemaVersion") != 2:
            continue
        checked += 1
        slug = data.get("slug") or path.stem
        iso2 = slug_to_iso2.get(slug)
        value = data.get("region")

        if not iso2:
            errors.append(f"{path.name}: slug {slug!r} is missing from destination registries")
            continue
        expected = expected_by_iso2.get(iso2)
        if not expected:
            errors.append(f"{path.name}: ISO2 {iso2} has no region-taxonomy assignment")
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path.name}: region is missing or empty; expected '{expected} / <latitude>°N|S'")
            continue

        match = REGION_RE.fullmatch(value.strip())
        if not match:
            errors.append(f"{path.name}: region {value!r} does not match '<taxonomy label> / <integer>°N|S'")
            continue

        label, degree_text, hemisphere = match.groups()
        labels[label] = labels.get(label, 0) + 1
        if label != expected:
            errors.append(f"{path.name}: region label '{label}' must be '{expected}' for ISO2 {iso2}")

        degree = int(degree_text)
        signed_lat = degree if hemisphere == "N" else -degree
        if not 0 <= degree <= 90:
            errors.append(f"{path.name}: invalid latitude {degree}°{hemisphere}")
            continue

        bounds = data.get("map", {}).get("bounds", {})
        north = bounds.get("north")
        south = bounds.get("south")
        if isinstance(north, (int, float)) and isinstance(south, (int, float)):
            # Region latitude is intentionally a rounded representative latitude,
            # so allow one degree of rounding tolerance around map bounds.
            if not (south - 1 <= signed_lat <= north + 1):
                errors.append(
                    f"{path.name}: latitude {degree}°{hemisphere} falls outside map bounds "
                    f"({south}..{north})"
                )

    print(f"Checked schemaVersion 2 Country files: {checked}")
    print("Region labels in use:")
    for label, count in sorted(labels.items()):
        print(f"  {label}: {count}")

    if errors:
        print(f"Region label audit failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Region label audit passed: all Country region labels match taxonomy and latitude format.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
