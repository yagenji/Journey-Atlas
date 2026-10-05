#!/usr/bin/env python3
"""JOURNEY ATLAS boundary standard: Japanese map conventions.

JOURNEY ATLAS is a Japanese-language atlas, so territorial depiction follows the
conventions of Japanese school atlases and the Government of Japan:

* Northern Territories (Etorofu, Kunashiri, Shikotan, Habomai) are Japan.
  MOFA: https://www.mofa.go.jp/mofaj/area/hoppo/hoppo.html
* Takeshima is Japan.
* South Sakhalin (south of 50 deg N) and the Kuril Islands from Urup northward are
  "帰属未定" (sovereignty undetermined): neither Japan nor Russia.
* Crimea is Ukraine (Japan does not recognise its annexation by Russia); the
  de facto Crimea line is not drawn as a border.
* The Golan Heights are Syria (occupied by Israel): the Israel-Syria border is
  the line Natural Earth shows from Japan's point of view (FCLASS_JP), and the
  1974 ceasefire line is drawn dashed like other lines of control.
* Kashmir and the China-India border: de facto control lines are kept, but the
  disputed / line-of-control / indefinite segments among India, Pakistan and
  China are drawn dashed (国境未確定).

Natural Earth 1:10m Admin-0 (de facto) assigns the Northern Territories, South
Sakhalin and the northern Kurils to Russia and Takeshima to South Korea. This
module derives an adjusted Admin-0 dataset from Natural Earth so that the shared
map generator draws these areas consistently, and patches existing target paths
whose geometry already came from the de facto dataset.

Selections are by whole Natural Earth polygons inside fixed lon/lat windows (the
islands are separate polygons); South Sakhalin is cut at the 50 deg N parallel,
the 1905-1945 boundary that Japanese atlases show.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.ops import unary_union

# lon/lat windows (WGS84). Urup's west coast is ~149.4E, so 149.0E separates it
# from Etorofu (east tip ~148.9E). Hokkaido is Japan in Natural Earth, so only
# Russian-assigned polygons inside the window are taken.
NORTHERN_TERRITORIES = box(145.3, 43.2, 149.0, 45.7)
KURILS_URUP_NORTHWARD = box(149.0, 45.5, 157.0, 51.0)
SAKHALIN_WINDOW = box(141.0, 45.5, 145.5, 54.6)
SOUTH_SAKHALIN_LIMIT = 50.0
TAKESHIMA = box(131.80, 37.20, 131.92, 37.28)

UNDETERMINED_ADMIN = "Undetermined (South Sakhalin and Kuril Islands)"

# Japanese atlases mark Kashmir and the China-India border as 国境未確定.
UNDETERMINED_BORDER_PARTIES = {"India", "Pakistan", "China", "Siachen Glacier"}

# African boundaries Natural Earth classifies as disputed / indefinite / line of
# control from Japan's point of view (FCLASS_JP, else FEATURECLA): Western
# Sahara (27°40'N), Morocco-Algeria, Hala'ib, Abyei and the Sudan-South Sudan
# line, Ilemi, Ethiopia-South Sudan, Ethiopia-Somalia and Lake Malawi.
AFRICA_UNDETERMINED_PARTIES = {
    "Western Sahara", "Morocco", "Algeria", "Egypt", "Sudan", "South Sudan", "Ethiopia",
    "Kenya", "Somalia", "Malawi", "United Republic of Tanzania",
}
# Golan Heights: the 1974 ceasefire line (line of control) is dashed.
LEVANT_UNDETERMINED_PARTIES = {"Israel", "Syria"}
UNDETERMINED_PARTY_GROUPS = (UNDETERMINED_BORDER_PARTIES, AFRICA_UNDETERMINED_PARTIES, LEVANT_UNDETERMINED_PARTIES)

# Natural Earth disputed areas whose administering country differs from Japan's
# view: (area NAME, de facto country ADMIN, country under the Japanese standard).
REASSIGNED_AREAS = (
    ("Crimea", "Russia", "Ukraine"),
    ("Golan Heights", "Israel", "Syria"),
)

# Lines Japan does not recognise as boundaries at all: Natural Earth marks them
# FCLASS_JP "Unrecognized" (e.g. the Moroccan berm in Western Sahara); Somaliland
# is not recognised by Japan, so its line with Somalia is not a border either.
UNRECOGNIZED_PAIRS = ({"Somaliland", "Somalia"},)

DISPUTED_LINE_CLASSES = (
    "Disputed (please verify)",
    "Line of control (please verify)",
    "Indefinite (please verify)",
    "Indeterminant frontier",
)


def japan_line_class(properties: dict) -> str | None:
    """Natural Earth line class from Japan's point of view."""
    return properties.get("FCLASS_JP") or properties.get("FEATURECLA")


def is_excluded_boundary_line(geometry, properties: dict) -> bool:
    """True for lines that are not national borders under the Japanese standard.

    The Natural Earth de facto line between Hokkaido and Kunashiri, lines Natural
    Earth marks unrecognised from Japan's point of view, and Somaliland-Somalia.
    """
    if (properties.get("FEATURECLA") == "Disputed (please verify)"
            and NORTHERN_TERRITORIES.buffer(0.5).contains(geometry)):
        return True
    if properties.get("FCLASS_JP") in ("Unrecognized", "Claim boundary"):
        # e.g. the Moroccan berm, Baikonur's lease limit, the de facto Crimea line
        return True
    sides = {properties.get("ADM0_LEFT"), properties.get("ADM0_RIGHT")}
    return any(sides == pair for pair in UNRECOGNIZED_PAIRS)


def _polygons(geometry) -> list[Polygon]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return [g for g in getattr(geometry, "geoms", []) if isinstance(g, Polygon)]


def _select(geometry, window) -> list[Polygon]:
    return [p for p in _polygons(geometry) if window.contains(p.representative_point())]


def split_russia(russia):
    """Return (russia_remaining, northern_territories, undetermined)."""
    northern = unary_union(_select(russia, NORTHERN_TERRITORIES))
    kurils = unary_union(_select(russia, KURILS_URUP_NORTHWARD))
    sakhalin = unary_union(_select(russia, SAKHALIN_WINDOW))
    south_box = box(140.0, 40.0, 146.0, SOUTH_SAKHALIN_LIMIT)
    south_sakhalin = sakhalin.intersection(south_box)
    undetermined = unary_union([kurils, south_sakhalin])
    remaining = russia.difference(unary_union([northern, undetermined]))
    if northern.is_empty or kurils.is_empty or south_sakhalin.is_empty:
        raise ValueError("Expected Natural Earth Russia polygons for all standard areas")
    return remaining, northern, undetermined


def split_korea(korea):
    takeshima = unary_union(_select(korea, TAKESHIMA))
    if takeshima.is_empty:
        raise ValueError("Takeshima polygon not found in Natural Earth South Korea")
    return korea.difference(takeshima), takeshima


def reassign_areas(by_admin: dict, disputed_areas: Path) -> dict:
    """Move REASSIGNED_AREAS from the de facto country to Japan's view."""
    areas = {f["properties"].get("NAME"): shape(f["geometry"])
             for f in json.loads(disputed_areas.read_text(encoding="utf-8"))["features"]}
    moved = {}
    for name, source_admin, target_admin in REASSIGNED_AREAS:
        area = areas[name].buffer(0)
        source_geom = shape(by_admin[source_admin]["geometry"]).buffer(0)
        part = source_geom.intersection(area)
        if part.area < area.area * 0.9:
            raise ValueError(f"{name} not found in Natural Earth {source_admin}")
        by_admin[source_admin]["geometry"] = mapping(source_geom.difference(area))
        by_admin[target_admin]["geometry"] = mapping(unary_union([shape(by_admin[target_admin]["geometry"]).buffer(0), part]))
        moved[name] = len(_polygons(part))
    return moved


def build_admin0(source: Path, output: Path, disputed_areas: Path | None = None) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    by_admin = {f["properties"]["ADMIN"]: f for f in data["features"]}
    moved = reassign_areas(by_admin, disputed_areas) if disputed_areas else {}
    russia, japan, korea = (by_admin[n] for n in ("Russia", "Japan", "South Korea"))
    rus_rest, northern, undetermined = split_russia(shape(russia["geometry"]))
    kor_rest, takeshima = split_korea(shape(korea["geometry"]))
    japan_geom = unary_union([shape(japan["geometry"]), northern, takeshima])
    russia["geometry"] = mapping(rus_rest)
    korea["geometry"] = mapping(kor_rest)
    japan["geometry"] = mapping(japan_geom)
    props = {k: None for k in russia["properties"]}
    props.update({"ADMIN": UNDETERMINED_ADMIN, "NAME": UNDETERMINED_ADMIN, "ISO_A2": "-99", "ISO_A2_EH": "-99"})
    data["features"].append({"type": "Feature", "properties": props, "geometry": mapping(undetermined)})
    output.write_text(json.dumps(data), encoding="utf-8")
    return {
        "northern_territories_polygons": len(_polygons(northern)),
        "undetermined_polygons": len(_polygons(undetermined)),
        "takeshima_polygons": len(_polygons(takeshima)),
        "reassigned": moved,
    }


# --- patching an existing single-region target path -------------------------

_RING = re.compile(r"M\s*([^MZ]*?)\s*Z")


def _projector(bounds: dict, antimeridian_shift: bool):
    west, east, south, north = bounds["west"], bounds["east"], bounds["south"], bounds["north"]
    scale_lon = math.cos(math.radians((south + north) / 2))
    projected_w, projected_h = (east - west) * scale_lon, north - south
    canvas = min(1200 / projected_w, 760 / projected_h)
    ox, oy = (1200 - projected_w * canvas) / 2, (760 - projected_h * canvas) / 2

    def project(lon: float, lat: float) -> tuple[float, float]:
        if antimeridian_shift and lon < 0:
            lon += 360
        return ox + (lon - west) * scale_lon * canvas, oy + (north - lat) * canvas

    return project


def _project_geometry(geometry, project):
    out = []
    for poly in _polygons(geometry):
        ext = [project(x, y) for x, y in poly.exterior.coords]
        holes = [[project(x, y) for x, y in r.coords] for r in poly.interiors]
        out.append(Polygon(ext, holes))
    return unary_union(out)


def _path_to_geometry(d: str):
    rings = []
    for chunk in _RING.finditer(d):
        pts = [tuple(float(v) for v in xy.split(",")) for xy in re.split(r"\s*L\s*", chunk.group(1).strip()) if xy.strip()]
        if len(pts) >= 3:
            rings.append(Polygon(pts).buffer(0))
    # even-odd: symmetric difference of rings
    geometry = Polygon()
    for ring in rings:
        geometry = geometry.symmetric_difference(ring)
    return geometry


def _geometry_to_path(geometry) -> str:
    parts = []
    for poly in _polygons(geometry):
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)[:-1]
            if len(coords) < 3:
                continue
            parts.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in coords) + " Z")
    return " ".join(parts)


def patch_russia_svg(svg: str, bounds: dict, admin0: Path) -> tuple[str, float]:
    """Remove Northern Territories and undetermined areas from a Russia target path."""
    data = json.loads(admin0.read_text(encoding="utf-8"))
    by_admin = {f["properties"]["ADMIN"]: f for f in data["features"]}
    removed = unary_union([
        unary_union(_select(shape(by_admin["Japan"]["geometry"]), NORTHERN_TERRITORIES)),
        shape(by_admin[UNDETERMINED_ADMIN]["geometry"]),
    ])
    project = _projector(bounds, 'data-antimeridian="shift-negative-longitudes-plus-360"' in svg)
    # Grow slightly in pixel space so differently simplified source outlines are fully covered.
    cut = _project_geometry(removed, project).buffer(1.2)
    # The 50N parallel is the boundary itself: the buffer must not eat into
    # North Sakhalin, so the cut stays flat along the parallel.
    north_sakhalin_px = _project_geometry(box(141.0, SOUTH_SAKHALIN_LIMIT, 145.5, 54.6), project)
    cut = cut.difference(box(*north_sakhalin_px.bounds))

    target_match = re.search(r'<path d="([^"]*)" fill="url\(#land\)"', svg)
    if not target_match:
        raise ValueError("Russia target path not found")
    target = _path_to_geometry(target_match.group(1))
    remaining = target.difference(cut)
    removed_area = target.area - remaining.area
    new_d = _geometry_to_path(remaining)
    # replace at the match: the same path data may also sit in a clipPath earlier in the file
    svg = svg[:target_match.start(1)] + new_d + svg[target_match.end(1):]
    clip = re.search(r'(<clipPath id="map-context-target-negative"[^>]*><path d=")([^"]*)(")', svg)
    if clip:
        svg = svg.replace(clip.group(0), clip.group(1) + "M 0,0 L 1200,0 L 1200,760 L 0,760 Z " + new_d + clip.group(3), 1)
    return svg, removed_area


def drop_context_inside(svg: str, bounds: dict, windows) -> tuple[str, int]:
    """Remove GSHHS context rings that sit inside areas now drawn as the target.

    Natural Earth and GSHHS island outlines are offset by a few pixels, so the
    shared >=90% redundancy filter keeps them and a second silhouette shows.
    Only rings whose interior point lies inside the given lon/lat windows go.
    """
    from shapely.geometry import Point
    project = _projector(bounds, 'data-antimeridian="shift-negative-longitudes-plus-360"' in svg)
    areas = unary_union([_project_geometry(w, project) for w in windows])
    m = re.search(r'(<g id="geographic-context"[^>]*>\s*<path[^>]* d=")([^"]*)(")', svg)
    if not m:
        raise ValueError("geographic-context path not found")
    kept, dropped = [], 0
    for chunk in _RING.finditer(m.group(2)):
        ring = _path_to_geometry(chunk.group(0))
        if not ring.is_empty and areas.contains(Point(ring.representative_point())):
            dropped += 1
        else:
            kept.append(chunk.group(0))
    return svg.replace(m.group(0), m.group(1) + " ".join(kept) + m.group(3), 1), dropped


def _lines(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return [geometry]
    return [g for g in getattr(geometry, "geoms", []) if g.geom_type == "LineString"]


def _lines_to_path(geometry) -> str:
    return " ".join(
        "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in line.coords)
        for line in _lines(geometry) if line.length >= 0.5
    )


def _parse_lines(d: str):
    from shapely.geometry import LineString, MultiLineString
    out = []
    for chunk in re.split(r"(?=M)", d.strip()):
        nums = re.findall(r"-?\d+(?:\.\d+)?", chunk)
        pts = list(zip(map(float, nums[0::2]), map(float, nums[1::2])))
        if len(pts) >= 2:
            out.append(LineString(pts))
    return MultiLineString(out)


def dash_undetermined(svg: str, bounds: dict, boundary_lines: Path, tolerance_px: float = 8.0,
                      require_target: bool = True) -> tuple[str, float]:
    """Draw 国境未確定 (disputed / line-of-control / indefinite) borders dashed.

    The target outline keeps its own geometry: only the parts of it that run
    within ``tolerance_px`` of a Natural Earth disputed-class line are dashed, so
    datasets that differ by a few pixels never produce a doubled border.
    """
    from shapely.geometry import LineString
    data = json.loads(boundary_lines.read_text(encoding="utf-8"))
    project = _projector(bounds, False)
    view = box(bounds["west"], bounds["south"], bounds["east"], bounds["north"]).buffer(1)
    disputed = []
    for f in data["features"]:
        props = f.get("properties") or {}
        geometry = shape(f["geometry"])
        if japan_line_class(props) not in DISPUTED_LINE_CLASSES or is_excluded_boundary_line(geometry, props):
            continue
        sides = {props.get("ADM0_LEFT"), props.get("ADM0_RIGHT")}
        if not any(sides <= group for group in UNDETERMINED_PARTY_GROUPS):
            continue
        for line in _lines(geometry.intersection(view)):
            disputed.append(LineString([project(x, y) for x, y in line.coords]))
    if not disputed:
        return svg, 0.0
    zone = unary_union(disputed).buffer(tolerance_px)

    targets = [m for m in re.finditer(r"<path\b[^>]*?/>", svg)
               if 'fill="url(#land)"' in m.group(0) and 'stroke="#31576a"' in m.group(0)]
    outline_only = False
    if not targets:
        # target fill without stroke plus a separate fill="none" outline path
        targets = [m for m in re.finditer(r"<path\b[^>]*?/>", svg)
                   if 'fill="none"' in m.group(0) and 'stroke="#31576a"' in m.group(0)]
        outline_only = bool(targets)
    if not targets and not require_target:
        targets = []
    elif not targets:
        raise ValueError("Target path with the standard outline was not found")
    solid_parts, dashed_parts = [Polygon().boundary], [Polygon().boundary]
    width = "1.5"
    for m in targets:
        tag = m.group(0)
        if "transform=" in tag:
            raise ValueError("Transformed target paths are not supported")
        width = (re.search(r'stroke-width="([^"]+)"', tag) or [None, "1.5"])[1]
        edge = _svg_d_to_geometry(re.search(r'\sd="([^"]*)"', tag).group(1)).boundary
        dashed_parts.append(edge.intersection(zone))
        solid_parts.append(edge.difference(zone))
    dashed, solid = unary_union(dashed_parts), unary_union(solid_parts)
    if dashed.length == 0:
        target_dashed = False
    else:
        target_dashed = True
        if outline_only:
            anchor = targets[-1].start()
            for m in reversed(targets):
                svg = svg[:m.start()] + svg[m.end():]
            anchor_end = anchor
        else:
            for m in reversed(targets):
                stripped = re.sub(r'\sstroke="#31576a"', ' stroke="none"', m.group(0), count=1)
                svg = svg[:m.start()] + stripped + svg[m.end():]
            anchor_end = [m for m in re.finditer(r"<path\b[^>]*?/>", svg)
                          if 'fill="url(#land)"' in m.group(0) and 'stroke="none"' in m.group(0)][-1].end()
        outline = (
            f'<g id="target-outline" fill="none" stroke="#31576a" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round">'
            f'<path d="{_lines_to_path(solid)}"/>'
            f'<path data-boundary="undetermined" stroke-dasharray="5 4" d="{_lines_to_path(dashed)}"/></g>'
        )
        svg = svg[:anchor_end] + "\n" + outline + svg[anchor_end:]

    c = re.search(r'(<g id="context-national-borders"[^>]*>)<path d="([^"]*)"/></g>', svg)
    if c:
        lines = _parse_lines(c.group(2))
        c_dashed, c_solid = lines.intersection(zone), lines.difference(zone)
        replacement = (
            f'{c.group(1)}<path d="{_lines_to_path(c_solid)}"/>'
            f'<path data-boundary="undetermined" stroke-dasharray="4 3" d="{_lines_to_path(c_dashed)}"/></g>'
        )
        svg = svg.replace(c.group(0), replacement, 1)
    return svg, dashed.length if target_dashed else 0.0


def _svg_d_to_geometry(d: str):
    """Even-odd polygon from any SVG path data (curves sampled)."""
    from svgelements import Path as SvgPath, Move, Close, Line
    geometry = Polygon()
    ring: list[tuple[float, float]] = []

    def flush():
        nonlocal geometry, ring
        if len(ring) >= 3:
            geometry = geometry.symmetric_difference(Polygon(ring).buffer(0))
        ring = []

    for seg in SvgPath(d):
        if isinstance(seg, Move):
            flush()
            ring = [(seg.end.x, seg.end.y)]
        elif isinstance(seg, Close):
            flush()
        elif isinstance(seg, Line):
            ring.append((seg.end.x, seg.end.y))
        else:
            ring.extend((pt.x, pt.y) for pt in (seg.point(i / 8) for i in range(1, 9)))
    flush()
    return geometry


def build_boundary_lines(land_lines: Path, disputed_lines: Path, output: Path) -> int:
    """Natural Earth land boundary lines plus the disputed-area lines Japan's
    point of view (FCLASS_JP) shows as disputed, e.g. Western Sahara's
    northern boundary at 27°40'N, which the de facto dataset omits."""
    data = json.loads(land_lines.read_text(encoding="utf-8"))
    extra = []
    for f in json.loads(disputed_lines.read_text(encoding="utf-8"))["features"]:
        jp = (f.get("properties") or {}).get("FCLASS_JP")
        if jp in DISPUTED_LINE_CLASSES:
            extra.append(f)
        elif jp == "International boundary (verify)" and not NORTHERN_TERRITORIES.buffer(1.5).intersects(shape(f["geometry"])):
            # a border only from Japan's point of view, e.g. Israel-Syria west of the Golan
            extra.append(f)
    data["features"] = data["features"] + extra
    output.write_text(json.dumps(data), encoding="utf-8")
    return len(extra)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    lines = sub.add_parser("build-boundary-lines", help="Write Japanese-standard boundary lines (land + JP-disputed claim lines)")
    lines.add_argument("--land-lines", required=True, type=Path, help="ne_10m_admin_0_boundary_lines_land.geojson")
    lines.add_argument("--disputed-lines", required=True, type=Path, help="ne_10m_admin_0_boundary_lines_disputed_areas.geojson")
    lines.add_argument("--output", required=True, type=Path)
    build = sub.add_parser("build-admin0", help="Write a Japanese-standard Admin-0 GeoJSON derived from Natural Earth")
    build.add_argument("--input", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--disputed-areas", type=Path, help="ne_10m_admin_0_disputed_areas.geojson (Crimea, Golan Heights)")
    patch = sub.add_parser("patch-russia", help="Apply the standard to an existing Russia map SVG")
    patch.add_argument("--country-json", required=True, type=Path)
    patch.add_argument("--admin0", required=True, type=Path, help="Output of build-admin0")
    patch.add_argument("--input", required=True, type=Path)
    patch.add_argument("--output", required=True, type=Path)
    clean = sub.add_parser("clean-japan-context", help="Drop GSHHS context rings under Northern Territories / Takeshima on a Japan map")
    clean.add_argument("--country-json", required=True, type=Path)
    clean.add_argument("--svg", required=True, type=Path)
    dash = sub.add_parser("dash-undetermined", help="Dash disputed / line-of-control borders (国境未確定) on a map")
    dash.add_argument("--country-json", required=True, type=Path)
    dash.add_argument("--boundary-lines", required=True, type=Path, help="Natural Earth ne_10m_admin_0_boundary_lines_land.geojson")
    dash.add_argument("--input", required=True, type=Path)
    dash.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "dash-undetermined":
        bounds = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]["bounds"]
        svg, length = dash_undetermined(args.input.read_text(encoding="utf-8"), bounds, args.boundary_lines)
        args.output.write_text(svg, encoding="utf-8")
        print(f"Dashed {length:.0f} px of target outline as undetermined border")
        return
    if args.command == "clean-japan-context":
        bounds = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]["bounds"]
        svg, n = drop_context_inside(args.svg.read_text(encoding="utf-8"), bounds, [NORTHERN_TERRITORIES, TAKESHIMA])
        args.svg.write_text(svg, encoding="utf-8")
        print(f"Dropped {n} duplicate context rings")
        return
    if args.command == "build-boundary-lines":
        added = build_boundary_lines(args.land_lines, args.disputed_lines, args.output)
        print(f"Wrote {args.output}: added {added} Japanese-standard disputed lines")
        return
    if args.command == "build-admin0":
        print(json.dumps(build_admin0(args.input, args.output, args.disputed_areas)))
    else:
        bounds = json.loads(args.country_json.read_text(encoding="utf-8"))["map"]["bounds"]
        svg, area = patch_russia_svg(args.input.read_text(encoding="utf-8"), bounds, args.admin0)
        args.output.write_text(svg, encoding="utf-8")
        print(f"Removed {area:.1f} px^2 of Northern Territories / undetermined areas from the Russia target")


if __name__ == "__main__":
    main()
