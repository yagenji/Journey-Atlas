#!/usr/bin/env python3
"""Normalize material inland-water rendering across canonical Country maps.

Approved country/coast/border path geometry is never rewritten. GSHHS/GSHHG
level-2 inland water is projected onto the existing 1200x760 map frame. A
reviewed canonical inland-water layer is preserved rather than regenerated.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import add_country_map_context as ctx

SVG_NS = "{http://www.w3.org/2000/svg}"
SUPPORTED_PROJECTIONS = {
    "local-equirectangular-fit-v1",
    "multi-region-local-equirectangular-fit-v1",
}
LAKE_FILL = "#e5eceb"
LAKE_STROKE = "#6f8a92"
LAKE_STROKE_OPACITY = ".35"
LAKE_STROKE_WIDTH = ".65"
MIN_PIXEL_AREA = 64
MIN_PIXEL_WIDTH = 5
MIN_PIXEL_HEIGHT = 5
SIMPLIFY = 0.00195
WATER_SOURCE_NOTE = "Inland water: GSHHS/GSHHG via Basemap resolution=i, WGS84."

WATER_GROUP_RE = re.compile(
    r'<g\b(?=[^>]*\bid="inland-water"|[^>]*\bfill="#e5eceb"|[^>]*\bfill="#e4eceb")'
    r'[^>]*>.*?</g>\s*',
    re.DOTALL,
)
METADATA_RE = re.compile(r"<metadata>(.*?)</metadata>", re.DOTALL)
DEFS_CLOSE_RE = re.compile(r"</defs\s*>")


def bounds_tuple(bounds: dict) -> tuple[float, float, float, float]:
    return tuple(float(bounds[key]) for key in ("west", "south", "east", "north"))


def rect_tuple(rect: dict) -> tuple[float, float, float, float]:
    return tuple(float(rect[key]) for key in ("x", "y", "width", "height"))


def visible_at_product_scale(poly: Polygon, bounds, rect=None) -> bool:
    factor, scale, _, _ = ctx.frame(bounds, rect)
    minx, miny, maxx, maxy = poly.bounds
    width = (maxx - minx) * factor * scale
    height = (maxy - miny) * scale
    area = poly.area * factor * scale * scale
    return area >= MIN_PIXEL_AREA and width >= MIN_PIXEL_WIDTH and height >= MIN_PIXEL_HEIGHT


def material_lakes(bounds: tuple[float, float, float, float], rect=None):
    """Return GSHHS level-2 water that remains material at product scale."""
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 360 and -89 <= south < north <= 89):
        raise ValueError("unsupported bounds for canonical inland-water normalization")
    basemap = Basemap(
        projection="cyl",
        llcrnrlon=west,
        llcrnrlat=south,
        urcrnrlon=east,
        urcrnrlat=north,
        resolution="i",
        area_thresh=0.1,
    )
    extent = box(*bounds)
    lakes = []
    for (xs, ys), level in zip(basemap.coastpolygons, basemap.coastpolygontypes):
        if level != 2:
            continue
        poly = Polygon(zip(xs, ys))
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        clipped = poly.intersection(extent)
        for component in ctx.mapgen.polygons_from_geometry(clipped):
            if not component.is_empty and visible_at_product_scale(component, bounds, rect):
                lakes.append(component)
    return lakes


def canonical_water_present(root: ET.Element, source: str) -> bool:
    """Keep already-reviewed shared-style lake geometry byte-for-byte."""
    for group in root.iter(SVG_NS + "g"):
        if group.get("id") != "inland-water":
            continue
        if (
            group.get("fill") == LAKE_FILL
            and group.get("stroke") == LAKE_STROKE
            and group.get("stroke-width") == LAKE_STROKE_WIDTH
            and group.get("stroke-opacity") == LAKE_STROKE_OPACITY
            and "GSHHS/GSHHG" in source
        ):
            return True
    return False


def projected_path(bounds, rect=None) -> tuple[str, int]:
    lakes = material_lakes(bounds, rect)
    if not lakes:
        return "", 0
    geometry = unary_union(lakes)
    return ctx.make_context_path(geometry, bounds, SIMPLIFY, rect), len(lakes)


def lake_markup(config: dict, projection: str) -> tuple[str, str, int]:
    """Return (defs, water_group, polygon_count)."""
    regions = (config.get("map") or {}).get("regions") or []
    clips: list[str] = []
    paths: list[str] = []
    count = 0

    if projection == "multi-region-local-equirectangular-fit-v1":
        if not regions:
            return "", "", 0
        for region in regions:
            bounds = bounds_tuple(region["bounds"])
            rect = rect_tuple(region["rect"])
            d, n = projected_path(bounds, rect)
            if not d:
                continue
            identifier = region["id"]
            x, y, width, height = rect
            clip_id = f"inland-water-clip-{identifier}"
            clips.append(
                f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">'
                f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"/></clipPath>'
            )
            paths.append(
                f'<path data-map-region="{identifier}" clip-path="url(#{clip_id})" d="{d}"/>'
            )
            count += n
    elif projection == "local-equirectangular-fit-v1":
        # The national overview remains the primary frame even when JSON also
        # declares one or more detail insets (Benin/Qatar pattern).
        main_bounds = bounds_tuple(config["map"]["bounds"])
        d, n = projected_path(main_bounds)
        if d:
            paths.append(f'<path data-map-frame="main" d="{d}"/>')
            count += n
        for region in regions:
            bounds = bounds_tuple(region["bounds"])
            rect = rect_tuple(region["rect"])
            d, n = projected_path(bounds, rect)
            if not d:
                continue
            identifier = region["id"]
            x, y, width, height = rect
            clip_id = f"inland-water-clip-{identifier}"
            clips.append(
                f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">'
                f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}"/></clipPath>'
            )
            paths.append(
                f'<path data-map-region="{identifier}" clip-path="url(#{clip_id})" d="{d}"/>'
            )
            count += n
    else:
        return "", "", 0

    if not paths:
        return "", "", 0
    group = (
        f'<g id="inland-water" fill="{LAKE_FILL}" stroke="{LAKE_STROKE}" '
        f'stroke-opacity="{LAKE_STROKE_OPACITY}" stroke-width="{LAKE_STROKE_WIDTH}" '
        f'fill-rule="evenodd">' + "".join(paths) + "</g>"
    )
    return "".join(clips), group, count


def add_source_note(svg: str) -> str:
    match = METADATA_RE.search(svg)
    if not match or "GSHHS/GSHHG" in match.group(1):
        return svg
    replacement = f"<metadata>{match.group(1).rstrip()} {WATER_SOURCE_NOTE}</metadata>"
    return svg[: match.start()] + replacement + svg[match.end() :]


def insert_water(source: str, defs: str, group: str) -> str:
    stripped = WATER_GROUP_RE.sub("", source)
    if defs:
        close = DEFS_CLOSE_RE.search(stripped)
        if not close:
            raise ValueError("SVG defs closing tag missing")
        stripped = stripped[: close.start()] + defs + stripped[close.start() :]
    if "</svg>" not in stripped:
        raise ValueError("SVG closing tag missing")

    # Prefer to place water before reviewed border overlays so international
    # and disputed lake boundaries remain visible above the water fill.
    anchors = (
        r'<path\b[^>]*\bid="target-country-boundary-overlay"',
        r'<g\b[^>]*\bid="country-boundaries"',
        r'<g\b[^>]*\bid="context-national-borders"',
        r'<path\b[^>]*\bid="neighbor-borders"',
    )
    positions = []
    for pattern in anchors:
        match = re.search(pattern, stripped)
        if match:
            positions.append(match.start())
    if positions:
        pos = min(positions)
        return stripped[:pos] + group + "\n" + stripped[pos:]
    return stripped.replace("</svg>", group + "\n</svg>", 1)


def normalize_svg(source: str, config: dict) -> tuple[str, str, int]:
    root = ET.fromstring(source)
    if root.tag != SVG_NS + "svg" or root.get("viewBox") != "0 0 1200 760":
        return source, "unsupported_canvas", 0
    projection = root.get("data-map-projection") or ""
    if projection not in SUPPORTED_PROJECTIONS:
        return source, "unsupported_projection", 0
    if canonical_water_present(root, source):
        return source, "unchanged", 0
    defs, group, count = lake_markup(config, projection)
    if not group:
        return source, "no_material_lakes", 0
    normalized = insert_water(source, defs, group)
    normalized = add_source_note(normalized)
    # Parse the finished SVG before allowing it to leave the normalizer.
    ET.fromstring(normalized)
    return normalized, ("unchanged" if normalized == source else "changed"), count


def normalize_country_source(config: dict) -> dict:
    source = (config.get("map") or {}).get("source")
    if not isinstance(source, str) or "GSHHS/GSHHG" in source:
        return config
    config = json.loads(json.dumps(config, ensure_ascii=False))
    config["map"]["source"] = source.rstrip() + " " + WATER_SOURCE_NOTE
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--scope", choices=("published", "all"), default="all")
    parser.add_argument("--check", action="store_true", help="Fail when a supported map still needs normalization")
    args = parser.parse_args()
    if not 0 <= args.shard < args.shards:
        parser.error("invalid shard")

    registry = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
    destinations = registry["destinations"]
    if args.scope == "published":
        destinations = [item for item in destinations if item.get("atlasPublished")]
    selected = [item for index, item in enumerate(destinations) if index % args.shards == args.shard]

    report = {
        "scope": args.scope,
        "shard": args.shard,
        "shards": args.shards,
        "selected_count": len(selected),
        "changed": [],
        "unchanged": [],
        "no_material_lakes": [],
        "unsupported": [],
        "errors": [],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for item in selected:
        slug = item["slug"]
        try:
            country_path = ROOT / "data" / "countries" / f"{slug}.json"
            if not country_path.exists():
                continue
            config = json.loads(country_path.read_text(encoding="utf-8"))
            relative = (config.get("map") or {}).get("svg")
            if not isinstance(relative, str) or not relative.endswith(".svg"):
                continue
            svg_path = ROOT / relative
            source = svg_path.read_text(encoding="utf-8")
            normalized, status, lake_count = normalize_svg(source, config)
            if status == "changed":
                out_svg = args.output_dir / relative
                out_svg.parent.mkdir(parents=True, exist_ok=True)
                out_svg.write_text(normalized, encoding="utf-8")
                updated_config = normalize_country_source(config)
                if updated_config != config:
                    out_json = args.output_dir / "data" / "countries" / f"{slug}.json"
                    out_json.parent.mkdir(parents=True, exist_ok=True)
                    out_json.write_text(json.dumps(updated_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                report["changed"].append({"slug": slug, "svg": relative, "lake_polygons": lake_count})
            elif status == "unchanged":
                report["unchanged"].append(slug)
            elif status == "no_material_lakes":
                report["no_material_lakes"].append(slug)
            else:
                report["unsupported"].append({"slug": slug, "reason": status, "svg": relative})
        except Exception as exc:
            report["errors"].append({"slug": slug, "error": f"{type(exc).__name__}: {exc}"})

    (args.output_dir / "lake-normalization-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "LAKE NORMALIZATION",
        json.dumps(
            {
                "selected": len(selected),
                "changed": len(report["changed"]),
                "unchanged": len(report["unchanged"]),
                "no_material_lakes": len(report["no_material_lakes"]),
                "unsupported": len(report["unsupported"]),
                "errors": len(report["errors"]),
            },
            ensure_ascii=False,
        ),
    )
    for row in report["unsupported"]:
        print("UNSUPPORTED", row["slug"], row["reason"], row["svg"])
    for row in report["errors"]:
        print("ERROR", row["slug"], row["error"])
    if report["errors"] or (args.check and report["changed"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
