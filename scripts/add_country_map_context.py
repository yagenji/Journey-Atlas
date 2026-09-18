#!/usr/bin/env python3
"""Add geographic context to an existing single-region JOURNEY ATLAS SVG.

This is an opt-in post-generation step. It preserves the approved country path,
projection, map bounds, and marker data. It deliberately rejects unfamiliar SVG
structures rather than guessing which geometry represents the target country.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import generate_country_map as mapgen

SEA_COLORS = ("#eaf2f4", "#dcebf0", "#d0e3eb")
CONTEXT_FILL = "#e4e0ce"
CONTEXT_STROKE = "#b6bbaf"
SVG_NS = "{http://www.w3.org/2000/svg}"
SEA_GRADIENT = re.compile(r'<linearGradient\b[^>]*\bid="sea"[^>]*>.*?</linearGradient>', re.DOTALL)
SEA_RECT = re.compile(r'<rect\b(?=[^>]*\bfill="url\(#sea\)")[^>]*/>')


def canvas_bounds(bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Get the geographic extent of *all* 1200 x 760 pixels, not only input bounds.

    Local equirectangular fit often has horizontal/vertical sidebands. Those
    sidebands also require real geographic context, not an artificial cutoff.
    """
    west, south, east, north = bounds
    lon_factor, scale, offset_x, offset_y = mapgen.projection_frame(bounds)
    dx = offset_x / (lon_factor * scale)
    dy = offset_y / scale
    return west - dx, south - dy, east + dx, north + dy


def context_geometry(bounds: tuple[float, float, float, float], resolution: str):
    """GSHHS shoreline topology: level 1/3 land; level 2/4 inland water."""
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -89 <= south < north <= 89):
        raise ValueError("Context crosses the antimeridian or polar limits; review a region-aware map instead")
    basemap = Basemap(
        projection="cyl", llcrnrlon=west, llcrnrlat=south,
        urcrnrlon=east, urcrnrlat=north,
        resolution=resolution, area_thresh=0.1,
    )
    levels: dict[int, list] = {1: [], 2: [], 3: [], 4: []}
    for (xs, ys), level in zip(basemap.coastpolygons, basemap.coastpolygontypes):
        if level not in levels:
            continue
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            levels[level].append(poly)
    if not levels[1]:
        return None
    main_land = unary_union(levels[1])
    if levels[2]:
        main_land = main_land.difference(unary_union(levels[2]))
    if levels[3]:
        main_land = main_land.union(unary_union(levels[3]))
    if levels[4]:
        main_land = main_land.difference(unary_union(levels[4]))
    return main_land.intersection(box(*bounds))


def make_context_path(geometry, bounds: tuple[float, float, float, float], simplify: float) -> str:
    if geometry is None or geometry.is_empty:
        return ""
    polygons = mapgen.polygons_from_geometry(geometry)
    return " ".join(mapgen.polygon_path(p, bounds, simplify) for p in polygons if p.area > 0.000002)


def add_context(svg: str, bounds: tuple[float, float, float, float], path: str, resolution: str) -> str:
    """Modify only the sea gradient and the new context layer; retain target SVG verbatim."""
    root = ET.fromstring(svg)
    if root.tag != SVG_NS + "svg" or root.attrib.get("viewBox") != "0 0 1200 760":
        raise ValueError("Expected an SVG with the canonical 1200 x 760 viewBox")
    if root.attrib.get("data-map-projection") != "local-equirectangular-fit-v1":
        raise ValueError("Unknown map projection: geographic context cannot be aligned safely")
    if root.find(f".//*[@id='geographic-context']") is not None:
        raise ValueError("SVG already has geographic context; refusing duplicate insertion")
    parents = {child: parent for parent in root.iter() for child in parent}
    target_paths = [node for node in root.iter(SVG_NS + "path") if node.attrib.get("fill") == "url(#land)"]
    if len(target_paths) != 1:
        raise ValueError("Expected exactly one explicit target-country path with fill=url(#land)")
    for node in target_paths:
        cursor = node
        while cursor is not None:
            if "transform" in cursor.attrib:
                raise ValueError("Transformed target geometry needs a reviewed projection adapter")
            cursor = parents.get(cursor)
    if not path:
        # Open-ocean islands can have no visible foreign coastline in the viewport.
        path_markup = ""
    else:
        path_markup = (f'<g id="geographic-context"><path d="{path}" fill="{CONTEXT_FILL}" '
                       f'fill-rule="evenodd" stroke="{CONTEXT_STROKE}" stroke-width="1" '
                       'stroke-linejoin="round"/></g>')
    gradient = SEA_GRADIENT.search(svg)
    if not gradient:
        raise ValueError("Missing named sea gradient")
    old_colors = re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', gradient.group())
    if len(old_colors) != 3 or tuple(old_colors) not in (
        ("#eef2ef", "#e4eceb", "#dce7e7"), SEA_COLORS,
    ):
        raise ValueError("Unrecognized sea palette: explicit visual review required")
    new_gradient = gradient.group()
    for old, new in zip(old_colors, SEA_COLORS):
        new_gradient = new_gradient.replace(f'stop-color="{old}"', f'stop-color="{new}"', 1)
    svg = svg[:gradient.start()] + new_gradient + svg[gradient.end():]
    sea_rects = list(SEA_RECT.finditer(svg))
    if len(sea_rects) != 1:
        raise ValueError("Expected exactly one sea background rectangle")
    insertion = sea_rects[0].end()
    source = f'<!-- Geographic context: GSHHS via Basemap; resolution={resolution}; WGS84; canvas-fit bounds. -->'
    result = svg[:insertion] + "\n" + source + "\n" + path_markup + svg[insertion:]
    ET.fromstring(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resolution", choices=("c", "l", "i", "h", "f"), default="i")
    parser.add_argument("--simplify", type=float, default=0.003)
    parser.add_argument("--max-bytes", type=int, default=6000000)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new, separate file; production assets are never overwritten in place")
    if not (0 <= args.simplify <= 0.003):
        parser.error("Use a topology-preserving simplify tolerance between 0 and 0.003 degrees")
    country = json.loads(args.country_json.read_text(encoding="utf-8"))
    config = country["map"]
    if config.get("regions"):
        parser.error("Multi-region maps require per-region reviewed context; refusing global-bounds overlay")
    b = config["bounds"]
    bounds = (float(b["west"]), float(b["south"]), float(b["east"]), float(b["north"]))
    viewport = canvas_bounds(bounds)
    source = args.input.read_text(encoding="utf-8")
    # Preflight the SVG *before* expensive geometry generation.
    add_context(source, bounds, "", args.resolution)
    path = make_context_path(context_geometry(viewport, args.resolution), bounds, args.simplify)
    result = add_context(source, bounds, path, args.resolution)
    if len(result.encode("utf-8")) > args.max_bytes:
        parser.error("Result exceeds max-bytes; review geographic detail instead of truncating SVG")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Created preview: {args.output} ({len(result.encode('utf-8'))} bytes; context resolution {args.resolution})")


if __name__ == "__main__":
    main()
