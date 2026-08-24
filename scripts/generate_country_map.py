#!/usr/bin/env python3
"""Generate a compact JOURNEY ATLAS country-map SVG from geographic data."""

from __future__ import annotations

import argparse
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon

WIDTH = 1200
HEIGHT = 760
STYLE_VERSION = "journey-atlas-map-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("gshhs", "natural-earth"), required=True)
    parser.add_argument("--bounds", nargs=4, type=float, metavar=("WEST", "SOUTH", "EAST", "NORTH"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset", help="Natural Earth shapefile/GeoJSON path")
    parser.add_argument("--country-name", help="Country name used to select Natural Earth geometry")
    parser.add_argument("--resolution", default="i", choices=("c", "l", "i", "h", "f"))
    parser.add_argument("--simplify", type=float, default=0.03, help="Geometry simplification tolerance in degrees")
    parser.add_argument("--include-lakes", action="store_true", help="Render major lakes when they improve readability")
    parser.add_argument("--max-bytes", type=int, default=0, help="Fail if generated SVG exceeds this size; 0 disables")
    return parser.parse_args()


def polygons_from_geometry(geometry) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return []


def load_gshhs(bounds: tuple[float, float, float, float], resolution: str) -> tuple[list[Polygon], list[Polygon]]:
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
    return land, lakes


def load_natural_earth(dataset: str, country_name: str) -> tuple[list[Polygon], list[Polygon]]:
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
    return land, lakes


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    x = (lon - west) / (east - west) * WIDTH
    y = (north - lat) / (north - south) * HEIGHT
    return x, y


def svg_path(polygon: Polygon, bounds: tuple[float, float, float, float], simplify: float) -> str:
    geom = polygon.simplify(simplify, preserve_topology=True)
    points = [project(lon, lat, bounds) for lon, lat in geom.exterior.coords]
    return "M " + " ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def render_svg(
    land: list[Polygon],
    lakes: list[Polygon],
    bounds: tuple[float, float, float, float],
    simplify: float,
    include_lakes: bool,
) -> str:
    land = sorted(land, key=lambda g: g.area, reverse=True)
    land_d = " ".join(svg_path(g, bounds, simplify) for g in land)

    lake_markup = ""
    if include_lakes:
        major_lakes = sorted((g for g in lakes if g.area > 0.003), key=lambda g: g.area, reverse=True)
        lake_markup = "".join(
            f'<path d="{svg_path(g, bounds, max(simplify * 0.65, 0.005))}"/>' for g in major_lakes
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Country map">
<defs>
<linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".55" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
<linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#e2dbad"/><stop offset=".52" stop-color="#d4cc9b"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/><feOffset in="b" dy="3" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .14 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>
<ellipse cx="220" cy="130" rx="300" ry="125" fill="#fbf7ec" opacity=".34"/><ellipse cx="1000" cy="650" rx="330" ry="155" fill="#d5e4e2" opacity=".35"/>
<path d="{land_d}" fill="url(#land)" stroke="#31576a" stroke-width="1.65" stroke-linejoin="round" stroke-linecap="round" filter="url(#shadow)"/>
{f'<g fill="#e5eceb" stroke="#6f8a92" stroke-opacity=".35" stroke-width=".65">{lake_markup}</g>' if lake_markup else ''}
</svg>'''


def main() -> None:
    args = parse_args()
    west, south, east, north = args.bounds
    bounds = (west, south, east, north)

    if args.source == "gshhs":
        land, lakes = load_gshhs(bounds, args.resolution)
    else:
        if not args.dataset or not args.country_name:
            raise ValueError("--dataset and --country-name are required for natural-earth")
        land, lakes = load_natural_earth(args.dataset, args.country_name)

    svg = render_svg(land, lakes, bounds, args.simplify, args.include_lakes)
    byte_size = len(svg.encode("utf-8"))
    if args.max_bytes and byte_size > args.max_bytes:
        raise ValueError(
            f"Generated SVG is {byte_size} bytes, exceeding --max-bytes {args.max_bytes}. "
            "Increase --simplify or reduce optional detail; do not publish a truncated asset."
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"Wrote {output} ({STYLE_VERSION}, {byte_size} bytes)")


if __name__ == "__main__":
    main()
