#!/usr/bin/env python3
"""Validate JOURNEY ATLAS country JSON files without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REQUIRED_TOP_LEVEL = {
    "slug",
    "nameEn",
    "nameJa",
    "region",
    "hero",
    "map",
    "scenes",
    "encounters",
    "seasons",
    "transport",
    "personas",
    "facts",
    "tips",
    "relatedCountries",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_country(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: JSONを読み込めません: {exc}"]

    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        fail(errors, f"{path.name}: 必須キー不足: {', '.join(sorted(missing))}")

    slug = data.get("slug")
    if slug and path.stem != slug:
        fail(errors, f"{path.name}: slug '{slug}' とファイル名が一致しません")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        fail(errors, f"{path.name}: scenes が空です")
        return errors

    ids: set[str] = set()
    bounds = data.get("map", {}).get("bounds", {})
    north = bounds.get("north")
    south = bounds.get("south")
    west = bounds.get("west")
    east = bounds.get("east")

    if not all(isinstance(v, (int, float)) for v in (north, south, west, east)):
        fail(errors, f"{path.name}: map.bounds が不正です")
    elif not (north > south and east > west):
        fail(errors, f"{path.name}: map.bounds の大小関係が不正です")

    for index, scene in enumerate(scenes, 1):
        prefix = f"{path.name}: scene {index}"
        scene_id = scene.get("id")
        if not scene_id:
            fail(errors, f"{prefix}: id がありません")
        elif scene_id in ids:
            fail(errors, f"{prefix}: id '{scene_id}' が重複しています")
        else:
            ids.add(scene_id)

        for key in ("name", "nameLocal", "mapLabel", "description", "coordinates", "image"):
            if key not in scene:
                fail(errors, f"{prefix}: '{key}' がありません")

        coords = scene.get("coordinates", {})
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
            fail(errors, f"{prefix}: latitude が不正です")
        if not isinstance(lon, (int, float)) or not -180 <= lon <= 180:
            fail(errors, f"{prefix}: longitude が不正です")

        if all(isinstance(v, (int, float)) for v in (north, south, west, east, lat, lon)):
            if not (south <= lat <= north and west <= lon <= east):
                fail(errors, f"{prefix}: 座標が map.bounds の外です")

        image = scene.get("image", "")
        if not isinstance(image, str) or not image.strip():
            fail(errors, f"{prefix}: image が空です")

    if data.get("slug") == "iceland" and len(scenes) != 8:
        fail(errors, f"{path.name}: Icelandは8景で設計されていますが {len(scenes)} 件です")

    return errors


def main() -> int:
    paths = [Path(arg) for arg in sys.argv[1:]] if len(sys.argv) > 1 else sorted(COUNTRY_DIR.glob("*.json"))
    errors: list[str] = []
    for path in paths:
        errors.extend(validate_country(path))

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {len(paths)} country file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
