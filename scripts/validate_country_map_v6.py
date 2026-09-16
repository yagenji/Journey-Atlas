#!/usr/bin/env python3
"""Map hard gates for new Content QA v6 Countries.

Checks run before visual production/review:
- Country map SVG must be self-contained (no nested/external image/use href).
- Real Scene coordinates must project into the rendered country land geometry.
  mapOffset is deliberately ignored: offsets may move labels, never geography.
"""
from __future__ import annotations

import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data/countries"
W, H = 1200.0, 760.0
TOKEN_RE = re.compile(r"[MmLlHhVvZz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def project(coords: dict, bounds: dict, rect=(0.0, 0.0, W, H)):
    lat, lon = coords.get("latitude"), coords.get("longitude")
    n, s, w, e = bounds.get("north"), bounds.get("south"), bounds.get("west"), bounds.get("east")
    if not all(isinstance(v, (int, float)) for v in (lat, lon, n, s, w, e)) or e <= w or n <= s:
        return None
    rx, ry, rw, rh = rect
    mid = (s + n) / 2
    lon_scale = math.cos(math.radians(mid))
    pw, ph = (e - w) * lon_scale, n - s
    scale = min(rw / pw, rh / ph)
    dw, dh = pw * scale, ph * scale
    ox, oy = rx + (rw - dw) / 2, ry + (rh - dh) / 2
    return ox + (lon - w) * lon_scale * scale, oy + (n - lat) * scale


def scene_point(scene: dict, map_data: dict):
    coords = scene.get("coordinates") if isinstance(scene.get("coordinates"), dict) else {}
    regions = map_data.get("regions") if isinstance(map_data.get("regions"), list) else []
    rid = scene.get("mapRegion")
    region = None
    if isinstance(rid, str):
        region = next((r for r in regions if isinstance(r, dict) and r.get("id") == rid), None)
    if region is None:
        for r in regions:
            if not isinstance(r, dict):
                continue
            b = r.get("bounds") or {}
            lat, lon = coords.get("latitude"), coords.get("longitude")
            if all(isinstance(v, (int, float)) for v in (lat, lon, b.get("north"), b.get("south"), b.get("west"), b.get("east"))):
                if b["south"] <= lat <= b["north"] and b["west"] <= lon <= b["east"]:
                    region = r
                    break
    if region:
        rect = region.get("rect") or {}
        return project(coords, region.get("bounds") or {}, (float(rect.get("x", 0)), float(rect.get("y", 0)), float(rect.get("width", W)), float(rect.get("height", H))))
    return project(coords, map_data.get("bounds") or {})


def parse_polygons(d: str):
    tokens = TOKEN_RE.findall(d)
    polys, poly = [], []
    i, cmd, x, y, sx, sy = 0, None, 0.0, 0.0, 0.0, 0.0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in "Zz":
                if len(poly) >= 3:
                    polys.append(poly)
                poly = []; x, y = sx, sy
            continue
        if cmd is None:
            return []
        try:
            if cmd in "MmLl":
                nx, ny = float(tokens[i]), float(tokens[i+1]); i += 2
                if cmd.islower(): nx, ny = x + nx, y + ny
                x, y = nx, ny
                if cmd in "Mm":
                    if poly and len(poly) >= 3: polys.append(poly)
                    poly = [(x, y)]; sx, sy = x, y
                    cmd = "l" if cmd == "m" else "L"
                else:
                    poly.append((x, y))
            elif cmd in "Hh":
                nx = float(tokens[i]); i += 1
                x = x + nx if cmd == "h" else nx; poly.append((x, y))
            elif cmd in "Vv":
                ny = float(tokens[i]); i += 1
                y = y + ny if cmd == "v" else ny; poly.append((x, y))
            else:
                return []
        except (ValueError, IndexError):
            return []
    if poly and len(poly) >= 3: polys.append(poly)
    return polys


def contains(poly, p):
    """Strict polygon interior; tolerance must NOT participate in even-odd parity."""
    px, py = p
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > py) != (y2 > py):
            xin = (x2 - x1) * (py - y1) / (y2 - y1) + x1
            if px < xin:
                inside = not inside
    return inside


def near_boundary(poly, p, tolerance=4.0):
    """Allow coarse coastlines once, after the exact even-odd fill is evaluated."""
    px, py = p
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        if not (dx or dy):
            continue
        u = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        if math.hypot(px - (x1 + u * dx), py - (y1 + u * dy)) <= tolerance:
            return True
    return False


def on_land_in_path(group, p):
    # SVG fill-rule="evenodd" uses exact subpath crossings. Applying the
    # coastline tolerance to each subpath first cancels nearby mainland/island
    # hits, even though the renderer visibly fills the scene's location.
    if sum(contains(poly, p) for poly in group) % 2:
        return True
    return any(near_boundary(poly, p) for poly in group)


def validate(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("contentQaVersion") or 1) < 6:
        return []
    errors = []
    svg_rel = (data.get("map") or {}).get("svg")
    if not isinstance(svg_rel, str) or not svg_rel.endswith(".svg"):
        return [f"{path.name}: Content QA v6 requires map.svg"]
    svg_path = ROOT / svg_rel
    if not svg_path.exists():
        return [f"{path.name}: map SVG missing: {svg_rel}"]
    text = svg_path.read_text(encoding="utf-8")
    lowered = text.lower()
    if "<image" in lowered or "<use" in lowered or "<foreignobject" in lowered or "xlink:href=" in lowered or re.search(r"\shref\s*=", lowered):
        errors.append(f"{path.name}: map SVG must be self-contained; nested/external image/use/href is forbidden")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return errors + [f"{path.name}: invalid map SVG XML: {exc}"]
    path_groups = []
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] != "path":
            continue
        d = el.attrib.get("d", "")
        polys = parse_polygons(d)
        if polys:
            path_groups.append(polys)
    if not path_groups:
        errors.append(f"{path.name}: map SVG has no parseable closed land path geometry")
        return errors
    map_data = data.get("map") or {}
    for idx, scene in enumerate(data.get("scenes") or [], 1):
        if not isinstance(scene, dict):
            continue
        p = scene_point(scene, map_data)
        if p is None:
            continue
        if not any(on_land_in_path(group, p) for group in path_groups):
            errors.append(f"{path.name}: Scene {idx} real coordinate projects outside rendered country land geometry; correct coordinates/map geometry, never hide it with mapOffset")
    return errors


def main():
    paths = [Path(p) for p in sys.argv[1:]] or sorted(COUNTRY_DIR.glob("*.json"))
    errors = []
    for p in paths:
        errors.extend(validate(p))
    if errors:
        print("Content QA v6 Map: FAIL")
        for e in errors: print(f"- {e}")
        return 1
    print(f"Content QA v6 Map: PASS ({len(paths)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
