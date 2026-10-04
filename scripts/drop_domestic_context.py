#!/usr/bin/env python3
"""Remove domestic duplicates from a Country map's geographic context.

The target country is drawn from one dataset and the pale context land from
GSHHS. Where the target's own coast or islets also appear in the context,
the two outlines are offset by a pixel or two and read as a second silhouette.
Context rings that lie on the target (at least 90% of their area within
`--tolerance` px of target land) are domestic duplicates and are removed;
foreign land is untouched. If nothing remains, the empty context path element
is removed and the `#geographic-context` group stays as an empty marker.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

RING = re.compile(r"M\s*([^MZ]*?)\s*Z")


def _rings(d: str):
    for chunk in RING.finditer(d):
        pts = []
        for xy in re.split(r"\s*L\s*", chunk.group(1).strip()):
            if xy.strip():
                x, y = xy.replace(" ", ",").split(",")[:2]
                pts.append((float(x), float(y)))
        poly = Polygon(pts) if len(pts) >= 3 else None
        if poly is not None and not poly.is_valid:
            poly = poly.buffer(0)
        yield chunk.group(0), poly


def target_geometry(group_xml: str):
    parts = []
    for d in re.findall(r'<path[^>]*?\sd="([^"]*)"[^>]*fill="url\(#land\)"|<path[^>]*fill="url\(#land\)"[^>]*?\sd="([^"]*)"', group_xml):
        for _, poly in _rings(d[0] or d[1]):
            if poly is not None and not poly.is_empty:
                parts.append(poly)
    for g in re.findall(r'<g[^>]*fill="url\(#land\)"[^>]*>(.*?)</g>', group_xml, re.S):
        for d in re.findall(r'\sd="([^"]*)"', g):
            for _, poly in _rings(d):
                if poly is not None and not poly.is_empty:
                    parts.append(poly)
    return unary_union(parts)


def clean(svg: str, tolerance: float = 3.0, context_id: str = "geographic-context") -> tuple[str, int]:
    target = target_geometry(svg)
    if target.is_empty:
        raise ValueError("Target land not found")
    zone = target.buffer(tolerance)
    m = re.search(r'(<g id="%s"[^>]*>)(.*?)(</g>)' % re.escape(context_id), svg, re.S)
    if not m:
        return svg, 0
    inner = m.group(2)
    removed = 0
    for pm in list(re.finditer(r'<path([^>]*?)\sd="([^"]*)"([^>]*)/>', inner)):
        kept = []
        for text, poly in _rings(pm.group(2)):
            # A ring is domestic when it lies (almost) entirely on the target. Large
            # continental rings that merely touch the target are foreign land.
            if poly is not None and not poly.is_empty and poly.area > 0 and \
                    poly.intersection(zone).area / poly.area >= 0.9:
                removed += 1
            else:
                kept.append(text)
        replacement = f'<path{pm.group(1)} d="{" ".join(kept)}"{pm.group(3)}/>' if kept else ""
        inner = inner.replace(pm.group(0), replacement, 1)
    return svg.replace(m.group(0), m.group(1) + inner + m.group(3), 1), removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, nargs="+")
    parser.add_argument("--tolerance", type=float, default=3.0)
    args = parser.parse_args()
    for path in args.svg:
        svg, removed = clean(path.read_text(encoding="utf-8"), args.tolerance)
        path.write_text(svg, encoding="utf-8")
        print(f"{path}: removed {removed} domestic context rings")


if __name__ == "__main__":
    main()
