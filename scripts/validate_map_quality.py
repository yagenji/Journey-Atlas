#!/usr/bin/env python3
"""Validate atlas-v2 JOURNEY ATLAS map assets for published countries."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATH = ROOT / "data" / "atlas-destinations.json"
EXPECTED_VIEWBOX = "0 0 1200 760"
EXPECTED_STYLE = "journey-atlas-map-v1"
EXPECTED_QUALITY = "atlas-v2"


def published_paths() -> list[Path]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        COUNTRY_DIR / f"{item['slug']}.json"
        for item in registry.get("destinations", [])
        if item.get("atlasPublished") and (COUNTRY_DIR / f"{item['slug']}.json").exists()
    ]


def validate_country_map(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    map_data = data.get("map") if isinstance(data.get("map"), dict) else {}
    if map_data.get("qualityProfile") != EXPECTED_QUALITY:
        return []

    errors: list[str] = []
    source = map_data.get("svg")
    if not isinstance(source, str) or not source:
        return [f"{path.name}: atlas-v2 map.svg がありません"]

    svg_path = ROOT / source
    if not svg_path.exists():
        return [f"{path.name}: atlas-v2 map asset がありません: {source}"]

    try:
        root = ET.parse(svg_path).getroot()
    except Exception as exc:
        return [f"{path.name}: map SVG XML parse failure: {exc}"]

    if root.attrib.get("viewBox") != EXPECTED_VIEWBOX:
        errors.append(f"{path.name}: atlas-v2 viewBox は {EXPECTED_VIEWBOX} が必要です")
    if root.attrib.get("data-map-style") != EXPECTED_STYLE:
        errors.append(f"{path.name}: data-map-style={EXPECTED_STYLE} が必要です")
    if root.attrib.get("data-map-quality") != EXPECTED_QUALITY:
        errors.append(f"{path.name}: data-map-quality={EXPECTED_QUALITY} が必要です")
    if not root.attrib.get("aria-label"):
        errors.append(f"{path.name}: map SVG aria-label がありません")

    metadata = next((element for element in root if element.tag.endswith("metadata")), None)
    metadata_text = "" if metadata is None or metadata.text is None else metadata.text.strip()
    if not metadata_text:
        errors.append(f"{path.name}: map SVG metadata にgeometry sourceがありません")
    if not str(map_data.get("source") or "").strip():
        errors.append(f"{path.name}: map.source がありません")

    text_elements = [element for element in root.iter() if element.tag.endswith("text")]
    if text_elements:
        errors.append(f"{path.name}: map SVG本体にtext要素を埋め込まないでください")

    return errors


def main() -> int:
    args = sys.argv[1:]
    if args == ["--published"]:
        paths = published_paths()
    elif args:
        paths = [Path(arg) for arg in args]
    else:
        paths = sorted(path for path in COUNTRY_DIR.glob("*.json") if path.name != "index.json")

    errors: list[str] = []
    checked = 0
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if (data.get("map") or {}).get("qualityProfile") != EXPECTED_QUALITY:
            continue
        checked += 1
        errors.extend(validate_country_map(path))

    if errors:
        print("Map quality validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Map quality validation passed: {checked} atlas-v2 country file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
