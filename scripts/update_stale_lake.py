#!/usr/bin/env python3
"""Replace a stale historic lake outline with its current Natural Earth extent.

GSHHS (used by the shared lake normalizer) still carries some lakes at their
historic extent. The clearest case is the Aral Sea, drawn at its pre-1960s
shoreline although most of it has dried out. This replaces, inside one map's
`#inland-water-auto` group, every auto-lake ring that lies mostly within the
historic footprint (Natural Earth `ne_10m_lakes_historic`) with the current
water bodies inside that footprint (Natural Earth `ne_10m_lakes`), projected
with the same local-equirectangular fit. The target land already includes the dried seabed; a
context-land patch fills any hole the surrounding GSHHS land has there.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

RING = re.compile(r"M\s*([^MZ]*?)\s*Z")


def projector(bounds: dict):
    lon_scale = math.cos(math.radians((bounds["south"] + bounds["north"]) / 2))
    pw = (bounds["east"] - bounds["west"]) * lon_scale
    ph = bounds["north"] - bounds["south"]
    scale = min(1200 / pw, 760 / ph)
    ox, oy = (1200 - pw * scale) / 2, (760 - ph * scale) / 2
    return lambda lon, lat: (ox + (lon - bounds["west"]) * lon_scale * scale, oy + (bounds["north"] - lat) * scale)


def ring_polygons(d: str):
    for chunk in RING.finditer(d):
        pts = []
        for xy in re.split(r"\s*L\s*", chunk.group(1).strip()):
            if xy.strip():
                x, y = xy.replace(" ", ",").split(",")[:2]
                pts.append((float(x), float(y)))
        if len(pts) >= 3:
            poly = Polygon(pts)
            yield chunk.group(0), (poly if poly.is_valid else poly.buffer(0))


def polygons(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [g for g in getattr(geometry, "geoms", []) if g.geom_type == "Polygon"]


def to_path(geometry, project) -> str:
    parts = []
    for poly in polygons(geometry):
        for ring in [poly.exterior, *poly.interiors]:
            pts = []
            for lon, lat in ring.coords[:-1]:
                x, y = project(lon, lat)
                p = (round(x, 1), round(y, 1))
                if not pts or pts[-1] != p:
                    pts.append(p)
            if len(pts) >= 3:
                parts.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z")
    return " ".join(parts)


def update(svg: str, bounds: dict, historic, current_lakes) -> tuple[str, int, int]:
    project = projector(bounds)
    footprint_px = unary_union([Polygon([project(x, y) for x, y in p.exterior.coords]) for p in polygons(historic)])
    group = re.search(r'(<g id="inland-water-auto"[^>]*>)(.*?)(</g>)', svg, re.S)
    if not group:
        raise ValueError("No #inland-water-auto group")
    removed = 0
    inner = group.group(2)
    for pm in list(re.finditer(r'<path([^>]*?)\sd="([^"]*)"([^>]*)/>', inner)):
        kept = []
        for text, poly in ring_polygons(pm.group(2)):
            if poly.area > 0 and poly.intersection(footprint_px).area / poly.area >= 0.5:
                removed += 1
            else:
                kept.append(text)
        inner = inner.replace(pm.group(0), f'<path{pm.group(1)} d="{" ".join(kept)}"{pm.group(3)}/>' if kept else "", 1)
    view = box(bounds["west"], bounds["south"], bounds["east"], bounds["north"])
    added = [lake.intersection(view) for lake in current_lakes if lake.intersects(historic) and lake.intersects(view)]
    if added:
        inner += f'<path data-map-current-water="natural-earth-10m-lakes" d="{to_path(unary_union(added), project)}"/>'
    svg = svg.replace(group.group(0), group.group(1) + inner + group.group(3), 1)
    # Surrounding GSHHS land may have a hole at the historic shoreline; the dried
    # bed is land, so fill the footprint with context land (no outline) below the
    # target, borders and current water.
    context = re.search(r'(<g id="geographic-context"[^>]*>)', svg)
    if context:
        bed = f'<path data-map-dried-lakebed="1" d="{to_path(historic.intersection(view), project)}" fill="#e4e0ce" fill-rule="evenodd" stroke="none"/>'
        svg = svg.replace(context.group(1), context.group(1) + bed, 1)
    return svg, removed, len(added)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lakes", required=True, type=Path, help="Natural Earth ne_10m_lakes.geojson (pinned)")
    parser.add_argument("--historic", required=True, type=Path, help="Natural Earth ne_10m_lakes_historic.geojson (pinned)")
    parser.add_argument("--name", required=True, help="Historic lake name, e.g. 'Aral Sea'")
    args = parser.parse_args()
    bounds = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]["bounds"]
    historic = unary_union([shape(f["geometry"]) for f in json.loads(args.historic.read_text(encoding="utf-8"))["features"]
                            if f["properties"].get("name") == args.name])
    if historic.is_empty:
        raise SystemExit(f"Historic lake not found: {args.name}")
    lakes = [shape(f["geometry"]) for f in json.loads(args.lakes.read_text(encoding="utf-8"))["features"]]
    svg, removed, added = update(args.input.read_text(encoding="utf-8"), bounds, historic, lakes)
    args.output.write_text(svg, encoding="utf-8")
    print(f"{args.output}: removed {removed} historic-extent rings, added {added} current water bodies")


if __name__ == "__main__":
    main()
