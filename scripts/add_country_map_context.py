#!/usr/bin/env python3
"""Preview sea and GSHHS context around approved Country-map paths.

Existing target SVG paths and markers stay byte-for-byte unchanged. Supports the
canonical single-region projection, its checked legacy aspect-fit matrix, and
explicit map.regions. Unsupported layouts fail closed; output is preview-only.
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
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
MATRIX = re.compile(r"matrix\(\s*([-+\d.eE]+)[, ]+([-+\d.eE]+)[, ]+([-+\d.eE]+)[, ]+([-+\d.eE]+)[, ]+([-+\d.eE]+)[, ]+([-+\d.eE]+)\s*\)\Z")


def frame(bounds, rect=None):
    west, south, east, north = bounds
    x, y, width, height = rect or (0, 0, mapgen.WIDTH, mapgen.HEIGHT)
    if not all(math.isfinite(v) for v in (*bounds, x, y, width, height)):
        raise ValueError("Map bounds/rect must be finite")
    if not (west < east and south < north and width > 0 and height > 0):
        raise ValueError("Invalid map bounds/rect")
    factor = math.cos(math.radians((south + north) / 2))
    if factor <= 0:
        raise ValueError("Unsupported local projection at polar latitude")
    scale = min(width / ((east - west) * factor), height / (north - south))
    dx = (width - (east - west) * factor * scale) / 2
    dy = (height - (north - south) * scale) / 2
    return factor, scale, x + dx, y + dy


def canvas_bounds(bounds, rect=None):
    """Full pixel rect includes projected sidebands, avoiding inland cutoffs."""
    x, y, width, height = rect or (0, 0, mapgen.WIDTH, mapgen.HEIGHT)
    factor, scale, origin_x, origin_y = frame(bounds, rect)
    west, south, east, north = bounds
    return (west - (origin_x - x) / (factor * scale),
            south - ((y + height) - (origin_y + (north - south) * scale)) / scale,
            east + ((x + width) - (origin_x + (east - west) * factor * scale)) / (factor * scale),
            north + (origin_y - y) / scale)


def context_geometry(bounds, resolution):
    """GSHHS land/lake nesting; allow normalized longitude such as Alaska -190."""
    from mpl_toolkits.basemap import Basemap
    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 180 and -89 <= south < north <= 89):
        raise ValueError("Unsupported longitude span or polar canvas; use verified regional projection")
    basemap = Basemap(projection="cyl", llcrnrlon=west, llcrnrlat=south,
                      urcrnrlon=east, urcrnrlat=north,
                      resolution=resolution, area_thresh=0.1)
    levels = {1: [], 2: [], 3: [], 4: []}
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
    land = unary_union(levels[1])
    if levels[2]:
        land = land.difference(unary_union(levels[2]))
    if levels[3]:
        land = land.union(unary_union(levels[3]))
    if levels[4]:
        land = land.difference(unary_union(levels[4]))
    return land.intersection(box(*bounds))


def make_context_path(geometry, bounds, simplify, rect=None):
    if geometry is None or geometry.is_empty:
        return ""
    if rect is None:
        return " ".join(mapgen.polygon_path(p, bounds, simplify)
                        for p in mapgen.polygons_from_geometry(geometry) if p.area > 0.000002)
    factor, scale, origin_x, origin_y = frame(bounds, rect)
    west, south, east, north = bounds

    def ring(coords):
        points = []
        for lon, lat in coords:
            point = (round(origin_x + (lon - west) * factor * scale, 1),
                     round(origin_y + (north - lat) * scale, 1))
            if not points or point != points[-1]:
                points.append(point)
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z" if len(points) >= 3 else ""

    paths = []
    for poly in mapgen.polygons_from_geometry(geometry):
        if poly.area <= 0.000002:
            continue
        simple = poly.simplify(simplify, preserve_topology=True) if simplify else poly
        for component in mapgen.polygons_from_geometry(simple):
            paths.append(ring(component.exterior.coords))
            paths.extend(ring(hole.coords) for hole in component.interiors)
    return " ".join(part for part in paths if part)


def validate_single_target(root, bounds):
    parents = {child: parent for parent in root.iter() for child in parent}
    targets = [node for node in root.iter(SVG_NS + "path") if node.attrib.get("fill") == "url(#land)"]
    if len(targets) != 1:
        raise ValueError("Expected exactly one explicit target-country path with fill=url(#land)")
    transforms = []
    cursor = targets[0]
    while cursor is not None:
        if "transform" in cursor.attrib:
            transforms.append(cursor.attrib["transform"])
        cursor = parents.get(cursor)
    if not transforms:
        return
    # Accept only the exact legacy longitude-aspect correction used by approved
    # Iceland-like SVGs. A free transform has no reliable geographic inverse.
    if len(transforms) != 1:
        raise ValueError("Unrecognized target transform chain; review geographic projection")
    match = MATRIX.fullmatch(transforms[0].strip())
    factor, scale, x, y = frame(bounds)
    west, south, east, north = bounds
    expected = (factor * scale * (east - west) / mapgen.WIDTH, 0.0, 0.0,
                scale * (north - south) / mapgen.HEIGHT, x, y)
    if not match or any(abs(float(actual) - correct) > 0.002
                        for actual, correct in zip(match.groups(), expected)):
        raise ValueError("Transformed target geometry does not match canonical aspect-fit matrix")


def validate_regions(root, regions):
    if not regions or not isinstance(regions, list):
        raise ValueError("Multi-region SVG requires map.regions")
    groups = [node for node in root.iter(SVG_NS + "g") if "data-map-region" in node.attrib]
    group_ids = [node.attrib["data-map-region"] for node in groups]
    ids = [region.get("id") for region in regions]
    if (len(set(ids)) != len(ids) or any(not isinstance(identifier, str) or not ID.fullmatch(identifier)
                                        for identifier in ids)
            or sorted(ids) != sorted(group_ids)):
        raise ValueError("Region groups must match JSON map.regions exactly")
    targets = [path for path in root.iter(SVG_NS + "path") if path.attrib.get("fill") == "url(#land)"]
    region_targets = [path for group in groups for path in group.iter(SVG_NS + "path")
                      if path.attrib.get("fill") == "url(#land)"]
    if not targets or len(targets) != len(region_targets):
        raise ValueError("Every approved country path must belong to one declared region")
    rectangles = []
    for region in regions:
        bounds = region["bounds"]
        b = tuple(float(bounds[key]) for key in ("west", "south", "east", "north"))
        r = region["rect"]
        rect = tuple(float(r[key]) for key in ("x", "y", "width", "height"))
        x, y, width, height = rect
        frame(b, rect)
        if not (0 <= x and 0 <= y and x + width <= mapgen.WIDTH and y + height <= mapgen.HEIGHT):
            raise ValueError("Region rect outside 1200x760 canvas")
        for ox, oy, ow, oh in rectangles:
            if x < ox + ow and ox < x + width and y < oy + oh and oy < y + height:
                raise ValueError("Overlapping map regions require explicit inset review")
        rectangles.append(rect)


def add_context(svg, bounds, path, resolution, regions=None):
    """Insert context underneath original target paths without rewriting them."""
    root = ET.fromstring(svg)
    if root.tag != SVG_NS + "svg" or root.attrib.get("viewBox") != "0 0 1200 760":
        raise ValueError("Expected an SVG with the canonical 1200 x 760 viewBox")
    if root.find(f".//*[@id='geographic-context']") is not None:
        raise ValueError("SVG already has geographic context; refusing duplicate insertion")
    if regions:
        if root.attrib.get("data-map-projection") != "multi-region-local-equirectangular-fit-v1":
            raise ValueError("Region SVG projection does not match map.regions")
        validate_regions(root, regions)
    else:
        if root.attrib.get("data-map-projection") != "local-equirectangular-fit-v1":
            raise ValueError("Unknown map projection: geographic context cannot be aligned safely")
        validate_single_target(root, bounds)
    gradient = SEA_GRADIENT.search(svg)
    if not gradient:
        raise ValueError("Missing named sea gradient")
    old_colors = re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', gradient.group())
    if len(old_colors) != 3 or tuple(old_colors) not in (("#eef2ef", "#e4eceb", "#dce7e7"), SEA_COLORS):
        raise ValueError("Unrecognized sea palette: explicit visual review required")
    replacement = gradient.group()
    for old, new in zip(old_colors, SEA_COLORS):
        replacement = replacement.replace(f'stop-color="{old}"', f'stop-color="{new}"', 1)
    svg = svg[:gradient.start()] + replacement + svg[gradient.end():]
    sea_rects = list(SEA_RECT.finditer(svg))
    if len(sea_rects) != 1:
        raise ValueError("Expected exactly one sea background rectangle")
    if regions:
        if not isinstance(path, dict) or set(path) != {region["id"] for region in regions}:
            raise ValueError("Region context paths must match all declared regions")
        defs = re.search(r"</defs\s*>", svg)
        if not defs:
            raise ValueError("Missing SVG defs for region clips")
        clips = []
        layers = []
        for region in regions:
            identifier = region["id"]
            x, y, w, h = (float(region["rect"][key]) for key in ("x", "y", "width", "height"))
            clips.append(f'<clipPath id="map-context-clip-{identifier}" clipPathUnits="userSpaceOnUse">'
                         f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/></clipPath>')
            if path[identifier]:
                layers.append(f'<path data-map-context-region="{identifier}" d="{path[identifier]}" '
                              f'clip-path="url(#map-context-clip-{identifier})"/>')
        svg = svg[:defs.start()] + "".join(clips) + svg[defs.start():]
        markup = (f'<g id="geographic-context" fill="{CONTEXT_FILL}" fill-rule="evenodd" '
                  f'stroke="{CONTEXT_STROKE}" stroke-width="1" stroke-linejoin="round">'
                  + "".join(layers) + "</g>") if layers else ""
    else:
        if not isinstance(path, str):
            raise ValueError("Single-region map expects one context path")
        markup = (f'<g id="geographic-context"><path d="{path}" fill="{CONTEXT_FILL}" '
                  f'fill-rule="evenodd" stroke="{CONTEXT_STROKE}" stroke-width="1" '
                  'stroke-linejoin="round"/></g>') if path else ""
    sea_rect = SEA_RECT.search(svg)
    source = f'<!-- Geographic context: GSHHS via Basemap; resolution={resolution}; WGS84; canvas-fit bounds. -->'
    result = svg[:sea_rect.end()] + "\n" + source + "\n" + markup + svg[sea_rect.end():]
    ET.fromstring(result)
    return result


def main():
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
        parser.error("Simplify must be between 0 and 0.003 degrees")
    config = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]
    b = config["bounds"]
    bounds = tuple(float(b[key]) for key in ("west", "south", "east", "north"))
    regions = config.get("regions")
    source = args.input.read_text(encoding="utf-8")
    preflight = {region["id"]: "" for region in regions} if regions else ""
    add_context(source, bounds, preflight, args.resolution, regions)
    if regions:
        paths = {}
        for region in regions:
            b = region["bounds"]
            rb = tuple(float(b[key]) for key in ("west", "south", "east", "north"))
            r = region["rect"]
            rect = tuple(float(r[key]) for key in ("x", "y", "width", "height"))
            paths[region["id"]] = make_context_path(
                context_geometry(canvas_bounds(rb, rect), args.resolution), rb, args.simplify, rect)
    else:
        paths = make_context_path(context_geometry(canvas_bounds(bounds), args.resolution), bounds, args.simplify)
    result = add_context(source, bounds, paths, args.resolution, regions)
    if len(result.encode("utf-8")) > args.max_bytes:
        parser.error("Result exceeds max-bytes; review geographic detail instead of truncating SVG")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Created preview: {args.output} ({len(result.encode('utf-8'))} bytes; context resolution {args.resolution})")


if __name__ == "__main__":
    main()
