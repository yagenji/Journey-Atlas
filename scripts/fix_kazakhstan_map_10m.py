#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import urllib.request
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, Polygon

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_PATH = ROOT / "data/countries/kazakhstan.json"
MAP_PATH = ROOT / "assets/images/kazakhstan/map-atlas-v1.svg"
SOURCE_COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{SOURCE_COMMIT}/geojson/ne_10m_admin_0_countries.geojson"
)
MARGIN_RATIO = 0.04
SIMPLIFY = 0.001

spec = importlib.util.spec_from_file_location(
    "journey_map_generator", ROOT / "scripts/generate_country_map.py"
)
assert spec and spec.loader
mapgen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapgen)


def download_source() -> Path:
    target = Path(tempfile.gettempdir()) / "ne_10m_admin_0_countries.geojson"
    urllib.request.urlretrieve(SOURCE_URL, target)
    return target


def country_geometry(dataset: Path):
    gdf = gpd.read_file(dataset).to_crs(4326)
    mask = False
    if "ADM0_A3" in gdf.columns:
        mask = gdf["ADM0_A3"].astype(str).eq("KAZ")
    if "ADMIN" in gdf.columns:
        admin_mask = gdf["ADMIN"].astype(str).str.casefold().eq("kazakhstan")
        mask = admin_mask if mask is False else (mask | admin_mask)
    selected = gdf[mask]
    if selected.empty:
        raise SystemExit("Kazakhstan geometry not found in Natural Earth 1:10m dataset")
    return selected.geometry.union_all() if hasattr(selected.geometry, "union_all") else selected.geometry.unary_union


def padded_bounds(geometry) -> tuple[float, float, float, float]:
    west, south, east, north = geometry.bounds
    lon_margin = (east - west) * MARGIN_RATIO
    lat_margin = (north - south) * MARGIN_RATIO
    return (
        west - lon_margin,
        south - lat_margin,
        east + lon_margin,
        north + lat_margin,
    )


def inverse_project(x: float, y: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    longitude_scale, canvas_scale, offset_x, offset_y = mapgen.projection_frame(bounds)
    lon = west + ((x - offset_x) / (longitude_scale * canvas_scale))
    lat = north - ((y - offset_y) / canvas_scale)
    return lon, lat


def displayed_geo_point(item: dict, bounds: tuple[float, float, float, float]) -> Point:
    coordinates = item.get("coordinates") or {}
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise SystemExit(f"Missing numeric coordinates: {item}")
    x, y = mapgen.project(float(lon), float(lat), bounds)
    offset = item.get("mapOffset") or {}
    x += (float(offset.get("x", 0)) / 100.0) * mapgen.WIDTH
    y += (float(offset.get("y", 0)) / 100.0) * mapgen.HEIGHT
    display_lon, display_lat = inverse_project(x, y, bounds)
    return Point(display_lon, display_lat)


def assert_markers_inside(data: dict, geometry, bounds: tuple[float, float, float, float]) -> None:
    markers = [("capital", data["capital"]), ("hero", data["hero"])]
    markers.extend((scene.get("id", "scene"), scene) for scene in data.get("scenes", []))
    safe_geometry = geometry.buffer(1e-9)
    failures = []
    for label, item in markers:
        coordinates = item.get("coordinates") or {}
        true_point = Point(float(coordinates["longitude"]), float(coordinates["latitude"]))
        display_point = displayed_geo_point(item, bounds)
        if not safe_geometry.covers(true_point):
            failures.append(f"{label}: true coordinate is outside Kazakhstan geometry")
        if not safe_geometry.covers(display_point):
            failures.append(
                f"{label}: displayed marker leaves Kazakhstan after mapOffset "
                f"({display_point.y:.5f}, {display_point.x:.5f})"
            )
    if failures:
        raise SystemExit("Marker geography QA failed:\n- " + "\n- ".join(failures))


def main() -> None:
    dataset = download_source()
    geometry = country_geometry(dataset)
    bounds = padded_bounds(geometry)
    land = mapgen.polygons_from_geometry(geometry)
    lakes = []
    for polygon in land:
        lakes.extend(Polygon(ring) for ring in polygon.interiors)

    source_note = (
        "Natural Earth 1:10m Admin 0 Countries, nvkelso/natural-earth-vector "
        f"commit {SOURCE_COMMIT}, WGS84; Kazakhstan geometry; JOURNEY ATLAS map-v3"
    )
    svg = mapgen.render_svg(
        land=land,
        lakes=lakes,
        bounds=bounds,
        simplify=SIMPLIFY,
        include_lakes=True,
        map_name="Kazakhstan",
        source_note=source_note,
    )
    MAP_PATH.write_text(svg, encoding="utf-8")

    data = json.loads(COUNTRY_PATH.read_text(encoding="utf-8"))
    west, south, east, north = bounds
    data["map"]["bounds"] = {
        "north": round(north, 5),
        "south": round(south, 5),
        "west": round(west, 5),
        "east": round(east, 5),
    }
    data["map"]["source"] = source_note
    data["hero"]["mapOffset"] = {"x": 0, "y": 0}

    # Keep nearby southeast markers legible without moving them outside the country.
    for scene in data.get("scenes", []):
        if scene.get("id") == "charyn-canyon-valley-of-castles":
            scene["mapOffset"] = {"x": 1.0, "y": -2.0}
        elif scene.get("id") == "altyn-emel-singing-dune":
            scene["mapOffset"] = {"x": 0, "y": 0}

    sources = data.setdefault("sources", {})
    sources["map"] = (
        "Natural Earth 1:10m Admin 0 Countries (nvkelso/natural-earth-vector, "
        f"commit {SOURCE_COMMIT}); Kazakhstan geometry; WGS84."
    )
    assert_markers_inside(data, geometry, bounds)
    COUNTRY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    print("Kazakhstan map rebuilt from Natural Earth 1:10m")
    print(
        "Geometry bbox / padded bounds:",
        tuple(round(value, 5) for value in geometry.bounds),
        tuple(round(value, 5) for value in bounds),
    )
    print("Hero offset reset to 0/0; all capital/Hero/scene displayed markers remain inside Kazakhstan")


if __name__ == "__main__":
    main()
