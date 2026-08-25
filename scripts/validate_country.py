#!/usr/bin/env python3
"""Validate JOURNEY ATLAS country data and production prerequisites."""

from __future__ import annotations

import base64
import json
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
    "signatureFacts", "updatedAt", "sources",
}
COMMON_FACT_LABELS = ["地域", "首都", "人口", "面積", "言語", "主な宗教", "通貨"]


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

    if strict:
        facts = data.get("facts") if isinstance(data.get("facts"), list) else []
        labels = [item.get("label") for item in facts if isinstance(item, dict)]
        if labels != COMMON_FACT_LABELS:
            fail(errors, f"{path.name}: 基本情報は {', '.join(COMMON_FACT_LABELS)} の順で7項目必要です")
        population = next((item.get("value", "") for item in facts if item.get("label") == "人口"), "")
        if re.search(r"\d+\.\d+", str(population)):
            fail(errors, f"{path.name}: 人口表示に小数精度を使わないでください: {population}")

        signature = data.get("signatureFacts") if isinstance(data.get("signatureFacts"), list) else []
        if len(signature) != 3:
            fail(errors, f"{path.name}: signatureFacts は3件必要です")

        extras = data.get("atlasExtras") if isinstance(data.get("atlasExtras"), list) else []
        if not extras:
            fail(errors, f"{path.name}: atlasExtras が空です")

        trivia = data.get("travelTrivia") if isinstance(data.get("travelTrivia"), list) else []
        if len(trivia) != 5:
            fail(errors, f"{path.name}: travelTrivia はレイアウト仕様上5件必要です")
        sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
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

        related = data.get("relatedCountries") if isinstance(data.get("relatedCountries"), list) else []
        related_slugs = [item.get("slug") for item in related if isinstance(item, dict)]
        if len(related_slugs) != len(set(related_slugs)):
            fail(errors, f"{path.name}: relatedCountries slug が重複しています")

    return errors


def country_paths_from_index() -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    registry = COUNTRY_DIR / "index.json"
    if not registry.exists():
        return sorted(path for path in COUNTRY_DIR.glob("*.json") if path.name != "index.json"), errors
    try:
        registry_data = json.loads(registry.read_text(encoding="utf-8"))
    except Exception as exc:
        return [], [f"index.json: JSONを読み込めません: {exc}"]
    entries = registry_data.get("countries")
    if not isinstance(entries, list):
        return [], ["index.json: countries は配列である必要があります"]
    paths = []
    for entry in entries:
        slug = entry.get("slug") if isinstance(entry, dict) else None
        if slug and (COUNTRY_DIR / f"{slug}.json").exists():
            paths.append(COUNTRY_DIR / f"{slug}.json")
    return paths, errors


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
            paths.append(path)
    return paths, errors


def main() -> int:
    strict = False
    args = sys.argv[1:]
    if args and args[0] == "--published":
        strict = True
        paths, errors = published_paths()
    elif args:
        paths = [Path(arg) for arg in args]
        errors = []
    else:
        paths, errors = country_paths_from_index()

    for path in paths:
        errors.extend(validate_country(path, strict=strict))

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "published strict" if strict else "standard"
    print(f"Validation passed ({mode}): {len(paths)} country file(s); 201-destination scope is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
