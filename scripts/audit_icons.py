#!/usr/bin/env python3
"""Audit JOURNEY ATLAS Country icon references against the shared SVG sprite."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
SPRITE_PATH = ROOT / "assets" / "icons" / "atlas-icons.svg"

# These fields are explicit requirements in the shared Country contract.
TRAVEL_SCALE_ICONS = ["city", "map", "compass"]
TRANSPORT_ICON = "road"

# These sections render an icon but intentionally support shared fallbacks.
OPTIONAL_ICON_SECTIONS = (
    "encounters",
    "signatureFacts",
    "atlasExtras",
    "seasons",
    "personas",
    "facts",
    "tips",
)


def sprite_ids() -> set[str]:
    text = SPRITE_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'<symbol\s+id="([a-z0-9-]+)"', text))


def walk_explicit_icons(value: object, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key == "icon":
                yield child_path, child
            yield from walk_explicit_icons(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_explicit_icons(child, f"{path}[{index}]")


def main() -> int:
    icons = sprite_ids()
    errors: list[str] = []
    explicit_usage: Counter[str] = Counter()
    fallback_usage: dict[str, list[str]] = defaultdict(list)
    checked = 0

    for country_path in sorted(COUNTRY_DIR.glob("*.json")):
        try:
            data = json.loads(country_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{country_path.name}: JSON parse failed: {exc}")
            continue

        # Legacy / placeholder data outside the current Country v2 renderer is not in scope.
        if data.get("schemaVersion") != 2:
            continue
        checked += 1

        for json_path, icon in walk_explicit_icons(data):
            if not isinstance(icon, str) or not icon.strip():
                errors.append(f"{country_path.name}: {json_path} is empty or not a string")
                continue
            icon = icon.strip()
            explicit_usage[icon] += 1
            if icon not in icons:
                errors.append(
                    f"{country_path.name}: {json_path} references missing sprite symbol '{icon}'"
                )

        trivia = data.get("travelTrivia") if isinstance(data.get("travelTrivia"), list) else []
        for index, item in enumerate(trivia, 1):
            if not isinstance(item, dict) or not isinstance(item.get("icon"), str) or not item.get("icon", "").strip():
                errors.append(f"{country_path.name}: travelTrivia[{index}] requires an explicit icon")

        travel_scale = data.get("travelScale") if isinstance(data.get("travelScale"), dict) else {}
        travel_items = travel_scale.get("items") if isinstance(travel_scale.get("items"), list) else []
        if travel_scale or travel_items:
            actual = [item.get("icon") if isinstance(item, dict) else None for item in travel_items]
            if actual != TRAVEL_SCALE_ICONS:
                errors.append(
                    f"{country_path.name}: travelScale icons must be {TRAVEL_SCALE_ICONS}, got {actual}"
                )

        transport = data.get("transport") if isinstance(data.get("transport"), dict) else {}
        if transport and transport.get("icon") != TRANSPORT_ICON:
            errors.append(
                f"{country_path.name}: transport.icon must be '{TRANSPORT_ICON}', got {transport.get('icon')!r}"
            )

        for section in OPTIONAL_ICON_SECTIONS:
            value = data.get(section)
            if isinstance(value, list):
                for index, item in enumerate(value, 1):
                    if isinstance(item, dict) and not item.get("icon"):
                        fallback_usage[section].append(f"{country_path.stem}[{index}]")

    print(f"Checked schemaVersion 2 Country files: {checked}")
    print(f"Shared sprite symbols: {len(icons)}")
    print(f"Explicit icon references: {sum(explicit_usage.values())}")
    print("Explicit icon IDs used:")
    for icon, count in sorted(explicit_usage.items()):
        print(f"  {icon}: {count}")

    print("Optional fallback usage (not an error):")
    for section in OPTIONAL_ICON_SECTIONS:
        values = fallback_usage.get(section, [])
        print(f"  {section}: {len(values)}")
        if values and len(values) <= 12:
            print("    " + ", ".join(values))

    if errors:
        print("Icon audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Icon audit passed: no missing required icons and no invalid explicit sprite references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
