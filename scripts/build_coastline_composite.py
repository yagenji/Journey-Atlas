#!/usr/bin/env python3
"""Build a target-country geometry from Natural Earth borders and GSHHS coastline.

Natural Earth 1:10m Admin-0 is the standard national geometry, but at the
1200x760 Country Map scale its coastline is visibly coarse for small or
coast-dominated countries (long straight segments). MAP_SYSTEM.md asks for a
finer source in that case without hand-drawing anything.

This combines two verified sources:
* land borders come from Natural Earth Admin-0 (unchanged);
* coastlines and islands come from GSHHS/GSHHG at the chosen resolution.

composite = (GSHHS land within `--coast-buffer` degrees of the Natural Earth
country) minus every other Natural Earth country polygon.

The result is written as a GeoJSON FeatureCollection with an ADMIN property so
the shared `generate_country_map_with_context.py --source natural-earth` can
draw it like any other Admin-0 dataset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from shapely.geometry import Polygon, box, mapping, shape
from shapely.ops import unary_union


def gshhs_land(bounds: tuple[float, float, float, float], resolution: str):
    from mpl_toolkits.basemap import Basemap

    west, south, east, north = bounds
    m = Basemap(projection="cyl", llcrnrlon=west, llcrnrlat=south, urcrnrlon=east, urcrnrlat=north,
                resolution=resolution, area_thresh=0.01)
    land = []
    for (xs, ys), kind in zip(m.coastpolygons, m.coastpolygontypes):
        if kind != 1 or len(xs) < 3:
            continue
        poly = Polygon(zip(xs, ys))
        land.append(poly if poly.is_valid else poly.buffer(0))
    return unary_union(land)


def nearest_islands(land, target, neighbours, max_distance: float):
    """GSHHS islands that touch no other country and lie nearest to the target.

    An offshore island missing from Natural Earth's coarse coastline belongs to
    the country it is closest to; land that touches a neighbour is never taken.
    """
    parts = list(getattr(land, "geoms", [land]))
    picked = []
    for part in parts:
        if part.is_empty or part.intersects(neighbours):
            continue
        d_target = part.distance(target)
        if d_target <= max_distance and d_target < part.distance(neighbours):
            picked.append(part)
    return unary_union(picked) if picked else Polygon()


def build(natural_earth: Path, country_name: str, bounds: dict, resolution: str, coast_buffer: float,
          merge: tuple[str, ...] = (), island_distance: float = 0.0) -> dict:
    data = json.loads(natural_earth.read_text(encoding="utf-8"))
    features = data["features"]
    target = None
    others = []
    for feature in features:
        geometry = shape(feature["geometry"])
        admin = feature["properties"].get("ADMIN", "")
        if admin.casefold() == country_name.casefold():
            target = geometry if target is None else target.union(geometry)
        elif admin in merge:
            # Areas the JOURNEY ATLAS boundary standard counts as part of the target
            # (e.g. Northern Cyprus and the U.N. buffer zone for Cyprus).
            target = geometry if target is None else target.union(geometry)
        else:
            others.append(geometry)
    if target is None or not any(
            f["properties"].get("ADMIN", "").casefold() == country_name.casefold() for f in features):
        raise SystemExit(f"Country not found in Natural Earth: {country_name}")
    pad = 1.0
    frame = (bounds["west"] - pad, bounds["south"] - pad, bounds["east"] + pad, bounds["north"] + pad)
    view = box(*frame)
    land = gshhs_land(frame, resolution)
    neighbours = unary_union([g for g in others if g.intersects(view)])
    composite = land.intersection(target.buffer(coast_buffer)).difference(neighbours)
    note = f"land within {coast_buffer} deg of the Natural Earth country, minus other Natural Earth countries"
    if island_distance > 0:
        composite = composite.union(nearest_islands(land, target, neighbours, island_distance))
        note += f"; plus islands within {island_distance} deg whose nearest country is the target"
    composite = composite.intersection(view)
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "ADMIN": country_name,
                "SOURCE": f"Natural Earth 1:10m Admin-0 land borders + GSHHS/GSHHG resolution={resolution} coastline "
                          f"({note})",
            },
            "geometry": mapping(composite),
        }],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--natural-earth", required=True, type=Path, help="ne_10m_admin_0_countries GeoJSON (pinned)")
    parser.add_argument("--country-json", required=True, type=Path)
    parser.add_argument("--country-name", required=True, help="Natural Earth ADMIN name")
    parser.add_argument("--resolution", default="h", choices=("i", "h", "f"))
    parser.add_argument("--coast-buffer", default=0.05, type=float)
    parser.add_argument("--island-distance", default=0.0, type=float,
                        help="also take GSHHS islands within this many degrees whose nearest Natural Earth country is the target")
    parser.add_argument("--merge", nargs="*", default=(), help="Natural Earth ADMIN names to treat as part of the target")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    bounds = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]["bounds"]
    result = build(args.natural_earth, args.country_name, bounds, args.resolution, args.coast_buffer, tuple(args.merge),
                   args.island_distance)
    args.output.write_text(json.dumps(result), encoding="utf-8")
    print(f"Wrote {args.output}: {result['features'][0]['properties']['SOURCE']}")


if __name__ == "__main__":
    main()
