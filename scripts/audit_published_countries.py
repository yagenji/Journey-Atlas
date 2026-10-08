#!/usr/bin/env python3
"""Audit published Country Pages with optional legacy renewal metadata.

This script does not rewrite country content. The legacy renewal registry is
treated as optional metadata for Countries that were tracked by the old renewal
process; newly produced Countries are not required to add renewal-state rows.

The audit prints Signature Facts and Scenes so horizontal editorial review can
compare all published Countries on the same basis. Heuristic flags are review
cues only; they do not fail publication by themselves.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "data" / "country-renewal-status.json"
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRIES = [ROOT / "data" / "atlas-destinations.json"]
THEMES = ROOT / "data" / "theme-taxonomy.json"

HERITAGE_TERMS = ("世界遺産", "unesco", "world heritage")
HERITAGE_DETAIL_TERMS = (
    "登録", "構成資産", "構成要素", "ha", "ヘクタール", "km²", "平方キロ",
    "標高", "高さ", "長さ", "面積", "年", "件",
)
PROFILE_TERMS = ("人口密度", "人口", "国土面積", "面積", "population density", "population", "area")
FOREST_TERMS = ("森林", "樹林", "forest", "woodland")
HERITAGE_EXCEPTION_MIN = 30
SHORT_NOTE_MIN_CHARS = 32
SCENE_EXPECTED_COUNT = 8
SCENE_SHORT_DESCRIPTION_MIN_CHARS = 48
SCENE_NEAR_COORDINATE_KM = 2.0
TOPIC_NOISE = {
    "count", "counts", "number", "numbers", "share", "rate", "ratio", "percent",
    "percentage", "stat", "stats", "fact", "facts", "trivia", "history", "background",
    "overview", "story", "system", "culture", "context", "figure", "figures", "country",
    "national", "detail", "details", "today", "current",
}


def published_slugs() -> list[str]:
    out, seen = [], set()
    for path in REGISTRIES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("destinations", []):
            slug = item.get("slug")
            if item.get("atlasPublished") and slug and slug not in seen:
                seen.add(slug)
                out.append(slug)
    return out


def theme_counts() -> dict[str, list[str]]:
    data = json.loads(THEMES.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for theme in data.get("themes", []):
        label = theme.get("label") or theme.get("id") or "theme"
        for slug in theme.get("examples", []):
            out.setdefault(slug, []).append(label)
    return out


def clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def first_number(value: object) -> float | None:
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)", clean(value))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def percentages(value: str) -> list[float]:
    return [float(part) for part in re.findall(r"(\d+(?:\.\d+)?)\s*%", value)]


def topic_tokens(value: object) -> set[str]:
    raw = {part for part in re.split(r"[-_\s]+", clean(value).lower()) if part and part not in TOPIC_NOISE}
    normalized: set[str] = set()
    if "world" in raw and "heritage" in raw:
        normalized.add("worldheritage")
        raw.discard("world")
        raw.discard("heritage")
    aliases = {
        "unesco": "worldheritage",
        "woodland": "forest",
        "forests": "forest",
        "nomadic": "nomad",
        "nomads": "nomad",
    }
    normalized.update(aliases.get(part, part) for part in raw)
    return {part for part in normalized if len(part) >= 3}


def cross_section_topic_keys(data: dict, section: str) -> list[tuple[str, set[str]]]:
    out: list[tuple[str, set[str]]] = []
    items = data.get(section, [])
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        key = clean(item.get("topicKey"))
        tokens = topic_tokens(key)
        if key and tokens:
            out.append((key, tokens))
    return out


def unfamiliar_unit_flags(value: str, note: str) -> list[str]:
    haystack = f"{value} {note}"
    flags: list[str] = []
    if re.search(r"(?:\bha\b|ヘクタール)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:km²|km2|平方キロ)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_HECTARE")
    if re.search(r"(?:\bacres?\b|エーカー)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:km²|km2|平方キロ)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_ACRE")
    if re.search(r"(?:\bmiles?\b|マイル)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:\bkm\b|キロメートル)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_MILE")
    if re.search(r"(?:\bfeet\b|\bfoot\b|フィート)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:\d[\d,.]*\s*m\b|メートル)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_FEET")
    if re.search(r"(?:°f\b|華氏)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:℃|°c\b|摂氏)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_FAHRENHEIT")
    if re.search(r"(?:\bgallons?\b|ガロン)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:\bl\b|リットル)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_GALLON")
    if re.search(r"(?:\bknots?\b|ノット)", haystack, flags=re.IGNORECASE) and not re.search(r"(?:km/h|キロ毎時|キロメートル毎時)", haystack, flags=re.IGNORECASE):
        flags.append("UNIT_KNOT")
    return flags


def signature_flags(data: dict, item: dict) -> list[str]:
    label = clean(item.get("label"))
    value = clean(item.get("value"))
    note = clean(item.get("note"))
    topic = clean(item.get("topicKey"))
    haystack = " ".join((topic, label, value, note)).lower()
    flags: list[str] = []

    heritage = any(term.lower() in haystack for term in HERITAGE_TERMS)
    if heritage:
        count = first_number(value)
        count_value = bool(re.search(r"(?:件|\bsites?\b)", value, flags=re.IGNORECASE))
        dimension_value = bool(re.search(
            r"(?:ha|ヘクタール|km²|平方キロ|\bkm\b|\bm\b|年|\byears?\b)", value, flags=re.IGNORECASE,
        ))
        exceptional_count = count is not None and count >= HERITAGE_EXCEPTION_MIN and count_value and not dimension_value
        if exceptional_count:
            flags.append("HERITAGE_EXCEPTION_REVIEW")
        elif any(term.lower() in haystack for term in HERITAGE_DETAIL_TERMS):
            flags.append("HERITAGE_DESCRIPTION")
        else:
            flags.append("HERITAGE_RELATED")

    if any(term.lower() in haystack for term in PROFILE_TERMS) and item.get("exceptionalScale") is not True:
        flags.append("PROFILE_STAT")

    if any(term.lower() in haystack for term in FOREST_TERMS):
        pcts = percentages(" ".join((value, note)))
        extreme = bool(pcts) and all(pct <= 10 or pct >= 70 for pct in pcts)
        if item.get("exceptionalShare") is not True or not extreme:
            flags.append("FOREST_SHARE")

    sig_tokens = topic_tokens(topic)
    if sig_tokens:
        for section in ("atlasExtras", "travelTrivia"):
            for other_key, other_tokens in cross_section_topic_keys(data, section):
                shared = sig_tokens & other_tokens
                if not shared:
                    continue
                union = sig_tokens | other_tokens
                jaccard = len(shared) / max(1, len(union))
                subset = sig_tokens <= other_tokens or other_tokens <= sig_tokens
                strong_single = len(shared) == 1 and subset and len(next(iter(shared))) >= 5
                if len(shared) >= 2 or jaccard >= 0.60 or strong_single:
                    flags.append(f"TOPIC_OVERLAP:{section}:{other_key}")
                    break

    if len(note) < SHORT_NOTE_MIN_CHARS:
        flags.append("SHORT_NOTE")
    flags.extend(unfamiliar_unit_flags(value, note))
    if not re.search(r"\d", value):
        flags.append("NO_NUMERIC_VALUE")
    return flags


def signature_rows(slug: str, data: dict) -> list[dict]:
    rows: list[dict] = []
    items = data.get("signatureFacts", [])
    if not isinstance(items, list):
        return rows
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        rows.append({
            "slug": slug,
            "index": index,
            "topicKey": clean(item.get("topicKey")),
            "label": clean(item.get("label")),
            "value": clean(item.get("value")),
            "note": clean(item.get("note")),
            "interestReason": clean(item.get("interestReason")),
            "flags": signature_flags(data, item),
        })
    return rows


def scene_coordinates(item: dict) -> tuple[float, float] | None:
    coords = item.get("coordinates")
    if not isinstance(coords, dict):
        return None
    lat, lon = coords.get("latitude"), coords.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return float(lat), float(lon)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def scene_flags(item: dict, index: int, scenes: list[dict]) -> list[str]:
    flags: list[str] = []
    required_text = ("id", "name", "description", "image")
    for key in required_text:
        if not clean(item.get(key)):
            flags.append(f"MISSING_{key.upper()}")
    if not clean(item.get("mapLabel")):
        flags.append("MISSING_MAP_LABEL")
    if not clean(item.get("nameLocal")):
        flags.append("MISSING_LOCAL_NAME_REVIEW")

    description = clean(item.get("description"))
    if description and len(description) < SCENE_SHORT_DESCRIPTION_MIN_CHARS:
        flags.append("SHORT_DESCRIPTION")
    sentence_marks = description.count("。") + description.count(".")
    if description and sentence_marks < 2 and len(description) < 90:
        flags.append("THIN_EXPLANATION")

    coords = scene_coordinates(item)
    if coords is None:
        flags.append("MISSING_COORDINATES")
    else:
        for other_index, other in enumerate(scenes, 1):
            if other_index >= index or not isinstance(other, dict):
                continue
            other_coords = scene_coordinates(other)
            if other_coords is None:
                continue
            distance = haversine_km(coords, other_coords)
            if distance < 0.05:
                flags.append(f"DUPLICATE_COORDINATES:S{other_index:02d}")
            elif distance < SCENE_NEAR_COORDINATE_KM:
                flags.append(f"NEAR_COORDINATES_REVIEW:S{other_index:02d}:{distance:.1f}km")

    for key, code in (("id", "ID"), ("name", "NAME"), ("mapLabel", "MAP_LABEL"), ("image", "IMAGE")):
        value = clean(item.get(key))
        if not value:
            continue
        for other_index, other in enumerate(scenes, 1):
            if other_index >= index or not isinstance(other, dict):
                continue
            if value == clean(other.get(key)):
                flags.append(f"DUPLICATE_{code}:S{other_index:02d}")
    return flags


def scene_country_flags(data: dict) -> list[str]:
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        return ["SCENES_NOT_LIST"]
    flags: list[str] = []
    if len(scenes) != SCENE_EXPECTED_COUNT:
        flags.append(f"SCENE_COUNT_{len(scenes)}")

    map_data = data.get("map") if isinstance(data.get("map"), dict) else {}
    bounds = map_data.get("bounds") if isinstance(map_data.get("bounds"), dict) else {}
    points = [scene_coordinates(item) for item in scenes if isinstance(item, dict)]
    points = [point for point in points if point is not None]
    if len(points) >= 4 and all(isinstance(bounds.get(k), (int, float)) for k in ("north", "south", "west", "east")):
        lat_span = max(p[0] for p in points) - min(p[0] for p in points)
        lon_span = max(p[1] for p in points) - min(p[1] for p in points)
        map_lat_span = float(bounds["north"]) - float(bounds["south"])
        map_lon_span = float(bounds["east"]) - float(bounds["west"])
        if map_lat_span > 0 and map_lon_span > 0:
            lat_ratio = lat_span / map_lat_span
            lon_ratio = lon_span / map_lon_span
            if lat_ratio < 0.28 and lon_ratio < 0.28:
                flags.append(f"LOW_GEOGRAPHIC_SPREAD_REVIEW:{lat_ratio:.2f}x{lon_ratio:.2f}")
    return flags


def scene_rows(slug: str, data: dict) -> tuple[list[dict], list[str]]:
    items = data.get("scenes", [])
    if not isinstance(items, list):
        return [], ["SCENES_NOT_LIST"]
    scenes = [item for item in items if isinstance(item, dict)]
    rows: list[dict] = []
    for index, item in enumerate(scenes, 1):
        coords = scene_coordinates(item)
        rows.append({
            "slug": slug,
            "index": index,
            "id": clean(item.get("id")),
            "name": clean(item.get("name")),
            "nameLocal": clean(item.get("nameLocal")),
            "mapLabel": clean(item.get("mapLabel")),
            "description": clean(item.get("description")),
            "coordinates": coords,
            "image": clean(item.get("image")),
            "flags": scene_flags(item, index, scenes),
        })
    return rows, scene_country_flags(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_rows = status.get("countries", [])
    status_slugs = [row.get("slug") for row in status_rows]
    published = published_slugs()

    errors = []
    missing = sorted(set(published) - set(status_slugs))
    extra = sorted(set(status_slugs) - set(published))
    duplicates = sorted({slug for slug in status_slugs if status_slugs.count(slug) > 1 and slug})
    if extra:
        errors.append(f"renewal status contains non-published countries: {', '.join(extra)}")
    if duplicates:
        errors.append(f"renewal status contains duplicate slugs: {', '.join(duplicates)}")

    themes = theme_counts()
    rows = []
    signature_audit: list[dict] = []
    scene_audit: list[dict] = []
    scene_country_audit: list[dict] = []
    by_status = {row["slug"]: row for row in status_rows if row.get("slug")}
    for slug in published:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"published Country JSON missing: {slug}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        visible_facts = [f for f in data.get("facts", []) if f.get("label") != "地域"]
        row = {
            "slug": slug,
            "auditState": by_status.get(slug, {}).get("auditState") or "N/A",
            "renewalClass": by_status.get(slug, {}).get("renewalClass") or "N/A",
            "hardImageGate": bool(by_status.get(slug, {}).get("hardImageGate")),
            "visibleFacts": len(visible_facts),
            "scenes": len(data.get("scenes", [])),
            "encounters": len(data.get("encounters", [])),
            "beyond": len(data.get("atlasExtras", [])),
            "trivia": len(data.get("travelTrivia", [])),
            "themes": len(themes.get(slug, [])),
            "hasHero": bool(data.get("hero", {}).get("image")),
            "hasMap": bool(data.get("map", {}).get("svg")),
            "sourcesVerifiedAt": data.get("sourcesVerifiedAt"),
        }
        rows.append(row)
        signature_audit.extend(signature_rows(slug, data))
        scene_items, country_flags = scene_rows(slug, data)
        scene_audit.extend(scene_items)
        scene_country_audit.append({"slug": slug, "count": len(scene_items), "flags": country_flags})

    if args.json:
        print(json.dumps(
            {
                "published": len(published),
                "rows": rows,
                "signatureFacts": signature_audit,
                "scenes": scene_audit,
                "sceneCountries": scene_country_audit,
                "legacyUntracked": missing,
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(f"Published Country renewal audit: {len(published)} country page(s)")
        for row in rows:
            print(
                f"{row['slug']:<16} audit={row['auditState']:<7} class={row['renewalClass']:<12} "
                f"gate={'Y' if row['hardImageGate'] else 'N'} facts={row['visibleFacts']} scenes={row['scenes']} "
                f"enc={row['encounters']} beyond={row['beyond']} trivia={row['trivia']} themes={row['themes']}"
            )

        print(f"Signature Facts horizontal audit: {len(signature_audit)} item(s)")
        for item in signature_audit:
            flags = ",".join(item["flags"]) if item["flags"] else "-"
            note = item["note"].replace("\n", " ")
            reason = item["interestReason"].replace("\n", " ")
            print(
                f"SIG|{item['slug']}|{item['index']}|{item['label']}|{item['value']}|"
                f"flags={flags}|note={note}|interestReason={reason}"
            )

        flagged = [item for item in signature_audit if item["flags"]]
        print(f"Signature Facts heuristic review candidates: {len(flagged)} item(s)")
        for item in flagged:
            print(
                f"SIG_REVIEW|{item['slug']}|{item['index']}|{item['label']}|{item['value']}|"
                f"{','.join(item['flags'])}"
            )

        print(f"Scenes horizontal audit: {len(scene_audit)} item(s)")
        for item in scene_audit:
            flags = ",".join(item["flags"]) if item["flags"] else "-"
            coords = item["coordinates"]
            coord_text = "" if coords is None else f"{coords[0]:.6f},{coords[1]:.6f}"
            description = item["description"].replace("\n", " ")
            print(
                f"SCENE|{item['slug']}|{item['index']}|{item['name']}|{item['mapLabel']}|"
                f"coords={coord_text}|flags={flags}|description={description}"
            )

        scene_flagged = [item for item in scene_audit if item["flags"]]
        country_flagged = [item for item in scene_country_audit if item["flags"]]
        print(f"Scenes heuristic review candidates: {len(scene_flagged)} item(s); country-level: {len(country_flagged)}")
        for item in scene_country_audit:
            if item["flags"]:
                print(f"SCENE_COUNTRY_REVIEW|{item['slug']}|count={item['count']}|{','.join(item['flags'])}")
        for item in scene_flagged:
            print(
                f"SCENE_REVIEW|{item['slug']}|{item['index']}|{item['name']}|"
                f"{','.join(item['flags'])}"
            )

        if missing:
            print("Legacy renewal metadata not required for:")
            for slug in missing:
                print(f"- {slug}")
        if errors:
            print("Registry errors:")
            for error in errors:
                print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
