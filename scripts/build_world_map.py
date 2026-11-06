#!/usr/bin/env python3
"""Generate assets/maps/world-states.svg from Natural Earth (public domain).

The explorer's framing in assets/js/map-regions.js is written in this map's
coordinates: Robinson, central meridian 10E, 1000 x 507.209 units. Keep them.

Inputs are Natural Earth 1:10m GeoJSON files (ne_10m_admin_0_map_units,
ne_10m_admin_0_disputed_areas and ne_10m_lakes). Territorial handling follows
scripts/japan_boundary_standard.py: Northern Territories and Takeshima with
Japan, Crimea with Ukraine, the Golan Heights with Syria, and South Sakhalin
and the Kuril Islands from Urup northward in the non-selectable group XU.
The Morocco-held part of Western Sahara (a Natural Earth disputed area named
"Morocco") stays with Western Sahara, and the Halayib Triangle with Sudan.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from pyproj import Proj
from shapely import segmentize, set_precision, transform as shapely_transform
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union

from japan_boundary_standard import _polygons, split_korea, split_russia

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "maps" / "world-states.svg"
WIDTH, HEIGHT = 1000.0, 507.209
CENTRAL_MERIDIAN = 10.0
# The Bering Strait, just east of Chukotka's tip; Samoa and Niue stay on the right edge.
SEAM = -169.0
SIMPLIFY = 0.07  # map units; about 0.75 km at the equator is kept for small islands
MIN_ISLAND_AREA = 0.004  # map units squared; smaller islets add bytes, not shape
ISO_OVERRIDES = {
    # Natural Earth map units without an ISO code, assigned as the previous map did.
    "Somaliland": "SO", "Northern Cyprus": "CY", "Cyprus No Mans Area": "CY",
    "Akrotiri Sovereign Base Area": "CY", "Dhekelia Sovereign Base Area": "CY",
    "Korean Demilitarized Zone (south)": "KR", "Korean Demilitarized Zone (north)": "KP",
    "US Naval Base Guantanamo Bay": "CU", "Siachen Glacier": "IN",
    "Southern Patagonian Ice Field": "AR", "Bir Tawil": "SD",
}
# Outlying territories the previous map drew as part of the parent group.
ISO_ALIASES = {"BQ": "NL", "NF": "AU", "CC": "AU", "CX": "AU", "HM": "AU", "AX": "FI", "BV": "NO", "SJ": "NO"}
UNASSIGNED = {
    "Paracel Islands", "Spratly Islands", "Scarborough Reef",
    "Bajo Nuevo Bank (Petrel Is.)", "Serranilla Bank",
}
LAKE_MAX_SCALERANK = 1
REASSIGNED = (
    ("Crimea", "RU", "UA"), ("Golan Heights", "IL", "SY"),
    ("Morocco", "MA", "EH"), ("Halayib Triangle", "EG", "SD"),
)


def load_units(path: Path) -> dict[str, object]:
    pieces: dict[str, list] = defaultdict(list)
    for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
        props = feature["properties"]
        name = props["GEOUNIT"]
        if name in UNASSIGNED:
            continue
        iso = ISO_OVERRIDES.get(name, props["ISO_A2_EH"])
        if iso == "-99":
            raise ValueError(f"No map code for {name}")
        pieces[ISO_ALIASES.get(iso, iso)].append(shape(feature["geometry"]).buffer(0))
    return {iso: unary_union(parts) for iso, parts in pieces.items()}


def apply_japan_standard(units: dict, disputed: Path) -> None:
    areas = {f["properties"].get("NAME"): shape(f["geometry"]).buffer(0)
             for f in json.loads(disputed.read_text(encoding="utf-8"))["features"]}
    for name, source, target in REASSIGNED:
        part = units[source].intersection(areas[name])
        if part.area < areas[name].area * 0.9:
            raise ValueError(f"{name} not found in {source}")
        units[source] = units[source].difference(areas[name])
        units[target] = unary_union([units[target], part])
    units["RU"], northern, undetermined = split_russia(units["RU"])
    units["KR"], takeshima = split_korea(units["KR"])
    units["JP"] = unary_union([units["JP"], northern, takeshima])
    units["XU"] = undetermined
    # Natural Earth stops near 85S; the rest of the continent is land to the pole.
    units["AQ"] = unary_union([units["AQ"], box(-180, -90, 180, -84.9)])


def remove_lakes(units: dict, lakes: Path) -> None:
    water = [shape(f["geometry"]).buffer(0)
             for f in json.loads(lakes.read_text(encoding="utf-8"))["features"]
             if f["properties"]["scalerank"] <= LAKE_MAX_SCALERANK
             and f["properties"]["featurecla"] == "Lake"]  # not dry salt lakes such as Eyre
    merged = unary_union(water)
    for iso in units:
        units[iso] = units[iso].difference(merged)


def build_projector():
    # +over keeps Chukotka's tip on the right edge instead of wrapping it.
    robinson = Proj(f"+proj=robin +lon_0={CENTRAL_MERIDIAN} +R=1 +over")
    xmax, _ = robinson(CENTRAL_MERIDIAN + 180, 0)
    scale = WIDTH / (2 * xmax)

    def project(coords):
        x, y = robinson(coords[:, 0], coords[:, 1])
        coords = coords.copy()
        coords[:, 0] = WIDTH / 2 + x * scale
        coords[:, 1] = HEIGHT / 2 - y * scale
        return coords
    return project


def cut_at_seam(geometry):
    """Move everything west of the map's seam to the right-hand edge."""
    west = geometry.intersection(box(-180, -90, SEAM, 90))
    if west.is_empty:
        return geometry
    east = geometry.intersection(box(SEAM, -90, 180, 90))
    return unary_union([east, translate(west, 360, 0)])


def project_country(geometry, project):
    dense = segmentize(cut_at_seam(geometry), 1.0)
    return shapely_transform(dense, project).buffer(0)


def tidy(geometry):
    polygons = _polygons(geometry)
    if not polygons:
        return geometry
    largest = max(p.area for p in polygons)
    kept = []
    for polygon in polygons:
        if polygon.area < MIN_ISLAND_AREA and polygon.area < largest:
            continue
        simple = polygon.simplify(SIMPLIFY, preserve_topology=True)
        kept.append(simple if not simple.is_empty else polygon)
    return MultiPolygon(kept)


def ring_path(ring) -> str:
    points = list(ring.coords)[:-1]
    text = []
    last = None
    for x, y in points:
        pair = f"{x:.2f} {y:.2f}"
        if pair != last:
            text.append(pair)
        last = pair
    return "M" + "L".join(text) + "Z" if len(text) >= 3 else ""


def geometry_path(geometry) -> str:
    return "".join(
        ring_path(ring)
        for polygon in _polygons(geometry)
        for ring in (polygon.exterior, *polygon.interiors)
    )


def render(units: dict) -> str:
    project = build_projector()
    groups = []
    for iso in sorted(units):
        path = geometry_path(tidy(project_country(units[iso], project)))
        if path:
            groups.append(f'<g id="{iso}"><path fill-rule="evenodd" d="{path}"/></g>')
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- JOURNEY ATLAS world map, generated by scripts/build_world_map.py from Natural Earth "
        "1:10m Admin-0 map units (public domain). Robinson, central meridian 10E. -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:g} {HEIGHT:g}">\n'
        + "\n".join(groups) + "\n</svg>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-units", required=True, type=Path)
    parser.add_argument("--disputed-areas", required=True, type=Path)
    parser.add_argument("--lakes", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    units = load_units(args.map_units)
    apply_japan_standard(units, args.disputed_areas)
    remove_lakes(units, args.lakes)
    args.output.write_text(render(units), encoding="utf-8")
    print(f"Wrote {args.output} ({args.output.stat().st_size / 1024:.0f} KB, {len(units)} groups)")


if __name__ == "__main__":
    main()
