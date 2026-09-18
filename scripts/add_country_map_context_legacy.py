#!/usr/bin/env python3
"""Migration-only adapters for approved legacy Country SVG layouts.

This module exists only to migrate already-approved historical map assets to the
shared Azerbaijan sea/surrounding-land appearance. It never changes target
country geometry, Country JSON, coordinates, markers, or publication state.
New Countries must use the canonical shared generator instead.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.ops import unary_union

import add_country_map_context as core
import generate_country_map as mapgen

SVG_NS = "{http://www.w3.org/2000/svg}"
LEGACY_SLUGS = {
    "antiguabarbuda", "bahrain", "brunei", "hong-kong", "maldives", "qatar", "russia"
}
SEA = core.SEA_COLORS


def _fmt(v: float) -> str:
    return f"{v:g}"


def _bounds(obj):
    return tuple(float(obj[k]) for k in ("west", "south", "east", "north"))


def _rect(obj):
    return tuple(float(obj[k]) for k in ("x", "y", "width", "height"))


def _replace_gradient(svg: str, gradient_id: str, accepted: tuple[tuple[str, str, str], ...]) -> str:
    pattern = re.compile(r'<linearGradient\b[^>]*\bid="' + re.escape(gradient_id) + r'"[^>]*>.*?</linearGradient>', re.DOTALL)
    match = pattern.search(svg)
    if not match:
        raise ValueError(f"Missing named {gradient_id} gradient")
    colors = tuple(re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', match.group()))
    if colors == SEA:
        return svg
    if colors not in accepted:
        raise ValueError(f"Unrecognized {gradient_id} palette: explicit review required")
    replacement = match.group()
    for old, new in zip(colors, SEA):
        replacement = replacement.replace(f'stop-color="{old}"', f'stop-color="{new}"', 1)
    return svg[:match.start()] + replacement + svg[match.end():]


def _sea_rect(svg: str, fill_id: str = "sea"):
    pattern = re.compile(r'<rect\b(?=[^>]*\bfill="url\(#' + re.escape(fill_id) + r'\)")[^>]*/>')
    matches = list(pattern.finditer(svg))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {fill_id} background rectangle")
    return matches[0]


def _context_markup(path: str, *, transform: str | None = None, attr: str = "") -> str:
    if not path:
        return '<g id="geographic-context"/>'
    transform_attr = f' transform="{transform}"' if transform else ""
    data_attr = f' data-map-context-legacy="{attr}"' if attr else ' data-map-context-legacy="true"'
    return (f'<g id="geographic-context"{transform_attr}><path{data_attr} d="{path}" '
            f'fill="{core.CONTEXT_FILL}" fill-rule="evenodd" stroke="{core.CONTEXT_STROKE}" '
            'stroke-width="1" stroke-linejoin="round"/></g>')


def _insert_after(svg: str, match, markup: str) -> str:
    return svg[:match.end()] + "\n" + markup + svg[match.end():]


def _split_context_geometry(bounds, resolution):
    """Fetch wide longitude spans as <=180° verified GSHHS pieces."""
    west, south, east, north = bounds
    if east - west <= 180:
        return core.context_geometry(bounds, resolution)
    if not (-360 <= west < east <= 360 and east - west <= 360 and -89 <= south < north <= 89):
        raise ValueError("Unsupported wide map extent")
    pieces = []
    start = west
    while start < east - 1e-9:
        stop = min(start + 179.5, east)
        piece = core.context_geometry((start, south, stop, north), resolution)
        if piece is not None and not piece.is_empty:
            pieces.append(piece)
        start = stop
    return unary_union(pieces) if pieces else None


def _simple_context(svg: str, config: dict, resolution: str, *, fill_id: str = "sea", gradient_id: str = "sea") -> str:
    root = ET.fromstring(svg)
    if root.attrib.get("data-map-projection") != "local-equirectangular-fit-v1":
        raise ValueError("Legacy single-map adapter requires local-equirectangular-fit-v1")
    bounds = _bounds(config["map"]["bounds"])
    canvas = core.canvas_bounds(bounds)
    geometry = _split_context_geometry(canvas, resolution)
    path = core.make_context_path(geometry, bounds, 0.003)
    accepted = (("#eef2ef", "#e4eceb", "#dce7e7"),)
    svg = _replace_gradient(svg, gradient_id, accepted)
    bg = _sea_rect(svg, fill_id)
    return _insert_after(svg, bg, _context_markup(path))


def _brunei(svg: str, config: dict, resolution: str) -> str:
    root = ET.fromstring(svg)
    targets = [p for p in root.iter(SVG_NS + "path") if p.attrib.get("fill") == "url(#country)"]
    if len(targets) != 1 or any("transform" in p.attrib for p in targets):
        raise ValueError("Brunei legacy country geometry no longer matches reviewed layout")
    old = (("#f1f2ee", "#eceee9", "#e7eae5"),)
    svg = _replace_gradient(svg, "background", old)
    bounds = _bounds(config["map"]["bounds"])
    path = core.make_context_path(_split_context_geometry(core.canvas_bounds(bounds), resolution), bounds, 0.003)
    bg = _sea_rect(svg, "background")
    return _insert_after(svg, bg, _context_markup(path, attr="alternate-country-gradient"))


def _hong_kong(svg: str, config: dict, resolution: str) -> str:
    root = ET.fromstring(svg)
    shape = root.find(f".//*[@id='land-shape']")
    uses = [u for u in root.iter(SVG_NS + "use")
            if u.attrib.get("href") == "#land-shape" and u.attrib.get("fill") == "url(#land)"]
    if shape is None or len(list(shape.iter(SVG_NS + "path"))) < 1 or len(uses) != 1:
        raise ValueError("Hong Kong referenced land-shape layout changed")
    return _simple_context(svg, config, resolution)


def _raw_grid_path(geometry, bounds):
    if geometry is None or geometry.is_empty:
        return ""
    west, south, east, north = bounds
    def ring(coords):
        points = []
        for lon, lat in coords:
            x = round((lon - west) / (east - west) * mapgen.WIDTH, 1)
            y = round((north - lat) / (north - south) * mapgen.HEIGHT, 1)
            point = (x, y)
            if not points or point != points[-1]:
                points.append(point)
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z" if len(points) >= 3 else ""
    parts = []
    for poly in mapgen.polygons_from_geometry(geometry):
        if poly.area <= 0.000002:
            continue
        simple = poly.simplify(0.003, preserve_topology=True)
        for component in mapgen.polygons_from_geometry(simple):
            parts.append(ring(component.exterior.coords))
            parts.extend(ring(h.coords) for h in component.interiors)
    return " ".join(p for p in parts if p)


def _maldives(svg: str, config: dict, resolution: str) -> str:
    root = ET.fromstring(svg)
    targets = [p for p in root.iter(SVG_NS + "path") if p.attrib.get("fill") == "url(#land)"]
    if len(targets) != 1:
        raise ValueError("Maldives reviewed legacy target path count changed")
    transform = targets[0].attrib.get("transform", "")
    match = core.MATRIX.fullmatch(transform.strip())
    if not match:
        raise ValueError("Maldives legacy matrix is no longer axis-aligned")
    a, b, c, d, e, f = map(float, match.groups())
    if abs(b) > 1e-9 or abs(c) > 1e-9 or a <= 0 or d <= 0:
        raise ValueError("Legacy raw-grid transform must be positive axis-aligned")
    bounds = _bounds(config["map"]["bounds"])
    west, south, east, north = bounds
    raw_x0, raw_x1 = (0 - e) / a, (mapgen.WIDTH - e) / a
    raw_y0, raw_y1 = (0 - f) / d, (mapgen.HEIGHT - f) / d
    canvas = (west + raw_x0 / mapgen.WIDTH * (east - west),
              north - raw_y1 / mapgen.HEIGHT * (north - south),
              west + raw_x1 / mapgen.WIDTH * (east - west),
              north - raw_y0 / mapgen.HEIGHT * (north - south))
    geometry = _split_context_geometry(canvas, resolution)
    path = _raw_grid_path(geometry, bounds)
    svg = _replace_gradient(svg, "sea", (("#eef2ef", "#e4eceb", "#dce7e7"),))
    bg = _sea_rect(svg, "sea")
    return _insert_after(svg, bg, _context_markup(path, transform=transform, attr="raw-grid-matrix"))


def _validate_region_rects(regions):
    rects = []
    for region in regions:
        rect = _rect(region["rect"])
        x, y, w, h = rect
        if not (0 <= x and 0 <= y and w > 0 and h > 0 and x + w <= mapgen.WIDTH and y + h <= mapgen.HEIGHT):
            raise ValueError("Legacy region rectangle outside canvas")
        core.frame(_bounds(region["bounds"]), rect)
        for ox, oy, ow, oh in rects:
            if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                raise ValueError("Legacy region rectangles overlap")
        rects.append(rect)


def _loose_multi_region(svg: str, config: dict, resolution: str) -> str:
    root = ET.fromstring(svg)
    if root.attrib.get("data-map-projection") != "multi-region-local-equirectangular-v1":
        raise ValueError("Loose multi-region adapter projection changed")
    regions = config["map"].get("regions") or []
    _validate_region_rects(regions)
    targets, _ = core.approved_land_paths(root)
    if len(targets) < len(regions):
        raise ValueError("Fewer approved target paths than declared legacy regions")
    svg = _replace_gradient(svg, "sea", (("#eef2ef", "#e4eceb", "#dce7e7"),))
    defs = re.search(r"</defs\s*>", svg)
    if not defs:
        raise ValueError("Legacy multi-region map missing defs")
    clips, paths = [], []
    for region in regions:
        rid = region["id"]
        rb = _bounds(region["bounds"])
        rect = _rect(region["rect"])
        x, y, w, h = rect
        clip_id = f"map-context-legacy-{rid}"
        clips.append(f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"/></clipPath>')
        geometry = _split_context_geometry(core.canvas_bounds(rb, rect), resolution)
        d = core.make_context_path(geometry, rb, 0.003, rect)
        paths.append(f'<path data-map-context-legacy="{rid}" d="{d}" clip-path="url(#{clip_id})"/>')
    svg = svg[:defs.start()] + "".join(clips) + svg[defs.start():]
    bg = _sea_rect(svg, "sea")
    markup = (f'<g id="geographic-context" fill="{core.CONTEXT_FILL}" fill-rule="evenodd" '
              f'stroke="{core.CONTEXT_STROKE}" stroke-width="1" stroke-linejoin="round">' + "".join(paths) + "</g>")
    return _insert_after(svg, bg, markup)


def _qatar(svg: str, config: dict, resolution: str) -> str:
    root = ET.fromstring(svg)
    if root.attrib.get("data-map-projection") != "local-equirectangular-fit-v1":
        raise ValueError("Qatar national+inset projection changed")
    regions = config["map"].get("regions") or []
    _validate_region_rects(regions)
    if not regions:
        raise ValueError("Qatar inset region missing")
    svg = _replace_gradient(svg, "sea", (("#eef2ef", "#e4eceb", "#dce7e7"),))
    bounds = _bounds(config["map"]["bounds"])
    main_path = core.make_context_path(_split_context_geometry(core.canvas_bounds(bounds), resolution), bounds, 0.003)
    bg = _sea_rect(svg, "sea")
    svg = _insert_after(svg, bg, _context_markup(main_path, attr="national-base"))
    for region in regions:
        rid = region["id"]
        rb = _bounds(region["bounds"])
        rect = _rect(region["rect"])
        x, y, w, h = rect
        d = core.make_context_path(_split_context_geometry(core.canvas_bounds(rb, rect), resolution), rb, 0.003, rect)
        pattern = re.compile(r'(<g\b[^>]*clip-path="url\(#[^)]+\)"[^>]*>\s*<rect\b[^>]*x="' + re.escape(_fmt(x)) + r'"[^>]*y="' + re.escape(_fmt(y)) + r'"[^>]*width="' + re.escape(_fmt(w)) + r'"[^>]*height="' + re.escape(_fmt(h)) + r'"[^>]*/>)')
        match = pattern.search(svg)
        if not match:
            raise ValueError(f"Inset background for {rid} no longer matches declared rect")
        existing = match.group(1)
        if 'fill="#e7eeee"' in existing:
            existing = existing.replace('fill="#e7eeee"', f'fill="{SEA[1]}"', 1)
        layer = (f'<path data-map-context-legacy="{rid}" d="{d}" fill="{core.CONTEXT_FILL}" fill-rule="evenodd" '
                 f'stroke="{core.CONTEXT_STROKE}" stroke-width="1" stroke-linejoin="round"/>')
        svg = svg[:match.start()] + existing + layer + svg[match.end():]
    return svg


def generate(country_json: Path, input_path: Path, output_path: Path, resolution: str = "i") -> None:
    data = json.loads(country_json.read_text(encoding="utf-8"))
    slug = data.get("slug")
    if slug not in LEGACY_SLUGS:
        raise ValueError(f"No migration-only legacy adapter for {slug}")
    svg = input_path.read_text(encoding="utf-8")
    root = ET.fromstring(svg)
    if root.tag != SVG_NS + "svg" or root.attrib.get("viewBox") != "0 0 1200 760":
        raise ValueError("Legacy adapter requires canonical 1200x760 SVG")
    if root.find(f".//*[@id='geographic-context']") is not None:
        raise ValueError("SVG already contains geographic context")
    if slug == "brunei":
        result = _brunei(svg, data, resolution)
    elif slug == "hong-kong":
        result = _hong_kong(svg, data, resolution)
    elif slug == "maldives":
        result = _maldives(svg, data, resolution)
    elif slug in {"antiguabarbuda", "bahrain"}:
        result = _loose_multi_region(svg, data, resolution)
    elif slug == "qatar":
        result = _qatar(svg, data, resolution)
    elif slug == "russia":
        result = _simple_context(svg, data, resolution)
    else:
        raise AssertionError(slug)
    ET.fromstring(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resolution", choices=("c", "l", "i", "h", "f"), default="i")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new separate preview file")
    generate(args.country_json, args.input, args.output, args.resolution)
    print(f"Created legacy migration preview: {args.output}")


if __name__ == "__main__":
    main()
