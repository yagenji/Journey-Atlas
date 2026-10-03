#!/usr/bin/env python3
"""Add missing major inland-water geometry to existing JOURNEY ATLAS maps.

Uses verified GSHHS/GSHHG level-2 inland-water geometry. Existing reviewed
``inland-water`` layers are preserved byte-for-byte. The tool changes no
coastline, island, administrative-boundary, marker or label coordinates.
"""
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import cairosvg
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import add_country_map_context as ctx
import validate_country_map_v6 as mapcheck

SVG_NS = "{http://www.w3.org/2000/svg}"
WIDTH, HEIGHT = 1200, 760
MIN_LAKE_PIXELS = 1000.0
MIN_LAKE_WIDTH = 10.0
MIN_LAKE_HEIGHT = 10.0
WATER_PASS = 0.70
WATER_FILL = "#e5eceb"
WATER_STROKE = "#6f8a92"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--country-json", required=True, type=Path)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--resolution", default="i", choices=("c", "l", "i", "h", "f"))
    p.add_argument("--report", type=Path)
    return p.parse_args()


def _rings_from_d(d: str) -> list[Polygon]:
    """Parse the linear M/L/H/V/Z syntax already supported by map QA."""
    polygons = mapcheck.parse_polygons(d)
    if not polygons:
        raise ValueError("No supported linear target-country geometry")
    result = []
    for points in polygons:
        poly = Polygon(points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty and poly.area > 0:
            result.extend(ctx.mapgen.polygons_from_geometry(poly))
    return result


def _effective_fill(node, parents):
    cursor = node
    while cursor is not None:
        if "fill" in cursor.attrib:
            return cursor.attrib["fill"]
        cursor = parents.get(cursor)
    return None


def _target_geometry(root: ET.Element):
    parents = {child: parent for parent in root.iter() for child in parent}
    targets = []
    for node in root.iter(SVG_NS + "path"):
        if _effective_fill(node, parents) != "url(#land)" or not node.get("d"):
            continue
        local = mapcheck.parse_transform_matrix(node.get("transform", ""))
        if local is None:
            raise ValueError("Unsupported target path transform")
        ancestor = parents.get(node)
        chain = []
        while ancestor is not None:
            transform = mapcheck.parse_transform_matrix(ancestor.get("transform", ""))
            if transform is None:
                raise ValueError("Unsupported target ancestor transform")
            chain.append(transform)
            ancestor = parents.get(ancestor)
        matrix = mapcheck.IDENTITY
        for transform in reversed(chain):
            matrix = mapcheck.affine_multiply(matrix, transform)
        matrix = mapcheck.affine_multiply(matrix, local)
        for poly in _rings_from_d(node.get("d", "")):
            points = [mapcheck.apply_affine(matrix, point) for point in poly.exterior.coords]
            converted = Polygon(points)
            if not converted.is_valid:
                converted = converted.buffer(0)
            if not converted.is_empty:
                targets.extend(ctx.mapgen.polygons_from_geometry(converted))
    if not targets:
        raise ValueError("No supported target-country land geometry found")
    return unary_union(targets)


def _frames(config: dict):
    regions = (config.get("map") or {}).get("regions")
    if regions:
        return [(
            r["id"],
            tuple(float(r["bounds"][k]) for k in ("west", "south", "east", "north")),
            tuple(float(r["rect"][k]) for k in ("x", "y", "width", "height")),
        ) for r in regions]
    b = config["map"]["bounds"]
    return [("main", tuple(float(b[k]) for k in ("west", "south", "east", "north")), None)]


def _gshhs_lakes(bounds, resolution: str):
    from mpl_toolkits.basemap import Basemap
    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 180 and -89 <= south < north <= 89):
        raise ValueError("Unsupported map bounds for shared lake normalization")
    m = Basemap(projection="cyl", llcrnrlon=west, llcrnrlat=south,
                urcrnrlon=east, urcrnrlat=north,
                resolution=resolution, area_thresh=0.1)
    lakes = []
    for (xs, ys), level in zip(m.coastpolygons, m.coastpolygontypes):
        if level != 2:
            continue
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            lakes.extend(ctx.mapgen.polygons_from_geometry(poly))
    return lakes


def _project_polygon(poly, bounds, rect):
    factor, scale, ox, oy = ctx.frame(bounds, rect)
    west, south, east, north = bounds
    def ring(coords):
        return [(ox + (lon - west) * factor * scale, oy + (north - lat) * scale)
                for lon, lat in coords]
    result = Polygon(ring(poly.exterior.coords), [ring(h.coords) for h in poly.interiors])
    return result.buffer(0) if not result.is_valid else result


def _path(poly):
    def ring(coords):
        pts = []
        for x, y in coords:
            point = (round(float(x), 1), round(float(y), 1))
            if not pts or point != pts[-1]:
                pts.append(point)
        return ("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z") if len(pts) >= 3 else ""
    return " ".join(filter(None, [ring(poly.exterior.coords), *[ring(h.coords) for h in poly.interiors]]))


def _mask(poly):
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(round(x), round(y)) for x, y in poly.exterior.coords], fill=255)
    for hole in poly.interiors:
        draw.polygon([(round(x), round(y)) for x, y in hole.coords], fill=0)
    return mask


def _is_water(rgb):
    r, g, b = rgb[:3]
    return b >= 212 and g >= 218 and g - r >= 2 and b - r >= 3


def _coverage(image, poly):
    mask = _mask(poly)
    bbox = mask.getbbox()
    if bbox is None:
        return 0.0
    px, mp = image.load(), mask.load()
    water = total = 0
    for y in range(max(0, bbox[1]), min(HEIGHT, bbox[3])):
        for x in range(max(0, bbox[0]), min(WIDTH, bbox[2])):
            if mp[x, y]:
                total += 1
                water += int(_is_water(px[x, y]))
    return water / total if total else 0.0


def _material(poly):
    minx, miny, maxx, maxy = poly.bounds
    return (poly.area >= MIN_LAKE_PIXELS and maxx - minx >= MIN_LAKE_WIDTH
            and maxy - miny >= MIN_LAKE_HEIGHT and maxx > 0 and maxy > 0
            and minx < WIDTH and miny < HEIGHT)


def _insert(source: str, markup: str):
    anchors = ('<path id="target-country-boundary-overlay"', '<path id="neighbor-borders"',
               '<g id="country-boundaries"', '<g id="boundary')
    positions = [source.find(a) for a in anchors if source.find(a) >= 0]
    if positions:
        pos = min(positions)
        return source[:pos] + markup + "\n" + source[pos:]
    close = source.rfind("</svg>")
    if close < 0:
        raise ValueError("SVG closing tag missing")
    return source[:close] + markup + "\n" + source[close:]


def normalize(source: str, config: dict, resolution: str):
    root = ET.fromstring(source)
    if root.tag != SVG_NS + "svg" or root.get("viewBox") != "0 0 1200 760":
        raise ValueError("Expected canonical 1200x760 SVG")
    if root.get("data-map-projection") not in ("local-equirectangular-fit-v1", "multi-region-local-equirectangular-fit-v1"):
        raise ValueError("Unsupported projection for shared lake normalization")
    if root.find(".//*[@id='inland-water']") is not None:
        return source, {"changed": False, "missing_lakes": 0, "reason": "reviewed_inland_water"}
    if root.find(".//*[@id='inland-water-auto']") is not None:
        return source, {"changed": False, "missing_lakes": 0, "reason": "already_normalized"}

    target = _target_geometry(root)
    raster = cairosvg.svg2png(bytestring=source.encode(), output_width=WIDTH, output_height=HEIGHT)
    image = Image.open(io.BytesIO(raster)).convert("RGB")
    missing, seen = [], set()
    frame_list = _frames(config)
    for frame_id, bounds, rect in frame_list:
        for lake in _gshhs_lakes(ctx.canvas_bounds(bounds, rect), resolution):
            projected = _project_polygon(lake, bounds, rect).intersection(box(0, 0, WIDTH, HEIGHT))
            for part in ctx.mapgen.polygons_from_geometry(projected):
                if part.is_empty or not _material(part):
                    continue
                overlap = part.intersection(target).area
                if overlap < max(40.0, part.area * 0.08):
                    continue
                rep = part.representative_point()
                key = (frame_id, round(rep.x, 1), round(rep.y, 1), round(part.area, 1))
                if key in seen:
                    continue
                seen.add(key)
                coverage = _coverage(image, part)
                if coverage >= WATER_PASS:
                    continue
                missing.append({"frame": frame_id, "area_pixels": round(part.area, 1),
                                "target_overlap_pixels": round(overlap, 1),
                                "water_fraction_before": round(coverage, 4), "geometry": part})
    if not missing:
        return source, {"changed": False, "missing_lakes": 0}

    by_frame = {}
    for item in missing:
        by_frame.setdefault(item["frame"], []).append(item)
    frame_map = {fid: (bounds, rect) for fid, bounds, rect in frame_list}
    clips, groups = [], []
    for frame_id, items in by_frame.items():
        paths = "".join(f'<path data-map-auto-lake="1" d="{_path(i["geometry"])}"/>' for i in items)
        _bounds, rect = frame_map[frame_id]
        if rect is None:
            groups.append(paths)
        else:
            x, y, w, h = rect
            clip_id = "lake-clip-" + re.sub(r"[^A-Za-z0-9_-]", "-", frame_id)
            clips.append(f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/></clipPath>')
            groups.append(f'<g clip-path="url(#{clip_id})">{paths}</g>')
    result = source
    if clips:
        if result.count("</defs>") != 1:
            raise ValueError("Expected one defs block for region lake clips")
        result = result.replace("</defs>", "".join(clips) + "</defs>", 1)
    markup = (f'<g id="inland-water-auto" fill="{WATER_FILL}" stroke="{WATER_STROKE}" '
              'stroke-opacity=".35" stroke-width=".65" fill-rule="evenodd" '
              'stroke-linejoin="round" stroke-linecap="round">' + "".join(groups) + "</g>")
    result = _insert(result, markup)
    return result, {"changed": True, "missing_lakes": len(missing), "items": [
        {k: v for k, v in item.items() if k != "geometry"} for item in missing]}


def main():
    args = parse_args()
    config = json.loads(args.country_json.read_text(encoding="utf-8"))
    source = args.input.read_text(encoding="utf-8")
    result, report = normalize(source, config, args.resolution)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slug": config.get("slug"), **report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
