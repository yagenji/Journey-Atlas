#!/usr/bin/env python3
"""Merge per-country context polygons into one land silhouette.

Some Country maps draw surrounding land as one outlined polygon per country.
Since national borders are drawn separately by `#context-national-borders`
(Natural Earth boundary lines, `add_country_border_context.py`), each shared
foreign border then appears twice — the two polygon edges plus the border line —
and reads as a heavier line than on other maps. This unions every path in
`#geographic-context` into a single path, so the context outline follows only
the coast and the borders come from the shared border layer.

This also applies when one path holds several countries' rings. Rings inside
one path are combined even-odd (holes stay holes); paths are then unioned. Geometry is unchanged except for the removed internal edges.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

RING = re.compile(r"M\s*([^MZ]*?)\s*Z")
PATH = re.compile(r'<path([^>]*?)\sd="([^"]*)"([^>]*?)\s*(?:/>|>(?:\s*<title>[^<]*</title>)?\s*</path>)')


def path_geometry(d: str):
    geom = Polygon()
    if re.search(r"[A-KN-Ya-kn-y]", d):
        raise ValueError("Only absolute M/L/Z context paths can be dissolved")
    for chunk in RING.finditer(d):
        # absolute M/L/Z; "L" may be omitted between coordinate pairs
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", chunk.group(1))]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) >= 3:
            poly = Polygon(pts)
            geom = geom.symmetric_difference(poly if poly.is_valid else poly.buffer(0))
    return geom


def to_d(geom) -> str:
    out = []
    for poly in getattr(geom, "geoms", [geom]):
        if poly.geom_type != "Polygon" or poly.is_empty:
            continue
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)[:-1]
            if len(coords) >= 3:
                out.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in coords) + " Z")
    return " ".join(out)


def dissolve(svg: str, context_id: str = "geographic-context") -> tuple[str, int]:
    m = re.search(r'(<g id="%s"[^>]*>)(.*?)(</g>)' % re.escape(context_id), svg, re.S)
    if not m:
        raise ValueError(f"No #{context_id} group")
    inner = m.group(2)
    paths = list(PATH.finditer(inner))
    if not paths:
        return svg, 0
    between = PATH.sub("", inner[paths[0].start():paths[-1].end()]).strip()
    if between:
        raise ValueError(f"Unexpected non-path content between context paths: {between[:80]}")
    geom = unary_union([path_geometry(p.group(2)) for p in paths]).buffer(0)
    attrs = re.sub(r'\sdata-(?:context-)?country="[^"]*"', "", paths[0].group(1) + paths[0].group(3))
    if "fill-rule" not in attrs and "fill-rule" not in m.group(1):
        attrs += ' fill-rule="evenodd"'
    new_inner = inner[:paths[0].start()] + f'<path{attrs} d="{to_d(geom)}"/>' + inner[paths[-1].end():]
    return svg.replace(m.group(0), m.group(1) + new_inner + m.group(3), 1), len(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    svg, merged = dissolve(args.input.read_text(encoding="utf-8"))
    args.output.write_text(svg, encoding="utf-8")
    print(f"{args.output}: merged {merged} context paths")


if __name__ == "__main__":
    main()
