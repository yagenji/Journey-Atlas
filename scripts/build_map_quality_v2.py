#!/usr/bin/env python3
"""Build high-detail Sweden/Finland JOURNEY ATLAS maps from geoBoundaries gbOpen."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union

WIDTH = 1200
HEIGHT = 760
STYLE_VERSION = "journey-atlas-map-v1"
QUALITY_PROFILE = "atlas-v2"

CONFIGS = {
    "SWE": {
        "slug": "sweden",
        "name": "Sweden",
        "bounds": (10.2, 55.0, 24.9, 69.4),
        "output": Path("assets/images/sweden/map-atlas-v2.svg"),
        "adm": "ADM1",
        "dissolve": True,
    },
    "FIN": {
        "slug": "finland",
        "name": "Finland",
        "bounds": (18.8, 59.4, 31.9, 70.4),
        "output": Path("assets/images/finland/map-atlas-v2.svg"),
        "adm": "ADM0",
        "dissolve": False,
    },
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Journey-Atlas-map-builder/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    x = (lon - west) / (east - west) * WIDTH
    y = (north - lat) / (north - south) * HEIGHT
    return x, y


def ring_path(coords, bounds: tuple[float, float, float, float]) -> str:
    points: list[tuple[float, float]] = []
    last = None
    for lon, lat, *_ in coords:
        x, y = project(lon, lat, bounds)
        point = (round(x, 1), round(y, 1))
        if point != last:
            points.append(point)
            last = point
    if len(points) < 3:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def polygons_from_geometry(geometry) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return []


def polygon_path(polygon: Polygon, bounds: tuple[float, float, float, float]) -> str:
    rings = [ring_path(polygon.exterior.coords, bounds)]
    rings.extend(ring_path(interior.coords, bounds) for interior in polygon.interiors)
    return " ".join(ring for ring in rings if ring)


def render_svg(name: str, polygons: list[Polygon], source_url: str, adm: str, bounds) -> str:
    land_d = " ".join(polygon_path(polygon, bounds) for polygon in polygons)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" role="img" aria-label="Map of {name}" data-map-style="{STYLE_VERSION}" data-map-quality="{QUALITY_PROFILE}">
<metadata>geoBoundaries gbOpen {adm} geometry, country-unioned for display: {source_url}</metadata>
<defs>
  <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".55" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
  <linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#e2dbad"/><stop offset=".52" stop-color="#d4cc9b"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/><feOffset in="b" dy="3" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .14 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
</defs>
<rect width="1200" height="760" fill="url(#sea)"/>
<ellipse cx="220" cy="130" rx="300" ry="125" fill="#fbf7ec" opacity=".34"/><ellipse cx="1000" cy="650" rx="330" ry="155" fill="#d5e4e2" opacity=".35"/>
<path d="{land_d}" fill="url(#land)" fill-rule="evenodd" stroke="#31576a" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#shadow)"/>
</svg>'''


def update_country_config(config: dict, metadata: dict) -> None:
    path = Path("data/countries") / f"{config['slug']}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    west, south, east, north = config["bounds"]
    data["map"]["bounds"] = {"north": north, "south": south, "west": west, "east": east}
    data["map"]["svg"] = str(config["output"])
    license_name = metadata.get("boundaryLicense") or "see upstream"
    build_date = metadata.get("buildDate") or "unknown"
    detail = "dissolved" if config["dissolve"] else "simplified"
    data["map"]["source"] = (
        f"geoBoundaries gbOpen {config['name']} {config['adm']} {detail} "
        f"(build {build_date}; {license_name}); illustrated treatment: JOURNEY ATLAS"
    )
    data["map"]["qualityProfile"] = QUALITY_PROFILE
    data["map"]["markerQaVersion"] = 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    qa_dir = Path("map-quality-v2-qa")
    qa_dir.mkdir(exist_ok=True)
    metadata_out = {}

    for iso, config in CONFIGS.items():
        api_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso}/{config['adm']}/"
        metadata = fetch_json(api_url)
        source_url = metadata["gjDownloadURL"] if config["dissolve"] else metadata["simplifiedGeometryGeoJSON"]
        geojson = fetch_json(source_url)

        geometries = [shape(feature["geometry"]) for feature in geojson.get("features", []) if feature.get("geometry")]
        if not geometries:
            raise RuntimeError(f"No geometry produced for {iso}")

        merged = unary_union(geometries)
        # Preserve islands and coastline character; remove only detail well below one display pixel.
        merged = merged.simplify(0.0008 if iso == "SWE" else 0.0006, preserve_topology=True)
        polygons = sorted(polygons_from_geometry(merged), key=lambda geom: geom.area, reverse=True)
        if not polygons:
            raise RuntimeError(f"No polygon geometry produced for {iso}")

        svg = render_svg(config["name"], polygons, source_url, config["adm"], config["bounds"])
        config["output"].parent.mkdir(parents=True, exist_ok=True)
        config["output"].write_text(svg, encoding="utf-8")
        update_country_config(config, metadata)

        point_count = sum(len(polygon.exterior.coords) + sum(len(interior.coords) for interior in polygon.interiors) for polygon in polygons)
        metadata_out[config["slug"]] = {
            "api": api_url,
            "source": source_url,
            "boundaryLicense": metadata.get("boundaryLicense"),
            "boundarySource": metadata.get("boundarySource"),
            "buildDate": metadata.get("buildDate"),
            "bounds": config["bounds"],
            "adm": config["adm"],
            "polygonCount": len(polygons),
            "pointCount": point_count,
            "svgBytes": len(svg.encode("utf-8")),
        }
        print(config["slug"], metadata_out[config["slug"]])

    (qa_dir / "metadata.json").write_text(json.dumps(metadata_out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
