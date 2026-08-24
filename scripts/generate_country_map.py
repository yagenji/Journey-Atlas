#!/usr/bin/env python3
"""Generate a JOURNEY ATLAS country-map SVG from geographic data.

Examples:
  python scripts/generate_country_map.py \
    --source gshhs --bounds -25.8 62.8 -12.2 67.1 \
    --output assets/images/iceland/map-atlas.svg

  python scripts/generate_country_map.py \
    --source natural-earth --dataset /path/ne_10m_admin_0_countries.shp \
    --country-name Japan --bounds 122 20 154 46 \
    --output assets/images/japan/map-atlas.svg
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

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
        target = land if polygon_type == 1 else lakes if polygon_type == 2 else None
        if target is not None:
            target.extend(polygons_from_geometry(geom))
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

    geometry = match.geometry.unary_union
    land = polygons_from_geometry(geometry)
    lakes: list[Polygon] = []
    for polygon in land:
        for ring in polygon.interiors:
            lakes.append(Polygon(ring))
    return land, lakes


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    x = (lon - west) / (east - west) * WIDTH
    y = (north - lat) / (north - south) * HEIGHT
    return x, y


def svg_path(polygon: Polygon, bounds: tuple[float, float, float, float], simplify: float) -> str:
    geom = polygon.simplify(simplify, preserve_topology=True)
    coords = list(geom.exterior.coords)
    points = [project(lon, lat, bounds) for lon, lat in coords]
    return "M " + " ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def render_svg(
    land: Iterable[Polygon],
    lakes: Iterable[Polygon],
    bounds: tuple[float, float, float, float],
    simplify: float,
) -> str:
    land = sorted(land, key=lambda g: g.area, reverse=True)
    lakes = sorted((g for g in lakes if g.area > 0.003), key=lambda g: g.area, reverse=True)

    land_paths = [svg_path(g, bounds, simplify) for g in land]
    lake_paths = [svg_path(g, bounds, max(simplify * 0.65, 0.005)) for g in lakes]
    clip = "".join(f'<path d="{path}"/>' for path in land_paths)
    land_shapes = "".join(f'<path d="{path}" class="land"/>' for path in land_paths)
    lake_shapes = "".join(f'<path d="{path}" class="lake"/>' for path in lake_paths)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Country map">
<defs>
<linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".52" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
<linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#ddd5a6"/><stop offset=".55" stop-color="#d2ca98"/><stop offset="1" stop-color="#c7be88"/></linearGradient>
<radialGradient id="wash1" cx="32%" cy="38%" r="44%"><stop offset="0" stop-color="#b8c3a1" stop-opacity=".28"/><stop offset="1" stop-color="#b8c3a1" stop-opacity="0"/></radialGradient>
<radialGradient id="wash2" cx="68%" cy="58%" r="42%"><stop offset="0" stop-color="#d6b883" stop-opacity=".2"/><stop offset="1" stop-color="#d6b883" stop-opacity="0"/></radialGradient>
<filter id="paper" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="2" seed="7" result="n"/><feColorMatrix in="n" type="saturate" values="0" result="g"/><feComponentTransfer in="g" result="f"><feFuncA type="table" tableValues="0 .035"/></feComponentTransfer><feBlend in="SourceGraphic" in2="f" mode="multiply"/></filter>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="5" result="b"/><feOffset in="b" dy="4" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .18 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
<clipPath id="landClip">{clip}</clipPath>
<style>.land{{fill:url(#land);stroke:#31576a;stroke-width:1.65;stroke-linejoin:round;stroke-linecap:round}}.lake{{fill:#e5eceb;stroke:#6f8a92;stroke-opacity:.35;stroke-width:.65}}</style>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sea)"/>
<g opacity=".38"><ellipse cx="250" cy="170" rx="250" ry="110" fill="#f8f4e8"/><ellipse cx="950" cy="620" rx="330" ry="150" fill="#d8e6e4"/></g>
<g filter="url(#shadow)">{land_shapes}</g>
<g clip-path="url(#landClip)" filter="url(#paper)"><rect width="{WIDTH}" height="{HEIGHT}" fill="url(#wash1)"/><rect width="{WIDTH}" height="{HEIGHT}" fill="url(#wash2)"/></g>
<g>{lake_shapes}</g>
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

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_svg(land, lakes, bounds, args.simplify), encoding="utf-8")
    print(f"Wrote {output} ({STYLE_VERSION})")


if __name__ == "__main__":
    main()
