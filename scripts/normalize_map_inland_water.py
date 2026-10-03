#!/usr/bin/env python3
"""Normalize visible inland-water layers across Country map SVGs.

The script never alters approved country/coast/border path geometry. It derives
material inland-water polygons from GSHHS/GSHHG and adds a canonical water
layer above land. Existing canonical/generated water groups are replaced.
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
MIN_GEODEG_AREA = 0.003
SIMPLIFY = 0.00195
WATER_SOURCE_NOTE = "Inland water: GSHHS/GSHHG via Basemap resolution=i, WGS84."

CANONICAL_WATER_RE = re.compile(
    r'<g\b(?=[^>]*\bid="inland-water"|[^>]*\bfill="#e5eceb")'
    r'[^>]*>.*?</g>\s*',
    re.DOTALL,
)
METADATA_RE = re.compile(r"<metadata>(.*?)</metadata>", re.DOTALL)


def bounds_tuple(bounds: dict) -> tuple[float, float, float, float]:
    return tuple(float(bounds[key]) for key in ("west", "south", "east", "north"))


def rect_tuple(rect: dict) -> tuple[float, float, float, float]:
    return tuple(float(rect[key]) for key in ("x", "y", "width", "height"))


def material_lakes(bounds: tuple[float, float, float, float]):
    """Return material GSHHS level-2 lake polygons clipped to the map bounds."""
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    if not (-360 <= west < east <= 360 and east - west <= 180 and -89 <= south < north <= 89):
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
        if poly.is_empty or poly.area <= MIN_GEODEG_AREA:
            continue
        clipped = poly.intersection(extent)
        if not clipped.is_empty:
            lakes.extend(ctx.mapgen.polygons_from_geometry(clipped))
    return lakes


def lake_markup(config: dict, projection: str) -> tuple[str, int]:
    regions = (config.get("map") or {}).get("regions")
    paths: list[str] = []
    count = 0
    if regions:
        if projection != "multi-region-local-equirectangular-fit-v1":
            raise ValueError("map.regions requires the reviewed multi-region projection")
        for region in regions:
            bounds = bounds_tuple(region["bounds"])
            rect = rect_tuple(region["rect"])
            lakes = material_lakes(bounds)
            if not lakes:
                continue
            geometry = unary_union(lakes)
            d = ctx.make_context_path(geometry, bounds, SIMPLIFY, rect)
            if d:
                paths.append(f'<path data-map-region="{region["id"]}" d="{d}"/>')
                count += len(lakes)
    else:
        if projection != "local-equirectangular-fit-v1":
            raise ValueError("unsupported single-region projection")
        bounds = bounds_tuple(config["map"]["bounds"])
        lakes = material_lakes(bounds)
        if lakes:
            geometry = unary_union(lakes)
            d = ctx.make_context_path(geometry, bounds, SIMPLIFY)
            if d:
                paths.append(f'<path d="{d}"/>')
                count += len(lakes)
    if not paths:
        return "", 0
    group = (
        f'<g id="inland-water" fill="{LAKE_FILL}" stroke="{LAKE_STROKE}" '
        f'stroke-opacity="{LAKE_STROKE_OPACITY}" stroke-width="{LAKE_STROKE_WIDTH}" '
        f'fill-rule="evenodd">' + "".join(paths) + "</g>"
    )
    return group, count


def add_source_note(svg: str) -> str:
    match = METADATA_RE.search(svg)
    if not match or "GSHHS/GSHHG" in match.group(1):
        return svg
    replacement = f"<metadata>{match.group(1).rstrip()} {WATER_SOURCE_NOTE}</metadata>"
    return svg[: match.start()] + replacement + svg[match.end() :]


def normalize_svg(source: str, config: dict) -> tuple[str, str, int]:
    root = ET.fromstring(source)
    if root.tag != SVG_NS + "svg" or root.get("viewBox") != "0 0 1200 760":
        return source, "unsupported_canvas", 0
    projection = root.get("data-map-projection") or ""
    if projection not in SUPPORTED_PROJECTIONS:
        return source, "unsupported_projection", 0
    group, count = lake_markup(config, projection)
    if not group:
        return source, "no_material_lakes", 0
    stripped = CANONICAL_WATER_RE.sub("", source)
    if "</svg>" not in stripped:
        raise ValueError("SVG closing tag missing")
    normalized = stripped.replace("</svg>", group + "\n</svg>", 1)
    normalized = add_source_note(normalized)
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
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
