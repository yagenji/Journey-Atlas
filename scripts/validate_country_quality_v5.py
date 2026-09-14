#!/usr/bin/env python3
"""Additional JOURNEY ATLAS Content QA v5 gates.

Content QA v5 adds two controls on top of the existing editorial validator:
1. Capital-name labels may not cover numbered Scene markers on the map.
2. Signature Facts must be reader-interest facts, with hard exceptions for
   generic World Heritage counts and ordinary forest-share statistics.

Existing v2-v4 Country files are intentionally not retroactively invalidated.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
CONTENT_QA_V5 = 5
MAP_WIDTH = 1200.0
MAP_HEIGHT = 760.0
SCENE_NUMBER_CLEARANCE_RADIUS = 16.0
CAPITAL_LABEL_EDGE_MARGIN = 4.0
HERITAGE_MINIMUM_COUNT = 25
FOREST_LOW_MAX = 10.0
FOREST_HIGH_MIN = 70.0
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")
HERITAGE_TERMS = ("世界遺産", "world heritage")


def text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def qa_version(data: dict[str, Any]) -> int:
    value = data.get("contentQaVersion", 1)
    return value if isinstance(value, int) else 1


def signature_haystack(item: dict[str, Any]) -> str:
    return " ".join(text(item.get(key)) for key in ("topicKey", "label", "value", "note")).lower()


def first_integer(value: object) -> int | None:
    match = re.search(r"(\d[\d,]*)", text(value))
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def percentages(item: dict[str, Any]) -> list[float]:
    haystack = " ".join(text(item.get(key)) for key in ("value", "note"))
    return [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", haystack)]


def validate_signature_interest(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = data.get("signatureFacts")
    if not isinstance(items, list):
        return

    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        owner = f"{filename}: signatureFacts[{index}]"
        reason = text(item.get("interestReason"))
        if len(reason) < 12:
            fail(
                errors,
                f"{owner}.interestReason is required in Content QA v5 and must explain why the number changes how a reader imagines the Country",
            )

        haystack = signature_haystack(item)
        if any(term in haystack for term in HERITAGE_TERMS):
            count = first_integer(item.get("value"))
            if item.get("exceptionalHeritageCount") is not True:
                fail(
                    errors,
                    f"{owner}: World Heritage count is not a default Signature Fact. Use another reader-interest number unless exceptionalHeritageCount:true is explicit.",
                )
            if count is None or count < HERITAGE_MINIMUM_COUNT:
                fail(
                    errors,
                    f"{owner}: World Heritage count must be exceptionally high (>= {HERITAGE_MINIMUM_COUNT}) to qualify for Signature Facts; got {text(item.get('value'))!r}",
                )

        if any(term.lower() in haystack for term in FOREST_TERMS):
            pcts = percentages(item)
            if item.get("exceptionalShare") is not True:
                fail(
                    errors,
                    f"{owner}: forest/woodland share is not a default Signature Fact. Use another number unless exceptionalShare:true is explicit.",
                )
            if not pcts:
                fail(errors, f"{owner}: forest/woodland Signature Fact must contain a percentage")
            moderate = [pct for pct in pcts if FOREST_LOW_MAX < pct < FOREST_HIGH_MIN]
            if moderate:
                fail(
                    errors,
                    f"{owner}: forest/woodland share {moderate} is not extreme enough for Signature Facts; use only <= {FOREST_LOW_MAX:g}% or >= {FOREST_HIGH_MIN:g}%",
                )


def region_contains(region: object, coordinates: object) -> bool:
    if not isinstance(region, dict) or not isinstance(coordinates, dict):
        return False
    bounds = region.get("bounds") if isinstance(region.get("bounds"), dict) else {}
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    north = bounds.get("north")
    south = bounds.get("south")
    west = bounds.get("west")
    east = bounds.get("east")
    if not all(isinstance(value, (int, float)) for value in (lat, lon, north, south, west, east)):
        return False
    return south <= lat <= north and west <= lon <= east


def resolve_region(map_data: dict[str, Any], coordinates: object, region_id: object) -> dict[str, Any] | None:
    regions = map_data.get("regions") if isinstance(map_data.get("regions"), list) else []
    if isinstance(region_id, str) and region_id:
        for region in regions:
            if isinstance(region, dict) and region.get("id") == region_id:
                return region
    for region in regions:
        if isinstance(region, dict) and region_contains(region, coordinates):
            return region
    return None


def numeric_offset(value: object) -> tuple[float, float]:
    if not isinstance(value, dict):
        return 0.0, 0.0
    x = value.get("x", 0)
    y = value.get("y", 0)
    return (
        float(x) if isinstance(x, (int, float)) else 0.0,
        float(y) if isinstance(y, (int, float)) else 0.0,
    )


def project_to_rect(
    coordinates: object,
    bounds: object,
    rect: tuple[float, float, float, float],
    offset: tuple[float, float],
) -> tuple[float, float] | None:
    if not isinstance(coordinates, dict) or not isinstance(bounds, dict):
        return None
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    north = bounds.get("north")
    south = bounds.get("south")
    west = bounds.get("west")
    east = bounds.get("east")
    if not all(isinstance(value, (int, float)) for value in (lat, lon, north, south, west, east)):
        return None
    longitude_range = float(east) - float(west)
    latitude_range = float(north) - float(south)
    if longitude_range <= 0 or latitude_range <= 0:
        return None
    rect_x, rect_y, rect_width, rect_height = rect
    midpoint_latitude = (float(south) + float(north)) / 2.0
    longitude_scale = math.cos(math.radians(midpoint_latitude))
    projected_width = longitude_range * longitude_scale
    projected_height = latitude_range
    if projected_width <= 0 or projected_height <= 0:
        return None
    canvas_scale = min(rect_width / projected_width, rect_height / projected_height)
    draw_width = projected_width * canvas_scale
    draw_height = projected_height * canvas_scale
    canvas_offset_x = rect_x + (rect_width - draw_width) / 2.0
    canvas_offset_y = rect_y + (rect_height - draw_height) / 2.0
    x = canvas_offset_x + (float(lon) - float(west)) * longitude_scale * canvas_scale + offset[0] / 100.0 * MAP_WIDTH
    y = canvas_offset_y + (float(north) - float(lat)) * canvas_scale + offset[1] / 100.0 * MAP_HEIGHT
    return x, y


def project_marker(item: dict[str, Any], map_data: dict[str, Any]) -> tuple[float, float] | None:
    coordinates = item.get("coordinates")
    offset = numeric_offset(item.get("mapOffset"))
    region = resolve_region(map_data, coordinates, item.get("mapRegion"))
    if region:
        rect_data = region.get("rect") if isinstance(region.get("rect"), dict) else {}
        rect = (
            float(rect_data.get("x", 0)),
            float(rect_data.get("y", 0)),
            float(rect_data.get("width", MAP_WIDTH)),
            float(rect_data.get("height", MAP_HEIGHT)),
        )
        return project_to_rect(coordinates, region.get("bounds"), rect, offset)
    return project_to_rect(
        coordinates,
        map_data.get("bounds"),
        (0.0, 0.0, MAP_WIDTH, MAP_HEIGHT),
        offset,
    )


def estimated_label_width(label: str) -> float:
    width = 10.0  # horizontal padding from CSS
    for character in label:
        code = ord(character)
        if character.isspace():
            width += 3.2
        elif code >= 0x3000:
            width += 9.8
        elif character.isupper():
            width += 6.4
        elif character.isdigit():
            width += 5.6
        else:
            width += 5.4
    return max(28.0, min(130.0, width))


def capital_label_rect(capital: dict[str, Any], point: tuple[float, float]) -> tuple[float, float, float, float]:
    x, y = point
    position = text(capital.get("labelPosition")) or "right"
    label_offset = numeric_offset(capital.get("labelOffset"))
    width = estimated_label_width(text(capital.get("nameJa")) or text(capital.get("nameEn")))
    height = 18.0
    center_y = y + label_offset[1]
    if position == "left":
        right = x - 14.0 + label_offset[0]
        left = right - width
    else:
        left = x + 14.0 + label_offset[0]
        right = left + width
    return left, center_y - height / 2.0, right, center_y + height / 2.0


def circle_intersects_rect(
    cx: float,
    cy: float,
    radius: float,
    rect: tuple[float, float, float, float],
) -> bool:
    left, top, right, bottom = rect
    closest_x = min(max(cx, left), right)
    closest_y = min(max(cy, top), bottom)
    return math.hypot(cx - closest_x, cy - closest_y) < radius


def validate_capital_label_collision(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    capital = data.get("capital")
    map_data = data.get("map")
    scenes = data.get("scenes")
    if not isinstance(capital, dict) or not isinstance(map_data, dict) or not isinstance(scenes, list):
        return

    position = text(capital.get("labelPosition")) or "right"
    if position not in {"left", "right"}:
        fail(errors, f"{filename}: capital.labelPosition must be 'left' or 'right' for map label QA")
        return
    label_offset = capital.get("labelOffset")
    if label_offset is not None:
        if not isinstance(label_offset, dict) or not all(isinstance(label_offset.get(axis, 0), (int, float)) for axis in ("x", "y")):
            fail(errors, f"{filename}: capital.labelOffset must be numeric x/y values")
            return
        if any(abs(float(label_offset.get(axis, 0))) > 80 for axis in ("x", "y")):
            fail(errors, f"{filename}: capital.labelOffset must stay within ±80px")

    capital_point = project_marker(capital, map_data)
    if not capital_point:
        return
    rect = capital_label_rect(capital, capital_point)
    left, top, right, bottom = rect
    if (
        left < CAPITAL_LABEL_EDGE_MARGIN
        or top < CAPITAL_LABEL_EDGE_MARGIN
        or right > MAP_WIDTH - CAPITAL_LABEL_EDGE_MARGIN
        or bottom > MAP_HEIGHT - CAPITAL_LABEL_EDGE_MARGIN
    ):
        fail(
            errors,
            f"{filename}: capital name label leaves the 1200×760 map canvas; adjust labelPosition / labelOffset without changing coordinates",
        )

    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            continue
        point = project_marker(scene, map_data)
        if not point:
            continue
        if circle_intersects_rect(point[0], point[1], SCENE_NUMBER_CLEARANCE_RADIUS, rect):
            fail(
                errors,
                f"{filename}: capital name label overlaps Scene {index} number marker. Keep real coordinates; resolve with capital.labelPosition / capital.labelOffset or minimal mapOffset.",
            )


def validate_data(data: dict[str, Any], filename: str, *, force: bool = False) -> list[str]:
    if not force and qa_version(data) < CONTENT_QA_V5:
        return []
    errors: list[str] = []
    validate_signature_interest(errors, filename, data)
    validate_capital_label_collision(errors, filename, data)
    return errors


def validate_path(path: Path, *, force: bool = False) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: cannot read JSON: {exc}"]
    return validate_data(data, path.name, force=force)


def main() -> int:
    args = sys.argv[1:]
    force = False
    if args and args[0] == "--force":
        force = True
        args = args[1:]
    paths = [Path(arg) for arg in args] if args else sorted(COUNTRY_DIR.glob("*.json"))
    errors: list[str] = []
    checked = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        if force or qa_version(data) >= CONTENT_QA_V5:
            checked += 1
            errors.extend(validate_data(data, path.name, force=True))
    if errors:
        print("Content QA v5: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Content QA v5: PASS ({checked} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
