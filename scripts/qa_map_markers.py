#!/usr/bin/env python3
"""QA marker spacing for JOURNEY ATLAS maps using the same linear projection as app.js."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATH = ROOT / "data" / "atlas-destinations.json"
WIDTH = 1200.0
HEIGHT = 760.0
MIN_MARKER_DISTANCE_PX = 42.0
MAX_OFFSET_PERCENT = 5.0
MAX_OFFSET_VECTOR_PERCENT = 5.5
EDGE_CLEARANCE_PX = 12.0


def published_paths() -> list[Path]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        COUNTRY_DIR / f"{item['slug']}.json"
        for item in registry.get("destinations", [])
        if item.get("atlasPublished") and (COUNTRY_DIR / f"{item['slug']}.json").exists()
    ]


def offset_for(item: dict) -> tuple[float, float]:
    offset = item.get("mapOffset") if isinstance(item.get("mapOffset"), dict) else {}
    return float(offset.get("x", 0) or 0), float(offset.get("y", 0) or 0)


def project(item: dict, bounds: dict) -> tuple[float, float]:
    coords = item.get("coordinates") or {}
    lat = float(coords["latitude"])
    lon = float(coords["longitude"])
    ox, oy = offset_for(item)
    x = (lon - bounds["west"]) / (bounds["east"] - bounds["west"]) * WIDTH + ox / 100.0 * WIDTH
    y = (bounds["north"] - lat) / (bounds["north"] - bounds["south"]) * HEIGHT + oy / 100.0 * HEIGHT
    return x, y


def marker_items(data: dict) -> list[tuple[str, dict]]:
    items: list[tuple[str, dict]] = []
    if isinstance(data.get("capital"), dict):
        items.append(("capital", data["capital"]))
    if isinstance(data.get("hero"), dict):
        items.append(("hero", data["hero"]))
    for index, scene in enumerate(data.get("scenes") or [], 1):
        if isinstance(scene, dict):
            items.append((f"scene-{index}:{scene.get('id', '')}", scene))
    return items


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    map_data = data.get("map") if isinstance(data.get("map"), dict) else {}
    # atlas-v2 countries opt into strict marker QA. New country scaffolds set this automatically.
    if int(map_data.get("markerQaVersion") or 0) < 1:
        return []

    errors: list[str] = []
    bounds = map_data.get("bounds") or {}
    items = marker_items(data)
    points: list[tuple[str, float, float]] = []

    for label, item in items:
        ox, oy = offset_for(item)
        if abs(ox) > MAX_OFFSET_PERCENT or abs(oy) > MAX_OFFSET_PERCENT:
            errors.append(f"{path.name}: {label} mapOffset は各軸 ±{MAX_OFFSET_PERCENT:.0f}%以内にしてください: ({ox}, {oy})")
        if math.hypot(ox, oy) > MAX_OFFSET_VECTOR_PERCENT:
            errors.append(f"{path.name}: {label} mapOffset の補正量が大きすぎます: ({ox}, {oy})")
        try:
            x, y = project(item, bounds)
        except Exception as exc:
            errors.append(f"{path.name}: {label} を投影できません: {exc}")
            continue
        if not (EDGE_CLEARANCE_PX <= x <= WIDTH - EDGE_CLEARANCE_PX and EDGE_CLEARANCE_PX <= y <= HEIGHT - EDGE_CLEARANCE_PX):
            errors.append(f"{path.name}: {label} が地図端に近すぎます: ({x:.1f}, {y:.1f})")
        points.append((label, x, y))

    for index, (label_a, x_a, y_a) in enumerate(points):
        for label_b, x_b, y_b in points[index + 1:]:
            distance = math.hypot(x_a - x_b, y_a - y_b)
            if distance < MIN_MARKER_DISTANCE_PX:
                errors.append(
                    f"{path.name}: marker collision {label_a} / {label_b}: {distance:.1f}px < {MIN_MARKER_DISTANCE_PX:.0f}px. "
                    "実座標は変えず mapOffset で最小補正してください"
                )

    svg_source = map_data.get("svg")
    if map_data.get("qualityProfile") == "atlas-v2" and isinstance(svg_source, str):
        svg_path = ROOT / svg_source
        if not svg_path.exists():
            errors.append(f"{path.name}: atlas-v2 map asset がありません: {svg_source}")
        else:
            head = svg_path.read_text(encoding="utf-8")[:800]
            if 'viewBox="0 0 1200 760"' not in head:
                errors.append(f"{path.name}: atlas-v2 map は viewBox 0 0 1200 760 が必要です")
            if 'data-map-quality="atlas-v2"' not in head:
                errors.append(f"{path.name}: atlas-v2 map に data-map-quality=\"atlas-v2\" がありません")

    return errors


def main() -> int:
    args = sys.argv[1:]
    if args == ["--published"]:
        paths = published_paths()
    elif args:
        paths = [Path(arg) for arg in args]
    else:
        paths = sorted(COUNTRY_DIR.glob("*.json"))

    errors: list[str] = []
    checked = 0
    for path in paths:
        if path.name == "index.json" or not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if int((data.get("map") or {}).get("markerQaVersion") or 0) < 1:
            continue
        checked += 1
        errors.extend(validate(path))

    if errors:
        print("Map marker QA failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Map marker QA passed: {checked} atlas-v2 country file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
