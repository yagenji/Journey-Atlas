#!/usr/bin/env python3
"""Generate a JOURNEY ATLAS country-map SVG from high-quality geographic data."""

from __future__ import annotations

import argparse
import json
import math
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.ops import unary_union

WIDTH = 1200
HEIGHT = 760
STYLE_VERSION = "journey-atlas-map-v2-proportional"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=("gshhs", "natural-earth", "geoboundaries"),
        required=True,
    )
    parser.add_argument(
        "--bounds",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        required=True,
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset", help="Natural Earth shapefile/GeoJSON path")
    parser.add_argument("--country-name", help="Country name used to select Natural Earth geometry")
    parser.add_argument("--map-name", help="Accessible country name embedded in the SVG")
    parser.add_argument("--iso", help="ISO3 code for geoBoundaries, e.g. SWE")
    parser.add_argument(
        "--admin-level",
        default="ADM0",
        choices=("ADM0", "ADM1", "ADM2", "ADM3"),
        help="geoBoundaries level. ADM1 may be dissolved when ADM0 coastline detail is insufficient.",
    )
    parser.add_argument("--resolution", default="i", choices=("c", "l", "i", "h", "f"))
    parser.add_argument(
        "--simplify",
        type=float,
        default=0.003,
        help="Geometry simplification tolerance in degrees. Keep <=0.003 for production unless QA proves otherwise.",
    )
    parser.add_argument("--include-lakes", action="store_true", help="Render major lakes when they improve readability")
    parser.add_argument("--max-bytes", type=int, default=0, help="Fail if generated SVG exceeds this size; 0 disables")
    return parser.parse_args()


def polygons_from_geometry(geometry) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        result: list[Polygon] = []
        for item in geometry.geoms:
            result.extend(polygons_from_geometry(item))
        return result
    return []


def load_gshhs(
    bounds: tuple[float, float, float, float],
    resolution: str,
) -> tuple[list[Polygon], list[Polygon], str]:
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    m = Basemap(
        projection="cyl",
        llcrnrlon=west,
        llcrnrlat=south,
        urcrnrlon=east,
        urcrnrlat=north,
        resolution=resolution,
        area_thresh=0.1,
    )

    land: list[Polygon] = []
    lakes: list[Polygon] = []
    for (xs, ys), polygon_type in zip(m.coastpolygons, m.coastpolygontypes):
        geom = Polygon(zip(xs, ys))
        if not geom.is_valid:
            geom = geom.buffer(0)
        if polygon_type == 1:
            land.extend(polygons_from_geometry(geom))
        elif polygon_type == 2:
            lakes.extend(polygons_from_geometry(geom))
    return land, lakes, f"GSHHS/GSHHG via Basemap resolution={resolution}"


def load_natural_earth(dataset: str, country_name: str) -> tuple[list[Polygon], list[Polygon], str]:
    import geopandas as gpd

    gdf = gpd.read_file(dataset).to_crs(4326)
    candidate_fields = ["ADMIN", "NAME", "NAME_LONG", "NAME_EN", "SOVEREIGNT"]
    match = None
    for field in candidate_fields:
        if field in gdf.columns:
            subset = gdf[gdf[field].astype(str).str.casefold() == country_name.casefold()]
            if not subset.empty:
                match = subset
                break
    if match is None or match.empty:
        raise ValueError(f"Country not found in Natural Earth dataset: {country_name}")

    geometry = match.geometry.union_all() if hasattr(match.geometry, "union_all") else match.geometry.unary_union
    land = polygons_from_geometry(geometry)
    lakes: list[Polygon] = []
    for polygon in land:
        lakes.extend(Polygon(ring) for ring in polygon.interiors)
    return land, lakes, f"Natural Earth 1:10m | {dataset}"


def load_geoboundaries(iso: str, admin_level: str) -> tuple[list[Polygon], list[Polygon], str]:
    api_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso.upper()}/{admin_level}/"
    with urllib.request.urlopen(api_url) as response:
        metadata = json.load(response)

    source_url = metadata.get("gjDownloadURL")
    if not source_url:
        raise ValueError(f"geoBoundaries API returned no gjDownloadURL: {api_url}")

    with urllib.request.urlopen(source_url) as response:
        geojson = json.load(response)

    geometries = [shape(feature["geometry"]) for feature in geojson.get("features", [])]
    if not geometries:
        raise ValueError(f"geoBoundaries dataset contains no features: {source_url}")

    geometry = unary_union(geometries)
    land = polygons_from_geometry(geometry)
    lakes: list[Polygon] = []
    for polygon in land:
        lakes.extend(Polygon(ring) for ring in polygon.interiors)

    source_note = (
        f"geoBoundaries gbOpen {admin_level} dissolved | {source_url} | "
        f"source={metadata.get('boundarySource', 'unknown')} | "
        f"license={metadata.get('boundaryLicense', 'see upstream')}"
    )
    return land, lakes, source_note


def projection_frame(
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Return local-equirectangular scale and centered offsets for the canvas.

    Longitude degrees become physically shorter toward the poles.  Using the
    country's midpoint latitude as the standard parallel preserves the local
    geographic aspect ratio while keeping north up and east right.
    """
    west, south, east, north = bounds
    longitude_range = east - west
    latitude_range = north - south
    if longitude_range <= 0 or latitude_range <= 0:
        raise ValueError("Map bounds must have positive longitude and latitude ranges")

    midpoint_latitude = (south + north) / 2
    longitude_scale = math.cos(math.radians(midpoint_latitude))
    projected_width = longitude_range * longitude_scale
    projected_height = latitude_range
    canvas_scale = min(WIDTH / projected_width, HEIGHT / projected_height)
    draw_width = projected_width * canvas_scale
    draw_height = projected_height * canvas_scale
    offset_x = (WIDTH - draw_width) / 2
    offset_y = (HEIGHT - draw_height) / 2
    return longitude_scale, canvas_scale, offset_x, offset_y


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    longitude_scale, canvas_scale, offset_x, offset_y = projection_frame(bounds)
    x = offset_x + (lon - west) * longitude_scale * canvas_scale
    y = offset_y + (north - lat) * canvas_scale
    return x, y


def ring_path(coords, bounds: tuple[float, float, float, float]) -> str:
    points: list[tuple[float, float]] = []
    previous = None
    for lon, lat in coords:
        x, y = project(lon, lat, bounds)
        point = (round(x, 1), round(y, 1))
        if point != previous:
            points.append(point)
            previous = point
    if len(points) < 3:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def polygon_path(
    polygon: Polygon,
    bounds: tuple[float, float, float, float],
    simplify: float,
) -> str:
    geom = polygon.simplify(simplify, preserve_topology=True) if simplify > 0 else polygon
    if geom.is_empty:
        return ""
    parts = []
    for item in polygons_from_geometry(geom):
        parts.append(ring_path(item.exterior.coords, bounds))
        parts.extend(ring_path(ring.coords, bounds) for ring in item.interiors)
    return " ".join(part for part in parts if part)


def render_svg(
    land: list[Polygon],
    lakes: list[Polygon],
    bounds: tuple[float, float, float, float],
    simplify: float,
    include_lakes: bool,
    map_name: str,
    source_note: str,
) -> str:
    land = sorted(land, key=lambda geometry: geometry.area, reverse=True)
    land_d = " ".join(polygon_path(geometry, bounds, simplify) for geometry in land)

    lake_markup = ""
    if include_lakes:
        major_lakes = sorted((geometry for geometry in lakes if geometry.area > 0.003), key=lambda geometry: geometry.area, reverse=True)
        lake_markup = "".join(
            f'<path d="{polygon_path(geometry, bounds, max(simplify * 0.65, 0.0005))}"/>'
            for geometry in major_lakes
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Map of {escape(map_name)}" data-map-style="{STYLE_VERSION}" data-map-projection="local-equirectangular-fit-v1">
<metadata>{escape(source_note)}</metadata>
<defs>
<linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".55" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
<linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#e2dbad"/><stop offset=".52" stop-color="#d4cc9b"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/><feOffset in="b" dy="3" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .14 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>
<ellipse cx="220" cy="130" rx="300" ry="125" fill="#fbf7ec" opacity=".34"/><ellipse cx="1000" cy="650" rx="330" ry="155" fill="#d5e4e2" opacity=".35"/>
<path d="{land_d}" fill="url(#land)" fill-rule="evenodd" stroke="#31576a" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#shadow)"/>
{f'<g fill="#e5eceb" stroke="#6f8a92" stroke-opacity=".35" stroke-width=".65">{lake_markup}</g>' if lake_markup else ''}
</svg>'''


def main() -> None:
    args = parse_args()
    west, south, east, north = args.bounds
    bounds = (west, south, east, north)

    if args.source == "gshhs":
        land, lakes, source_note = load_gshhs(bounds, args.resolution)
    elif args.source == "natural-earth":
        if not args.dataset or not args.country_name:
            raise ValueError("--dataset and --country-name are required for natural-earth")
        land, lakes, source_note = load_natural_earth(args.dataset, args.country_name)
    else:
        if not args.iso:
            raise ValueError("--iso is required for geoboundaries")
        land, lakes, source_note = load_geoboundaries(args.iso, args.admin_level)

    map_name = args.map_name or args.country_name or args.iso or "Country"
    svg = render_svg(
        land,
        lakes,
        bounds,
        args.simplify,
        args.include_lakes,
        map_name,
        source_note,
    )
    byte_size = len(svg.encode("utf-8"))
    if args.max_bytes and byte_size > args.max_bytes:
        raise ValueError(
            f"Generated SVG is {byte_size} bytes, exceeding --max-bytes {args.max_bytes}. "
            "Increase --simplify only after visual QA; do not publish a truncated asset."
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"Wrote {output} ({STYLE_VERSION}, {byte_size} bytes)")
    print(f"Source: {source_note}")


if __name__ == "__main__":
    main()
