#!/usr/bin/env python3
"""Normalize Country hero region labels to JOURNEY ATLAS region taxonomy."""

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
REGION_LINE_RE = re.compile(r'^(\s*"region"\s*:\s*)"[^"]*"(,?\s*)$', re.MULTILINE)


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


def registry_slug_to_iso2() -> dict[str, str]:
    result: dict[str, str] = {}
    for registry_path in REGISTRY_PATHS:
        if not registry_path.exists():
            continue
        registry = load_json(registry_path)
        for row in registry.get("destinations", []):
            slug = row.get("slug")
            iso2 = row.get("iso2")
            if slug and iso2:
                result[slug] = iso2
    return result


def representative_latitude(data: dict) -> tuple[int, str]:
    bounds = data.get("map", {}).get("bounds", {})
    north = bounds.get("north")
    south = bounds.get("south")
    if not isinstance(north, (int, float)) or not isinstance(south, (int, float)):
        raise ValueError("map.bounds north/south are required to derive representative latitude")
    midpoint = (float(north) + float(south)) / 2.0
    # Avoid Python's bankers rounding so .5 is consistently rounded away from zero.
    degree = int(abs(midpoint) + 0.5)
    return degree, "N" if midpoint >= 0 else "S"


def normalized_region(data: dict, expected_label: str) -> str:
    current = data.get("region")
    if isinstance(current, str):
        match = REGION_RE.fullmatch(current.strip())
        if match:
            _label, degree_text, hemisphere = match.groups()
            return f"{expected_label} / {degree_text}°{hemisphere}"
    degree, hemisphere = representative_latitude(data)
    return f"{expected_label} / {degree}°{hemisphere}"


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    slug_to_iso2 = registry_slug_to_iso2()
    expected_by_iso2 = expected_region_by_iso2(taxonomy)

    changed: list[tuple[str, str, str]] = []
    errors: list[str] = []

    for path in sorted(COUNTRY_DIR.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if data.get("schemaVersion") != 2:
            continue
        slug = data.get("slug") or path.stem
        iso2 = slug_to_iso2.get(slug)
        if not iso2:
            errors.append(f"{path.name}: slug {slug!r} is missing from destination registries")
            continue
        expected = expected_by_iso2.get(iso2)
        if not expected:
            errors.append(f"{path.name}: ISO2 {iso2} has no taxonomy assignment")
            continue

        before = data.get("region")
        try:
            after = normalized_region(data, expected)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if before == after:
            continue

        def replacement(match: re.Match[str]) -> str:
            return f'{match.group(1)}"{after}"{match.group(2)}'

        new_text, count = REGION_LINE_RE.subn(replacement, text, count=1)
        if count != 1:
            errors.append(f"{path.name}: could not replace top-level region line safely")
            continue
        path.write_text(new_text, encoding="utf-8")
        changed.append((path.name, str(before), after))

    print(f"Normalized Country region labels: {len(changed)}")
    for name, before, after in changed:
        print(f"- {name}: {before!r} -> {after!r}")

    if errors:
        print(f"Normalization failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
