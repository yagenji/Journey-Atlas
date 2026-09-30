#!/usr/bin/env python3
"""Add source-backed surrounding-country borders to a JOURNEY ATLAS map SVG.

The highlighted Country geometry is never modified. This adds only Natural
Earth 1:10m Admin-0 land-boundary linework below the target Country, projected
with the same canonical local-equirectangular fit and clipped to the visible
1200x760 canvas.
"""
from __future__ import annotations

import argparse
import json
import math
import urllib.request
from pathlib import Path

from shapely.geometry import GeometryCollection, LineString, MultiLineString, box, shape

WIDTH = 1200
HEIGHT = 760
GROUP_ID = "context-national-borders"
STROKE = "#b6bbaf"
STROKE_WIDTH = "1"
NATURAL_EARTH_REF = "ca96624a56bd078437bca8184e78163e5039ad19"
NATURAL_EARTH_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{NATURAL_EARTH_REF}/geojson/ne_10m_admin_0_boundary_lines_land.geojson"
)


def frame(bounds: dict[str, float]) -> tuple[float, float, float, float]:
    west, south, east, north = (float(bounds[k]) for k in ("west", "south", "east", "north"))
    if not (west < east and south < north):
        raise ValueError("Invalid map bounds")
    factor = math.cos(math.radians((south + north) / 2))
    if factor <= 0:
        raise ValueError("Unsupported polar local projection")
    scale = min(WIDTH / ((east - west) * factor), HEIGHT / (north - south))
    draw_w = (east - west) * factor * scale
    draw_h = (north - south) * scale
    return factor, scale, (WIDTH - draw_w) / 2, (HEIGHT - draw_h) / 2


def canvas_bounds(bounds: dict[str, float]) -> tuple[float, float, float, float]:
    west, south, east, north = (float(bounds[k]) for k in ("west", "south", "east", "north"))
    factor, scale, ox, oy = frame(bounds)
    return (
        west - ox / (factor * scale),
        south - (HEIGHT - (oy + (north - south) * scale)) / scale,
        east + (WIDTH - (ox + (east - west) * factor * scale)) / (factor * scale),
        north + oy / scale,
    )


def project(lon: float, lat: float, bounds: dict[str, float]) -> tuple[float, float]:
    west, _, _, north = (float(bounds[k]) for k in ("west", "south", "east", "north"))
    factor, scale, ox, oy = frame(bounds)
    return ox + (lon - west) * factor * scale, oy + (north - lat) * scale


def load_boundaries(dataset: Path | None = None):
    if dataset is not None:
        source = json.loads(dataset.read_text(encoding="utf-8"))
    else:
        with urllib.request.urlopen(NATURAL_EARTH_URL) as response:
            source = json.load(response)
    for feature in source.get("features", []):
        geometry = shape(feature["geometry"])
        if not geometry.is_empty:
            yield geometry


def _line_parts(geometry):
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, MultiLineString):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        return [g for g in geometry.geoms if isinstance(g, LineString)]
    return []


def _fmt(value: float) -> str:
    value = round(value, 1)
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def make_border_path(
    bounds: dict[str, float],
    simplify_px: float = 0.6,
    dataset: Path | None = None,
) -> str:
    west, south, east, north = canvas_bounds(bounds)
    viewport = box(west, south, east, north)
    parts: list[str] = []

    for geometry in load_boundaries(dataset):
        for line in _line_parts(geometry):
            for shift in (-360.0, 0.0, 360.0):
                shifted = LineString((lon + shift, lat) for lon, lat in line.coords)
                if not shifted.bounds or (
                    shifted.bounds[2] < west or shifted.bounds[0] > east
                    or shifted.bounds[3] < south or shifted.bounds[1] > north
                ):
                    continue
                clipped = shifted.intersection(viewport)
                for piece in _line_parts(clipped):
                    projected = LineString(project(lon, lat, bounds) for lon, lat in piece.coords)
                    if simplify_px:
                        projected = projected.simplify(simplify_px, preserve_topology=False)
                    coords: list[tuple[float, float]] = []
                    for x, y in projected.coords:
                        x, y = round(x, 1), round(y, 1)
                        if -0.2 <= x <= WIDTH + 0.2 and -0.2 <= y <= HEIGHT + 0.2:
                            if not coords or coords[-1] != (x, y):
                                coords.append((x, y))
                    if len(coords) >= 2:
                        parts.append("M" + " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in coords))
    return " ".join(parts)


def add_borders(
    svg: str,
    bounds: dict[str, float],
    simplify_px: float = 0.6,
    dataset: Path | None = None,
) -> str:
    if f'id="{GROUP_ID}"' in svg:
        raise ValueError("SVG already contains surrounding-country borders")
    if 'viewBox="0 0 1200 760"' not in svg:
        raise ValueError("Expected canonical 1200x760 SVG")
    if 'data-map-projection="local-equirectangular-fit-v1"' not in svg:
        raise ValueError("Only canonical single-region local projection is supported")

    path = make_border_path(bounds, simplify_px, dataset)
    if not path:
        return svg

    target_index = svg.find('fill="url(#land)"')
    if target_index < 0:
        raise ValueError("Approved target land is missing")
    insert_at = svg.rfind("<", 0, target_index)
    if insert_at < 0:
        raise ValueError("Cannot locate target land element")

    source = (
        "<!-- Surrounding national borders: Natural Earth 1:10m Admin-0 boundary lines land; "
        f"nvkelso/natural-earth-vector {NATURAL_EARTH_REF}; public domain; WGS84; "
        "clipped to visible canvas. -->\n"
    )
    group = (
        f'<g id="{GROUP_ID}" fill="none" stroke="{STROKE}" stroke-width="{STROKE_WIDTH}" '
        'stroke-linejoin="round" stroke-linecap="round" aria-hidden="true">'
        f'<path d="{path}"/></g>\n'
    )
    return svg[:insert_at] + source + group + svg[insert_at:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", type=Path, help="Optional pinned Natural Earth boundary-lines GeoJSON")
    parser.add_argument("--simplify-px", type=float, default=0.6)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new file; production assets are not overwritten in place")
    if not (0 <= args.simplify_px <= 1.0):
        parser.error("--simplify-px must be between 0 and 1.0")

    country = json.loads(args.country_json.read_text(encoding="utf-8"))
    if country.get("map", {}).get("regions"):
        parser.error("Multi-region maps require explicit region-aware review")
    bounds = country["map"]["bounds"]
    svg = args.input.read_text(encoding="utf-8")
    result = add_borders(svg, bounds, args.simplify_px, args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Created {args.output} ({len(result.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
