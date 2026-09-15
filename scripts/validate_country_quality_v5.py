#!/usr/bin/env python3
"""Additional JOURNEY ATLAS Content QA v5/v6 gates.

Content QA v5 adds:
1. Capital-name labels may not cover numbered Scene markers on the map.
2. Signature Facts must be reader-interest facts, with hard exceptions for
   generic World Heritage counts and ordinary forest-share statistics.

Content QA v6 adds production-time selection gates so editorial mistakes are
caught once before visual production instead of repeatedly during review:
- stronger cross-section subject separation;
- fixed Taste heading contract;
- established NEXT ROUTES independent of temporary border status;
- affinity-based NEXT DESTINATIONS;
- broad, observable ENCOUNTERS;
- plain-language / exceptional Signature Facts;
- an additional map collision safety margin.

Existing v2-v4 Country files are intentionally not retroactively invalidated.
Existing v5 Country files keep v5 behavior unless intentionally migrated.
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
CONTENT_QA_V6 = 6
MAP_WIDTH = 1200.0
MAP_HEIGHT = 760.0
SCENE_NUMBER_CLEARANCE_RADIUS = 16.0
V6_SCENE_NUMBER_CLEARANCE_RADIUS = 20.0
V6_LABEL_SAFETY_MARGIN = 6.0
CAPITAL_LABEL_EDGE_MARGIN = 4.0
HERITAGE_MINIMUM_COUNT = 25
FOREST_LOW_MAX = 10.0
FOREST_HIGH_MIN = 70.0
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")
HERITAGE_TERMS = ("世界遺産", "world heritage")
GENERIC_PROFILE_TERMS = ("人口密度", "人口", "国土面積", "面積", "population density", "population", "area")
NEXT_ROUTE_STATUSES = {"OPEN", "TEMPORARILY_RESTRICTED", "SEASONAL", "CHECK_CURRENT_CONDITIONS"}
AFFINITY_TYPES = {
    "LANDSCAPE", "NATURE", "CULTURE", "CITY", "ARCHITECTURE", "HISTORY",
    "FOOD", "TRAVEL_STYLE", "MOUNTAIN", "DESERT", "ISLAND", "COAST", "WILDLIFE",
}
ENCOUNTER_CATEGORIES = {
    "LANDSCAPE", "NATURE", "CITY", "ARCHITECTURE", "DAILY_LIFE", "MOVEMENT",
    "FOOD", "WILDLIFE", "SEASON", "FAITH", "CULTURE", "LANGUAGE", "WORK",
}
TOPIC_NOISE = {
    "count", "counts", "number", "numbers", "share", "rate", "ratio", "percent",
    "percentage", "stat", "stats", "fact", "facts", "trivia", "history", "background",
    "overview", "story", "system", "culture", "context", "figure", "figures", "country",
    "national", "detail", "details", "today", "current",
}


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
    width = 10.0
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


def topic_tokens(value: str) -> set[str]:
    parts = [part for part in re.split(r"[-_\s]+", value.lower()) if part and part not in TOPIC_NOISE]
    normalized: set[str] = set()
    raw = set(parts)
    if "world" in raw and "heritage" in raw:
        normalized.add("worldheritage")
        raw.discard("world")
        raw.discard("heritage")
    if "silk" in raw and "road" in raw:
        normalized.add("silkroad")
        raw.discard("silk")
        raw.discard("road")
    aliases = {"woodland": "forest", "forests": "forest", "nomadic": "nomad", "nomads": "nomad", "unesco": "worldheritage"}
    for part in raw:
        normalized.add(aliases.get(part, part))
    return {part for part in normalized if len(part) >= 3}


def validate_cross_section_subject_overlap_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    records: list[tuple[str, str, set[str]]] = []
    for section in ("signatureFacts", "atlasExtras", "travelTrivia"):
        items = data.get(section)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            key = text(item.get("topicKey"))
            tokens = topic_tokens(key)
            if tokens:
                records.append((section, f"{section}[{index}]", tokens))
    for i, (section_a, owner_a, tokens_a) in enumerate(records):
        for section_b, owner_b, tokens_b in records[i + 1:]:
            if section_a == section_b:
                continue
            shared = tokens_a & tokens_b
            if not shared:
                continue
            union = tokens_a | tokens_b
            jaccard = len(shared) / max(1, len(union))
            subset_collision = tokens_a <= tokens_b or tokens_b <= tokens_a
            strong_single = len(shared) == 1 and subset_collision and len(next(iter(shared))) >= 5
            if len(shared) >= 2 or jaccard >= 0.60 or strong_single:
                fail(
                    errors,
                    f"{filename}: Content QA v6 detects likely subject reuse across {owner_a} and {owner_b}: shared topic tokens={sorted(shared)}. 数値 / 景色の向こうへ / トリビア must use different subjects.",
                )


def validate_taste_heading_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    taste = data.get("taste")
    if not isinstance(taste, dict):
        fail(errors, f"{filename}: Content QA v6 requires taste object")
        return
    expected_kicker = f"TASTE OF {text(data.get('nameEn')).upper()}"
    expected_title = f"{text(data.get('nameJa'))}で食べたいもの"
    if taste.get("kicker") != expected_kicker:
        fail(errors, f"{filename}: taste.kicker is fixed and must be {expected_kicker!r}")
    if taste.get("title") != expected_title:
        fail(errors, f"{filename}: taste.title is fixed and must be {expected_title!r}")


def validate_next_routes_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    routes = data.get("nextRoutes", [])
    if routes is None:
        routes = []
    if not isinstance(routes, list) or len(routes) > 3:
        fail(errors, f"{filename}: nextRoutes must be a list of 0–3 established traveler routes")
        return
    for index, route in enumerate(routes, 1):
        owner = f"{filename}: nextRoutes[{index}]"
        if not isinstance(route, dict):
            fail(errors, f"{owner} must be an object")
            continue
        if route.get("travelerRoute") is not True:
            fail(errors, f"{owner}.travelerRoute must be true; include routes because they are established traveler continuations, not because the border is currently open")
        status = text(route.get("status"))
        if status not in NEXT_ROUTE_STATUSES:
            fail(errors, f"{owner}.status must be one of {sorted(NEXT_ROUTE_STATUSES)}")
        if status != "OPEN" and len(text(route.get("statusNote"))) < 8:
            fail(errors, f"{owner}.statusNote is required when a representative route is temporarily restricted, seasonal, or needs current-condition checking")


def validate_related_countries_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = data.get("relatedCountries")
    if not isinstance(items, list) or len(items) != 3:
        fail(errors, f"{filename}: relatedCountries must contain exactly 3 affinity recommendations")
        return
    for index, item in enumerate(items, 1):
        owner = f"{filename}: relatedCountries[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{owner} must be an object")
            continue
        affinity = text(item.get("affinityType"))
        if affinity not in AFFINITY_TYPES:
            fail(errors, f"{owner}.affinityType must express why a fan of this Country may also like the recommendation; got {affinity!r}")
        if len(text(item.get("reason"))) < 18:
            fail(errors, f"{owner}.reason must explain the travel affinity, not mere geographic proximity")


def validate_encounters_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = data.get("encounters")
    if not isinstance(items, list) or len(items) != 8:
        fail(errors, f"{filename}: encounters must contain exactly 8 observable travel experiences")
        return
    categories: set[str] = set()
    for index, item in enumerate(items, 1):
        owner = f"{filename}: encounters[{index}]"
        if not isinstance(item, dict):
            fail(errors, f"{owner} must be an object")
            continue
        title = text(item.get("title"))
        category = text(item.get("category"))
        if not title:
            fail(errors, f"{owner}.title is required")
        if len(title) > 22:
            fail(errors, f"{owner}.title is too specific/long for ENCOUNTERS; use a directly imaginable, broadly representative expression")
        if any(mark in title for mark in ("（", "(", " / ")):
            fail(errors, f"{owner}.title should not need parenthetical or slash explanation; move explanation-heavy local terms to Beyond the Scenery / Trivia")
        if category not in ENCOUNTER_CATEGORIES:
            fail(errors, f"{owner}.category must be one of {sorted(ENCOUNTER_CATEGORIES)}")
        else:
            categories.add(category)
    if len(categories) < 4:
        fail(errors, f"{filename}: encounters must span at least 4 distinct categories; got {sorted(categories)}")


def validate_signature_plain_meaning_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    items = data.get("signatureFacts")
    if not isinstance(items, list):
        return
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        owner = f"{filename}: signatureFacts[{index}]"
        label = text(item.get("label"))
        value = text(item.get("value"))
        note = text(item.get("note"))
        reason = text(item.get("interestReason"))
        if len(label) > 16:
            fail(errors, f"{owner}.label must be short enough for a reader to understand the metric at a glance")
        if not re.search(r"\d", value):
            fail(errors, f"{owner}.value must contain an immediately readable number")
        if len(note) < 18:
            fail(errors, f"{owner}.note must explain in plain language what the number means for the Country")
        if len(reason) < 18:
            fail(errors, f"{owner}.interestReason must explain why this number is distinctive enough to occupy one of only three slots")
        haystack = signature_haystack(item)
        if any(term.lower() in haystack for term in GENERIC_PROFILE_TERMS):
            if item.get("exceptionalScale") is not True:
                fail(errors, f"{owner}: ordinary population/area/density figures are not Signature Facts. Use exceptionalScale:true only when the scale itself is genuinely distinctive.")


def validate_capital_label_collision_v6(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    capital = data.get("capital")
    map_data = data.get("map")
    scenes = data.get("scenes")
    if not isinstance(capital, dict) or not isinstance(map_data, dict) or not isinstance(scenes, list):
        return
    capital_point = project_marker(capital, map_data)
    if not capital_point:
        return
    left, top, right, bottom = capital_label_rect(capital, capital_point)
    rect = (
        left - V6_LABEL_SAFETY_MARGIN,
        top - V6_LABEL_SAFETY_MARGIN,
        right + V6_LABEL_SAFETY_MARGIN,
        bottom + V6_LABEL_SAFETY_MARGIN,
    )
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            continue
        point = project_marker(scene, map_data)
        if not point:
            continue
        if circle_intersects_rect(point[0], point[1], V6_SCENE_NUMBER_CLEARANCE_RADIUS, rect):
            fail(errors, f"{filename}: Content QA v6 safety margin: capital name label is too close to Scene {index} number marker. Resolve before visual production with labelPosition / labelOffset / minimal mapOffset, never coordinate mutation.")


def validate_v6_additions(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    validate_cross_section_subject_overlap_v6(errors, filename, data)
    validate_taste_heading_v6(errors, filename, data)
    validate_next_routes_v6(errors, filename, data)
    validate_related_countries_v6(errors, filename, data)
    validate_encounters_v6(errors, filename, data)
    validate_signature_plain_meaning_v6(errors, filename, data)
    validate_capital_label_collision_v6(errors, filename, data)


def validate_data(data: dict[str, Any], filename: str, *, force: bool = False) -> list[str]:
    version = qa_version(data)
    if not force and version < CONTENT_QA_V5:
        return []
    errors: list[str] = []
    validate_signature_interest(errors, filename, data)
    validate_capital_label_collision(errors, filename, data)
    if version >= CONTENT_QA_V6:
        validate_v6_additions(errors, filename, data)
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
        version = qa_version(data)
        if force or version >= CONTENT_QA_V5:
            checked += 1
            errors.extend(validate_data(data, path.name, force=True))
    if errors:
        print("Content QA v5/v6: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Content QA v5/v6: PASS ({checked} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
