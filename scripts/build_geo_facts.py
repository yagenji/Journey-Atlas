#!/usr/bin/env python3
"""Generate data/geo-facts.json: small "地球の上で" facts for Country and Region pages.

For every published Country / Region page:
- tz:        IANA time zone of the capital / seat (countries with several zones use the
             capital), so the page can show the current local time;
- latitude:  a place at almost the same latitude as the capital (±0.5°) — a Japanese city
             when one fits, otherwise a capital on another continent, the farthest away;
- antipode:  Countries whose land lies on the opposite side of the Earth from this
             one's land (land-to-land only).

Run when capitals or published pages change:
    pip install shapely timezonefinder
    python3 scripts/build_geo_facts.py --countries /path/to/ne_50m_admin_0_countries.geojson

Geometry: Natural Earth 1:50m Admin-0 countries (public domain). Time zones: timezonefinder
(timezone-boundary-builder, ODbL data used only to look up zone names, not shipped).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from shapely import make_valid
from shapely.affinity import affine_transform
from shapely.geometry import MultiPolygon, Point, Polygon, box, shape
from shapely.ops import unary_union
from timezonefinder import TimezoneFinder

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/geo-facts.json"

# Reference cities for Japanese readers (city hall / prefectural office, 2 decimals).
JAPAN_CITIES = [
    ("稚内", 45.42), ("旭川", 43.77), ("札幌", 43.06), ("函館", 41.77), ("青森", 40.82),
    ("盛岡", 39.70), ("仙台", 38.27), ("新潟", 37.92), ("福島", 37.75), ("金沢", 36.56),
    ("宇都宮", 36.56), ("長野", 36.65), ("水戸", 36.37), ("東京", 35.68), ("名古屋", 35.18),
    ("京都", 35.01), ("大阪", 34.69), ("広島", 34.39), ("松山", 33.84), ("福岡", 33.59),
    ("高知", 33.56), ("長崎", 32.75), ("熊本", 32.80), ("宮崎", 31.91), ("鹿児島", 31.60),
    ("奄美", 28.38), ("那覇", 26.21), ("石垣", 24.34),
]
LATITUDE_WINDOW = 0.5

# Pages without capital coordinates in their data: representative seat / centre.
FALLBACK_PLACES = {
    "brunei": ("バンダルスリブガワン", 4.8903, 114.9401),
    "hong-kong": ("香港", 22.2793, 114.1628),
    "macau": ("マカオ", 22.1987, 113.5439),
}
# Regions without a seat: the zone is fixed by name (no latitude fact is shown).
FALLBACK_ZONES = {
    "azores": "Atlantic/Azores",
    "canary-islands": "Atlantic/Canary",
    "gibraltar": "Europe/Gibraltar",
    "montserrat": "America/Montserrat",
    "caribbean-netherlands": "America/Kralendijk",
    "mariana-islands": "Pacific/Guam",
}
NO_FACTS = {"antarctica"}  # no single local time, capital or latitude

# Natural Earth parts farther than this from the capital are left out of a Country's
# antipode test (e.g. French overseas departments, Hawaii, Alaska), so the fact describes
# the Country's main land; a part touching the capital (Russia's mainland) is always kept.
MAIN_LAND_RADIUS_KM = 3000
MIN_OVERLAP_SHARE = 0.08
MAX_ANTIPODES = 2


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def polygons(geom) -> list[Polygon]:
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def main_land(geom, lat: float | None, lon: float | None):
    if lat is None:
        return geom
    kept = []
    for part in polygons(geom):
        if part.contains(Point(lon, lat)):
            kept.append(part)
            continue
        nearest = part.exterior.interpolate(part.exterior.project(Point(lon, lat)))
        if haversine_km(lat, lon, nearest.y, nearest.x) <= MAIN_LAND_RADIUS_KM:
            kept.append(part)
    return unary_union(kept) if kept else geom


def antipodal(geom):
    """Point-by-point antipode: (lon, lat) -> (lon ± 180, -lat), split at the 0° meridian."""
    geom = make_valid(geom)
    east = geom.intersection(box(0, -90, 180, 90))
    west = geom.intersection(box(-180, -90, 0, 90))
    parts = []
    if not east.is_empty:
        parts.append(affine_transform(east, [1, 0, 0, -1, -180, 0]))
    if not west.is_empty:
        parts.append(affine_transform(west, [1, 0, 0, -1, 180, 0]))
    return make_valid(unary_union(parts))


def load_pages() -> list[dict]:
    registry = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
    chapters = json.loads((ROOT / "data/region-taxonomy.json").read_text(encoding="utf-8"))
    continent = {}
    for region in chapters.get("regions", []):
        for iso in region.get("iso2", []):
            continent[iso] = region["id"]
    pages = []
    for item in registry["destinations"]:
        if not item.get("atlasPublished"):
            continue
        data = json.loads((ROOT / "data/countries" / f"{item['slug']}.json").read_text(encoding="utf-8"))
        capital = data.get("capital") or {}
        coords = capital.get("coordinates") or {}
        place = None
        label = "首都"
        if coords:
            place = (capital.get("nameJa"), coords["latitude"], coords["longitude"])
        elif item["slug"] in FALLBACK_PLACES:
            place = FALLBACK_PLACES[item["slug"]]
            label = "首都" if item["slug"] == "brunei" else ""
        pages.append({
            "slug": item["slug"], "nameJa": item["nameJa"], "iso2": item.get("iso2"),
            "kind": "country", "place": place, "label": label, "continent": continent.get(item.get("iso2")),
            "detail": item["slug"] in set(registry.get("detailRegionSlugs") or []),
        })
    for path in sorted((ROOT / "data/regions").glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("regionPublished") is not True:
            continue
        capital = data.get("capital") or {}
        coords = capital.get("coordinates") or {}
        place = (capital.get("nameJa"), coords["latitude"], coords["longitude"]) if coords else None
        pages.append({
            "slug": data["slug"], "nameJa": data["nameJa"], "iso2": None, "kind": "region",
            "place": place, "label": capital.get("labelJa") or "", "continent": None, "parent": data.get("parentSlug"), "detail": True,
        })
    return pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", required=True, help="Natural Earth 1:50m admin-0 countries GeoJSON")
    args = parser.parse_args()

    pages = load_pages()
    by_slug = {page["slug"]: page for page in pages}
    finder = TimezoneFinder()

    features = json.loads(Path(args.countries).read_text(encoding="utf-8"))["features"]
    shapes: dict[str, object] = {}
    for feature in features:
        iso = feature["properties"].get("ISO_A2_EH")
        if iso and iso != "-99":
            geom = make_valid(shape(feature["geometry"]))
            shapes[iso] = unary_union([shapes[iso], geom]) if iso in shapes else geom

    countries = [page for page in pages if page["kind"] == "country" and not page["detail"]]
    lands = {}
    for page in countries:
        geom = shapes.get(page["iso2"])
        if geom is None or page["slug"] in NO_FACTS:
            continue
        lat = page["place"][1] if page["place"] else None
        lon = page["place"][2] if page["place"] else None
        lands[page["slug"]] = main_land(geom, lat, lon)

    out: dict[str, dict] = {}
    for page in pages:
        slug = page["slug"]
        if slug in NO_FACTS:
            continue
        entry: dict = {}
        place = page["place"]
        if place:
            entry["tz"] = finder.timezone_at(lat=place[1], lng=place[2])
            entry["place"] = {"label": page["label"], "nameJa": place[0], "lat": round(place[1], 2)}
        elif slug in FALLBACK_ZONES:
            entry["tz"] = FALLBACK_ZONES[slug]
        if not entry.get("tz") or entry["tz"].startswith("Etc/"):
            raise ValueError(f"No land time zone for {slug}: {entry.get('tz')}")

        if place and slug != "japan":
            lat = place[1]
            japan = [(abs(lat - city_lat), name, city_lat) for name, city_lat in JAPAN_CITIES
                     if abs(lat - city_lat) <= LATITUDE_WINDOW]
            if japan:
                _, name, city_lat = min(japan)
                entry["latitude"] = {"kind": "japan", "nameJa": name, "lat": city_lat}
            else:
                mine = page["continent"] or by_slug.get(page.get("parent") or "", {}).get("continent")
                candidates = []
                for other in countries:
                    if other["slug"] in (slug, page.get("parent")) or not other["place"]:
                        continue
                    if other["continent"] == mine:
                        continue
                    o_lat, o_lon = other["place"][1], other["place"][2]
                    if abs(o_lat - lat) <= LATITUDE_WINDOW:
                        candidates.append((-haversine_km(lat, place[2], o_lat, o_lon), other))
                if candidates:
                    _, other = min(candidates, key=lambda item: item[0])
                    entry["latitude"] = {
                        "kind": "capital", "nameJa": other["place"][0], "slug": other["slug"],
                        "countryJa": other["nameJa"], "lat": round(other["place"][1], 2),
                    }

        land = lands.get(slug)
        if land is not None:
            opposite = antipodal(land)
            hits = []
            for other_slug, other_land in lands.items():
                if other_slug == slug:
                    continue
                overlap = opposite.intersection(other_land).area
                if not overlap:
                    continue
                share = max(overlap / land.area, overlap / other_land.area)
                if share >= MIN_OVERLAP_SHARE:
                    hits.append((overlap, other_slug))
            hits.sort(reverse=True)
            if hits:
                entry["antipode"] = [
                    {"slug": other, "nameJa": by_slug[other]["nameJa"]} for _, other in hits[:MAX_ANTIPODES]
                ]
        out[slug] = entry

    payload = {
        "version": 1,
        "note": "Generated by scripts/build_geo_facts.py. Do not edit by hand.",
        "latitudeWindow": LATITUDE_WINDOW,
        "entries": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} pages: time {sum('tz' in e for e in out.values())}, "
          f"latitude {sum('latitude' in e for e in out.values())}, "
          f"antipode {sum('antipode' in e for e in out.values())}")


if __name__ == "__main__":
    main()
