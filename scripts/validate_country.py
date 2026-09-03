#!/usr/bin/env python3
"""Validate JOURNEY ATLAS country data and production prerequisites."""

from __future__ import annotations

import base64
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]

REQUIRED_TOP_LEVEL = {
    "slug", "nameEn", "nameJa", "region", "hero", "map", "scenes",
    "encounters", "seasons", "transport", "personas", "facts", "tips",
    "relatedCountries",
}
STRICT_REQUIRED = {
    "schemaVersion", "seo", "capital", "atlasExtras", "travelTrivia",
    "signatureFacts", "updatedAt", "sourcesVerifiedAt", "sourceDates", "sources",
}
COMMON_FACT_LABELS = ["地域", "首都", "人口", "面積", "言語", "主な宗教", "通貨"]

MAP_WIDTH = 1200
MAP_HEIGHT = 760
MAX_MARKER_OFFSET_PERCENT = 5.0
MARKER_EDGE_MARGIN = {"scene": 18.0, "hero": 18.0, "capital": 18.0}



def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_asset(errors: list[str], owner: str, source: object) -> None:
    if not isinstance(source, str) or not source.strip():
        fail(errors, f"{owner}: asset path が空です")
        return
    path = ROOT / source
    if not path.exists():
        fail(errors, f"{owner}: asset がありません: {source}")
        return

    if source.endswith(".parts.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            parts = manifest.get("parts") or []
            if not parts:
                fail(errors, f"{owner}: manifest parts が空です")
                return
            encoded_chunks: list[str] = []
            for part in parts:
                part_path = ROOT / part
                if not part_path.exists():
                    fail(errors, f"{owner}: image part がありません: {part}")
                    continue
                encoded_chunks.append(part_path.read_text(encoding="utf-8"))
            encoded = "".join("".join(encoded_chunks).split())
            signature = manifest.get("signature")
            if signature and encoded and not encoded.startswith(signature):
                fail(errors, f"{owner}: manifest signature が一致しません")
            if encoded:
                base64.b64decode(encoded, validate=True)
        except Exception as exc:
            fail(errors, f"{owner}: manifestを復元できません: {exc}")

    if source.endswith(".b64"):
        try:
            encoded = "".join(path.read_text(encoding="utf-8").split())
            base64.b64decode(encoded, validate=True)
        except Exception as exc:
            fail(errors, f"{owner}: base64 asset を復元できません: {exc}")


def validate_map_svg_clean(errors: list[str], filename: str, source: object) -> None:
    if not isinstance(source, str) or not source.endswith(".svg"):
        return
    path = ROOT / source
    if not path.exists():
        return
    try:
        svg = path.read_text(encoding="utf-8")
    except Exception as exc:
        fail(errors, f"{filename}: map SVGを読み込めません: {exc}")
        return

    if "<ellipse" in svg:
        fail(errors, f"{filename}: country map SVG に <ellipse> は使用できません（背景の白い楕円アーティファクト防止）")
    if "<radialGradient" in svg:
        fail(errors, f"{filename}: country map SVG に radialGradient は使用できません（背景ムラ防止）")


def normalized_editorial_title(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE).casefold()


def validate_content_topic_keys(errors: list[str], filename: str, data: dict) -> None:
    sections = (
        ("signatureFacts", "label"),
        ("atlasExtras", "title"),
        ("travelTrivia", "title"),
        ("tips", "title"),
    )

    seen_titles: dict[str, str] = {}
    for section, title_field in sections:
        items = data.get(section) if isinstance(data.get(section), list) else []
        for index, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            normalized = normalized_editorial_title(item.get(title_field))
            if not normalized:
                continue
            owner = f"{section}[{index}]"
            if normalized in seen_titles:
                fail(
                    errors,
                    f"{filename}: editorial title が重複しています: "
                    f"{seen_titles[normalized]} / {owner}",
                )
            else:
                seen_titles[normalized] = owner

    if data.get("contentQaVersion") != 1:
        return

    seen_keys: dict[str, str] = {}
    generic_keys = {
        "city", "history", "life", "food", "road", "earth", "sea", "culture",
        "nature", "travel", "transport", "season", "fact", "trivia", "tip",
    }
    topic_pattern = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

    for section, _title_field in sections:
        items = data.get(section) if isinstance(data.get(section), list) else []
        for index, item in enumerate(items, 1):
            owner = f"{section}[{index}]"
            if not isinstance(item, dict):
                continue
            key = item.get("topicKey")
            if not isinstance(key, str) or not key.strip():
                fail(errors, f"{filename}: {owner} に topicKey がありません")
                continue
            key = key.strip()
            if not topic_pattern.fullmatch(key):
                fail(errors, f"{filename}: {owner}.topicKey は英小文字kebab-caseで指定してください: {key}")
                continue
            if key in generic_keys:
                fail(errors, f"{filename}: {owner}.topicKey が抽象的すぎます: {key}")
            if key in seen_keys:
                fail(
                    errors,
                    f"{filename}: primary topic '{key}' が重複しています: "
                    f"{seen_keys[key]} / {owner}",
                )
            else:
                seen_keys[key] = owner


def validate_map_css_clean(errors: list[str]) -> None:
    """Reject decorative map ovals in shared Country CSS sources.

    Generated assets/css/country.css is rebuilt from source CSS during build,
    so scan the source stylesheets and leave generated bundles out of this gate.
    """
    css_root = ROOT / "assets" / "css"
    if not css_root.exists():
        return
    for path in sorted(css_root.glob("*.css")):
        if path.name in {"country.css", "top.css"}:
            continue
        try:
            css = path.read_text(encoding="utf-8")
        except Exception as exc:
            fail(errors, f"{path.relative_to(ROOT)}: CSSを読み込めません: {exc}")
            continue
        if ".map-art::before" in css or ".map-art::after" in css:
            fail(
                errors,
                f"{path.relative_to(ROOT)}: Country Mapの装飾楕円pseudo-elementは禁止です",
            )


def bounds_values(data: dict) -> tuple[object, object, object, object]:
    bounds = data.get("map", {}).get("bounds", {})
    return bounds.get("north"), bounds.get("south"), bounds.get("west"), bounds.get("east")


def validate_coordinates(errors: list[str], owner: str, coordinates: object, bounds: tuple[object, object, object, object]) -> None:
    coords = coordinates if isinstance(coordinates, dict) else {}
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
        fail(errors, f"{owner}: latitude が不正です")
    if not isinstance(lon, (int, float)) or not -180 <= lon <= 180:
        fail(errors, f"{owner}: longitude が不正です")

    north, south, west, east = bounds
    if all(isinstance(v, (int, float)) for v in (north, south, west, east, lat, lon)):
        if not (south <= lat <= north and west <= lon <= east):
            fail(errors, f"{owner}: 座標が map.bounds の外です")


def marker_min_distance(kind_a: str, kind_b: str) -> float:
    kinds = {kind_a, kind_b}
    # Intrinsic-canvas distances equivalent to the 320px mobile map.
    if kind_a == kind_b == "scene":
        return 71.0
    if kinds == {"scene", "hero"}:
        return 64.0
    if kinds == {"scene", "capital"}:
        return 55.0
    if kinds == {"hero", "capital"}:
        return 47.0
    return 0.0


def marker_offset(errors: list[str], owner: str, value: object) -> tuple[float, float]:
    if value is None:
        return 0.0, 0.0
    if not isinstance(value, dict):
        fail(errors, f"{owner}: mapOffset は object で指定してください")
        return 0.0, 0.0
    x = value.get("x", 0)
    y = value.get("y", 0)
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        fail(errors, f"{owner}: mapOffset.x / y は数値で指定してください")
        return 0.0, 0.0
    if math.hypot(float(x), float(y)) > MAX_MARKER_OFFSET_PERCENT:
        fail(
            errors,
            f"{owner}: mapOffset が大きすぎます（最大 {MAX_MARKER_OFFSET_PERCENT:.1f}%）: x={x}, y={y}",
        )
    return float(x), float(y)


def project_marker(
    coordinates: object,
    bounds: tuple[object, object, object, object],
    offset: tuple[float, float],
) -> tuple[float, float] | None:
    if not isinstance(coordinates, dict):
        return None
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    north, south, west, east = bounds
    if not all(isinstance(value, (int, float)) for value in (lat, lon, north, south, west, east)):
        return None
    longitude_range = east - west
    latitude_range = north - south
    midpoint_latitude = (south + north) / 2
    longitude_scale = math.cos(math.radians(midpoint_latitude))
    projected_width = longitude_range * longitude_scale
    projected_height = latitude_range
    canvas_scale = min(MAP_WIDTH / projected_width, MAP_HEIGHT / projected_height)
    draw_width = projected_width * canvas_scale
    draw_height = projected_height * canvas_scale
    canvas_offset_x = (MAP_WIDTH - draw_width) / 2
    canvas_offset_y = (MAP_HEIGHT - draw_height) / 2
    x = canvas_offset_x + (lon - west) * longitude_scale * canvas_scale + offset[0] / 100 * MAP_WIDTH
    y = canvas_offset_y + (north - lat) * canvas_scale + offset[1] / 100 * MAP_HEIGHT
    return x, y


def validate_map_markers(
    errors: list[str],
    filename: str,
    data: dict,
    bounds: tuple[object, object, object, object],
) -> None:
    markers: list[tuple[str, str, float, float]] = []

    capital = data.get("capital") if isinstance(data.get("capital"), dict) else {}
    capital_offset = marker_offset(errors, f"{filename}: capital", capital.get("mapOffset"))
    capital_point = project_marker(capital.get("coordinates"), bounds, capital_offset)
    if capital_point:
        markers.append(("capital", "capital", *capital_point))

    hero = data.get("hero") if isinstance(data.get("hero"), dict) else {}
    hero_offset = marker_offset(errors, f"{filename}: hero", hero.get("mapOffset"))
    hero_point = project_marker(hero.get("coordinates"), bounds, hero_offset)
    if hero_point:
        markers.append(("hero", "hero", *hero_point))

    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            continue
        offset = marker_offset(errors, f"{filename}: scene {index}", scene.get("mapOffset"))
        point = project_marker(scene.get("coordinates"), bounds, offset)
        if point:
            markers.append(("scene", f"scene {index}", *point))

    for kind, label, x, y in markers:
        margin = MARKER_EDGE_MARGIN[kind]
        if x < margin or x > MAP_WIDTH - margin or y < margin or y > MAP_HEIGHT - margin:
            fail(errors, f"{filename}: {label} marker が map canvas の端に近すぎます")

    for index, first in enumerate(markers):
        for second in markers[index + 1 :]:
            minimum = marker_min_distance(first[0], second[0])
            if not minimum:
                continue
            distance = math.hypot(first[2] - second[2], first[3] - second[3])
            if distance < minimum:
                fail(
                    errors,
                    f"{filename}: map marker collision: {first[1]} / {second[1]} "
                    f"({distance:.1f}px < {minimum:.1f}px)。座標は維持し mapOffset で最小補正してください",
                )


def validate_country(path: Path, strict: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: JSONを読み込めません: {exc}"]

    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        fail(errors, f"{path.name}: 必須キー不足: {', '.join(sorted(missing))}")
    if strict:
        strict_missing = STRICT_REQUIRED - data.keys()
        if strict_missing:
            fail(errors, f"{path.name}: 公開テンプレート必須キー不足: {', '.join(sorted(strict_missing))}")
        if data.get("schemaVersion") != 2:
            fail(errors, f"{path.name}: schemaVersion は 2 が必要です")

    slug = data.get("slug")
    if slug and path.stem != slug:
        fail(errors, f"{path.name}: slug '{slug}' とファイル名が一致しません")

    bounds = bounds_values(data)
    north, south, west, east = bounds
    if not all(isinstance(v, (int, float)) for v in bounds):
        fail(errors, f"{path.name}: map.bounds が不正です")
    elif not (north > south and east > west):
        fail(errors, f"{path.name}: map.bounds の大小関係が不正です")

    validate_asset(errors, f"{path.name}: map", data.get("map", {}).get("svg"))
    validate_map_svg_clean(errors, path.name, data.get("map", {}).get("svg"))
    validate_asset(errors, f"{path.name}: hero", data.get("hero", {}).get("image"))
    validate_coordinates(errors, f"{path.name}: hero", data.get("hero", {}).get("coordinates"), bounds)

    if strict:
        validate_coordinates(errors, f"{path.name}: capital", data.get("capital", {}).get("coordinates"), bounds)
        if not data.get("seo", {}).get("description"):
            fail(errors, f"{path.name}: seo.description がありません")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        fail(errors, f"{path.name}: scenes が空です")
        return errors
    if strict and len(scenes) != 8:
        fail(errors, f"{path.name}: 公開ページは8景必須ですが {len(scenes)} 件です")

    ids: set[str] = set()
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
        validate_coordinates(errors, prefix, scene.get("coordinates"), bounds)
        validate_asset(errors, prefix, scene.get("image"))

    validate_map_markers(errors, path.name, data, bounds)

    if strict:
        facts = data.get("facts") if isinstance(data.get("facts"), list) else []
        labels = [item.get("label") for item in facts if isinstance(item, dict)]
        if labels != COMMON_FACT_LABELS:
            fail(errors, f"{path.name}: 基本情報は {', '.join(COMMON_FACT_LABELS)} の順で7項目必要です")
        population = next((item.get("value", "") for item in facts if item.get("label") == "人口"), "")
        if re.search(r"\d+\.\d+", str(population)):
            fail(errors, f"{path.name}: 人口表示に小数精度を使わないでください: {population}")

        encounters = data.get("encounters") if isinstance(data.get("encounters"), list) else []
        if len(encounters) != 8:
            fail(errors, f"{path.name}: encounters はレイアウト仕様上8件必要です")

        signature = data.get("signatureFacts") if isinstance(data.get("signatureFacts"), list) else []
        if len(signature) != 3:
            fail(errors, f"{path.name}: signatureFacts は3件必要です")

        extras = data.get("atlasExtras") if isinstance(data.get("atlasExtras"), list) else []
        if len(extras) != 6:
            fail(errors, f"{path.name}: atlasExtras はレイアウト仕様上6件必要です")

        trivia = data.get("travelTrivia") if isinstance(data.get("travelTrivia"), list) else []
        if len(trivia) != 5:
            fail(errors, f"{path.name}: travelTrivia はレイアウト仕様上5件必要です")

        validate_content_topic_keys(errors, path.name, data)

        sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
        sources_verified_at = data.get("sourcesVerifiedAt")
        if not isinstance(sources_verified_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sources_verified_at):
            fail(errors, f"{path.name}: sourcesVerifiedAt は YYYY-MM-DD で指定してください")

        source_dates = data.get("sourceDates") if isinstance(data.get("sourceDates"), dict) else {}
        if "population" not in source_dates:
            fail(errors, f"{path.name}: 変動値の人口には sourceDates.population が必要です")
        period_pattern = re.compile(r"\d{4}(?:-(?:Q[1-4]|\d{2}(?:-\d{2})?))?")
        for source_key, period in source_dates.items():
            if source_key not in sources:
                fail(errors, f"{path.name}: sourceDates の '{source_key}' が sources にありません")
            if not isinstance(period, str) or not period_pattern.fullmatch(period):
                fail(
                    errors,
                    f"{path.name}: sourceDates.{source_key} は YYYY / YYYY-MM / YYYY-MM-DD / YYYY-Qn で指定してください",
                )

        seen_trivia_titles: set[str] = set()
        for index, item in enumerate(trivia, 1):
            if not isinstance(item, dict):
                fail(errors, f"{path.name}: trivia {index} がobjectではありません")
                continue
            for key in ("categoryEn", "categoryJa", "title", "text", "icon", "sourceKey"):
                if not item.get(key):
                    fail(errors, f"{path.name}: trivia {index} に {key} がありません")
            source_key = item.get("sourceKey")
            if source_key and source_key not in sources:
                fail(errors, f"{path.name}: trivia {index} の sourceKey '{source_key}' が sources にありません")
            title = item.get("title")
            if title in seen_trivia_titles:
                fail(errors, f"{path.name}: trivia title '{title}' が重複しています")
            if title:
                seen_trivia_titles.add(title)

        seasons = data.get("seasons") if isinstance(data.get("seasons"), list) else []
        if len(seasons) != 4:
            fail(errors, f"{path.name}: seasons はレイアウト仕様上4件必要です")

        personas = data.get("personas") if isinstance(data.get("personas"), list) else []
        if len(personas) != 3:
            fail(errors, f"{path.name}: personas はレイアウト仕様上3件必要です")

        tips = data.get("tips") if isinstance(data.get("tips"), list) else []
        if len(tips) != 3:
            fail(errors, f"{path.name}: tips はレイアウト仕様上3件必要です")

        related = data.get("relatedCountries") if isinstance(data.get("relatedCountries"), list) else []
        if len(related) != 3:
            fail(errors, f"{path.name}: relatedCountries はレイアウト仕様上3件必要です")
        related_slugs = [item.get("slug") for item in related if isinstance(item, dict)]
        if len(related_slugs) != len(set(related_slugs)):
            fail(errors, f"{path.name}: relatedCountries slug が重複しています")

    return errors


def validate_all_atlas_map_assets() -> list[str]:
    errors: list[str] = []
    image_root = ROOT / "assets" / "images"
    if not image_root.exists():
        return errors
    for path in sorted(image_root.rglob("map-atlas*.svg")):
        try:
            svg = path.read_text(encoding="utf-8")
        except Exception as exc:
            fail(errors, f"{path.relative_to(ROOT)}: SVGを読み込めません: {exc}")
            continue
        if "<ellipse" in svg:
            fail(errors, f"{path.relative_to(ROOT)}: <ellipse> を検出。Country Mapの装飾楕円は禁止です")
        if "<radialGradient" in svg:
            fail(errors, f"{path.relative_to(ROOT)}: radialGradient を検出。Country Mapの背景ムラは禁止です")
    return errors


def all_country_paths() -> tuple[list[Path], list[str]]:
    return sorted(COUNTRY_DIR.glob("*.json")), []


def load_destination_scope() -> tuple[list[dict], list[str]]:
    items: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()
    for registry_path in REGISTRY_PATHS:
        if not registry_path.exists():
            errors.append(f"destination registry がありません: {registry_path.name}")
            continue
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{registry_path.name}: 読み込めません: {exc}")
            continue
        for item in registry.get("destinations", []):
            slug = item.get("slug") if isinstance(item, dict) else None
            if not slug:
                errors.append(f"{registry_path.name}: slugのないdestinationがあります")
                continue
            if slug in seen:
                errors.append(f"destination slug '{slug}' がregistry間で重複しています")
                continue
            seen.add(slug)
            items.append(item)
    if len(items) != 201:
        errors.append(f"destination scope は201件必要ですが {len(items)} 件です")
    return items, errors


def published_paths() -> tuple[list[Path], list[str]]:
    items, errors = load_destination_scope()
    paths: list[Path] = []
    for item in items:
        if not item.get("atlasPublished"):
            continue
        slug = item.get("slug")
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"公開対象 '{slug}' のcountry JSONがありません")
        else:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{path.name}: JSONを読み込めません: {exc}")
                continue
            expected_href = f"countries/{slug}/"
            if item.get("href") != expected_href:
                errors.append(
                    f"公開対象 '{slug}' のhrefは '{expected_href}' が必要です: {item.get('href')!r}"
                )
            expected_image = data.get("hero", {}).get("image")
            if item.get("image") != expected_image:
                errors.append(
                    f"公開対象 '{slug}' のregistry imageがhero.imageと一致しません: "
                    f"{item.get('image')!r} != {expected_image!r}"
                )
            paths.append(path)
    return paths, errors


def reviewable_paths() -> tuple[list[Path], list[str]]:
    """Return schema-v2 country JSONs that build_site renders as review pages."""
    items, errors = load_destination_scope()
    paths: list[Path] = []
    for item in items:
        slug = item.get("slug")
        if not slug:
            continue
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.name}: JSONを読み込めません: {exc}")
            continue
        if data.get("schemaVersion") == 2:
            paths.append(path)
    return paths, errors


def main() -> int:
    strict = False
    mode = "standard"
    args = sys.argv[1:]
    if args and args[0] == "--published":
        strict = True
        mode = "published strict"
        paths, errors = published_paths()
    elif args and args[0] == "--reviewable":
        strict = True
        mode = "reviewable strict"
        paths, errors = reviewable_paths()
    elif args:
        paths = [Path(arg) for arg in args]
        errors = []
    else:
        paths, errors = all_country_paths()

    errors.extend(validate_all_atlas_map_assets())
    validate_map_css_clean(errors)

    for path in paths:
        errors.extend(validate_country(path, strict=strict))

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed ({mode}): {len(paths)} country file(s); 201-destination scope is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
