#!/usr/bin/env python3
"""Add missing material inland-water geometry to an existing JOURNEY ATLAS map.

The tool is deliberately conservative:
- uses verified GSHHS/GSHHG level-2 inland-water geometry;
- only considers lakes that visibly intersect the target Country geometry;
- limits automatic fixes to major water bodies that are clearly legible at 1200x760;
- raster-checks the existing SVG and leaves already-rendered water alone;
- never changes coastline, islands, administrative boundaries or marker coordinates;
- never modifies maps that already contain a reviewed ``inland-water`` layer.

It is shared map tooling, not Country-specific production state.
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

SVG_NS = "{http://www.w3.org/2000/svg}"
WIDTH = 1200
HEIGHT = 760
# Major-lake gate. Smaller water bodies remain a visual-review choice rather
# than being forced into every map. This keeps the shared rule geographic and
# legible instead of turning the map into a hydrography layer.
MIN_LAKE_PIXELS = 1000.0
MIN_LAKE_WIDTH = 10.0
MIN_LAKE_HEIGHT = 10.0
# Borders, shoreline antialiasing and reviewed water strokes can occupy part of
# a true lake polygon. Seventy percent visible water is enough to treat it as
# already represented and avoids double-drawing reviewed lakes.
WATER_PASS = 0.70
WATER_FILL = "#e5eceb"
WATER_STROKE = "#6f8a92"
FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
RING_RE = re.compile(r"[Mm]\s*([^Mm]*?)[Zz]", re.S)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resolution", default="i", choices=("c", "l", "i", "h", "f"))
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def _numbers(token: str) -> tuple[float, float]:
    values = [float(value) for value in FLOAT_RE.findall(token)]
    if len(values) != 2:
        raise ValueError("Only linear M/L/Z path coordinates are supported")
    return values[0], values[1]


def _rings_from_d(d: str) -> list[Polygon]:
    remainder = RING_RE.sub("", d)
    if remainder.strip():
        raise ValueError("Only linear M/L/Z target geometry is supported")
    rings: list[Polygon] = []
    for match in RING_RE.finditer(d):
        parts = re.split(r"[Ll]", match.group(1))
        points = [_numbers(part) for part in parts if part.strip()]
        if len(points) < 3:
            continue
        poly = Polygon(points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty and poly.area > 0:
            rings.extend(ctx.mapgen.polygons_from_geometry(poly))
    return rings


def _effective_fill(node, parents) -> str | None:
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
        if _effective_fill(node, parents) != "url(#land)":
            continue
        d = node.get("d", "")
        if d:
            targets.extend(_rings_from_d(d))
    if not targets:
        raise ValueError("No linear target-country land geometry found")
    return unary_union(targets)


def _frames(config: dict):
    regions = (config.get("map") or {}).get("regions")
    if regions:
        result = []
        for region in regions:
            b = region["bounds"]
            r = region["rect"]
            result.append((
                region["id"],
                tuple(float(b[key]) for key in ("west", "south", "east", "north")),
                tuple(float(r[key]) for key in ("x", "y", "width", "height")),
            ))
        return result
    b = config["map"]["bounds"]
    return [("main", tuple(float(b[key]) for key in ("west", "south", "east", "north")), None)]


def _gshhs_lakes(bounds, resolution: str):
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 180 and -89 <= south < north <= 89):
        raise ValueError("Unsupported map bounds for shared lake normalization")
    basemap = Basemap(
        projection="cyl",
        llcrnrlon=west,
        llcrnrlat=south,
        urcrnrlon=east,
        urcrnrlat=north,
        resolution=resolution,
        area_thresh=0.1,
    )
    lakes = []
    for (xs, ys), level in zip(basemap.coastpolygons, basemap.coastpolygontypes):
        if level != 2:
            continue
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            lakes.extend(ctx.mapgen.polygons_from_geometry(poly))
    return lakes


def _project_polygon(poly: Polygon, bounds, rect):
    factor, scale, origin_x, origin_y = ctx.frame(bounds, rect)
    west, south, east, north = bounds

    def ring(coords):
        return [
            (origin_x + (lon - west) * factor * scale,
             origin_y + (north - lat) * scale)
            for lon, lat in coords
        ]

    projected = Polygon(ring(poly.exterior.coords), [ring(interior.coords) for interior in poly.interiors])
    if not projected.is_valid:
        projected = projected.buffer(0)
    return projected


def _path_from_polygon(poly: Polygon) -> str:
    def ring(coords):
        pts = []
        for x, y in coords:
            point = (round(float(x), 1), round(float(y), 1))
            if not pts or point != pts[-1]:
                pts.append(point)
        if len(pts) < 3:
            return ""
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

    parts = [ring(poly.exterior.coords)]
    parts.extend(ring(interior.coords) for interior in poly.interiors)
    return " ".join(part for part in parts if part)


def _mask(poly):
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    exterior = [(round(x), round(y)) for x, y in poly.exterior.coords]
    if len(exterior) >= 3:
        draw.polygon(exterior, fill=255)
    for interior in poly.interiors:
        points = [(round(x), round(y)) for x, y in interior.coords]
        if len(points) >= 3:
            draw.polygon(points, fill=0)
    return mask


def _is_water(rgb) -> bool:
    r, g, b = rgb[:3]
    # Shared sea gradient and approved inland-water fills are pale cool tones;
    # the warm target/context land palette fails this gate.
    return b >= 212 and g >= 218 and g - r >= 2 and b - r >= 3


def _coverage(image: Image.Image, poly) -> float:
    mask = _mask(poly)
    bbox = mask.getbbox()
    if bbox is None:
        return 0.0
    px = image.load()
    mp = mask.load()
    water = total = 0
    for y in range(max(0, bbox[1]), min(HEIGHT, bbox[3])):
        for x in range(max(0, bbox[0]), min(WIDTH, bbox[2])):
            if not mp[x, y]:
                continue
            total += 1
            if _is_water(px[x, y]):
                water += 1
    return water / total if total else 0.0


def _material(poly) -> bool:
    minx, miny, maxx, maxy = poly.bounds
    return (
        poly.area >= MIN_LAKE_PIXELS
        and maxx - minx >= MIN_LAKE_WIDTH
        and maxy - miny >= MIN_LAKE_HEIGHT
        and maxx > 0 and maxy > 0 and minx < WIDTH and miny < HEIGHT
    )


def _clip_to_canvas(poly):
    clipped = poly.intersection(box(0, 0, WIDTH, HEIGHT))
    return [p for p in ctx.mapgen.polygons_from_geometry(clipped) if not p.is_empty and p.area > 0]


def _insert_markup(source: str, markup: str) -> str:
    # Put water above land but below reviewed national/border overlays whenever present.
    anchors = (
        '<path id="target-country-boundary-overlay"',
        '<path id="neighbor-borders"',
        '<g id="country-boundaries"',
        '<g id="boundary',
    )
    positions = [source.find(anchor) for anchor in anchors if source.find(anchor) >= 0]
    if positions:
        pos = min(positions)
        return source[:pos] + markup + "\n" + source[pos:]
    close = source.rfind("</svg>")
    if close < 0:
        raise ValueError("SVG closing tag missing")
    return source[:close] + markup + "\n" + source[close:]


def normalize(source: str, config: dict, resolution: str) -> tuple[str, dict]:
    root = ET.fromstring(source)
    if root.tag != SVG_NS + "svg" or root.get("viewBox") != "0 0 1200 760":
        raise ValueError("Expected canonical 1200x760 SVG")
    if root.get("data-map-projection") not in (
        "local-equirectangular-fit-v1",
        "multi-region-local-equirectangular-fit-v1",
    ):
        raise ValueError("Unsupported projection for shared lake normalization")

    # Explicit inland-water geometry means the map has already had Country-level
    # geographic review. Never stack an automatic layer on top of it.
    if root.find(".//*[@id='inland-water']") is not None:
        return source, {"changed": False, "missing_lakes": 0, "reason": "reviewed_inland_water"}
    if root.find(".//*[@id='inland-water-auto']") is not None:
        return source, {"changed": False, "missing_lakes": 0, "reason": "already_normalized"}

    target = _target_geometry(root)
    raster = cairosvg.svg2png(bytestring=source.encode("utf-8"), output_width=WIDTH, output_height=HEIGHT)
    image = Image.open(io.BytesIO(raster)).convert("RGB")

    missing = []
    seen = set()
    for frame_id, bounds, rect in _frames(config):
        visible = ctx.canvas_bounds(bounds, rect)
        for lake in _gshhs_lakes(visible, resolution):
            projected = _project_polygon(lake, bounds, rect)
            for part in _clip_to_canvas(projected):
                if not _material(part):
                    continue
                overlap = part.intersection(target).area
                # Require a meaningful overlap with target-country land; nearby
                # lakes belonging only to surrounding countries are not patched.
                if overlap < max(40.0, part.area * 0.08):
                    continue
                rep = part.representative_point()
                key = (frame_id, round(rep.x, 1), round(rep.y, 1), round(part.area, 1))
                if key in seen:
                    continue
                seen.add(key)
                water_fraction = _coverage(image, part)
                if water_fraction >= WATER_PASS:
                    continue
                missing.append({
                    "frame": frame_id,
                    "area_pixels": round(part.area, 1),
                    "target_overlap_pixels": round(overlap, 1),
                    "water_fraction_before": round(water_fraction, 4),
                    "geometry": part,
                })

    if not missing:
        return source, {"changed": False, "missing_lakes": 0}

    by_frame: dict[str, list] = {}
    for item in missing:
        by_frame.setdefault(item["frame"], []).append(item)

    clips = []
    groups = []
    frame_map = {frame_id: (bounds, rect) for frame_id, bounds, rect in _frames(config)}
    for frame_id, items in by_frame.items():
        paths = "".join(
            f'<path data-map-auto-lake="1" d="{_path_from_polygon(item["geometry"])}"/>'
            for item in items
        )
        _bounds, rect = frame_map[frame_id]
        if rect is None:
            groups.append(paths)
        else:
            x, y, width, height = rect
            clip_id = f"lake-clip-{re.sub(r'[^A-Za-z0-9_-]', '-', frame_id)}"
            clips.append(
                f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">'
                f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"/>'
                '</clipPath>'
            )
            groups.append(f'<g clip-path="url(#{clip_id})">{paths}</g>')

    result = source
    if clips:
        if result.count("</defs>") != 1:
            raise ValueError("Expected one defs block for region lake clips")
        result = result.replace("</defs>", "".join(clips) + "</defs>", 1)
    markup = (
        f'<g id="inland-water-auto" fill="{WATER_FILL}" stroke="{WATER_STROKE}" '
        'stroke-opacity=".35" stroke-width=".65" fill-rule="evenodd" '
        'stroke-linejoin="round" stroke-linecap="round">'
        + "".join(groups)
        + "</g>"
    )
    result = _insert_markup(result, markup)
    return result, {
        "changed": True,
        "missing_lakes": len(missing),
        "items": [
            {key: value for key, value in item.items() if key != "geometry"}
            for item in missing
        ],
    }


def main() -> None:
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
