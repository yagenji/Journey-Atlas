#!/usr/bin/env python3
"""Build high-detail Sweden/Finland JOURNEY ATLAS maps from geoBoundaries gbOpen ADM0."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

WIDTH = 1200
HEIGHT = 760
STYLE_VERSION = "journey-atlas-map-v1"

CONFIGS = {
    "SWE": {
        "slug": "sweden",
        "name": "Sweden",
        "bounds": (10.2, 55.0, 24.9, 69.4),
        "output": Path("assets/images/sweden/map-atlas-v2.svg"),
    },
    "FIN": {
        "slug": "finland",
        "name": "Finland",
        "bounds": (18.8, 59.4, 31.9, 70.4),
        "output": Path("assets/images/finland/map-atlas-v2.svg"),
    },
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Journey-Atlas-map-builder/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    x = (lon - west) / (east - west) * WIDTH
    y = (north - lat) / (north - south) * HEIGHT
    return x, y


def ring_path(ring: list[list[float]], bounds: tuple[float, float, float, float]) -> str:
    points: list[tuple[float, float]] = []
    last = None
    for lon, lat, *_ in ring:
        x, y = project(lon, lat, bounds)
        point = (round(x, 1), round(y, 1))
        if point != last:
            points.append(point)
            last = point
    if len(points) < 3:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def geometry_paths(geometry: dict, bounds: tuple[float, float, float, float]) -> list[str]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    polygons = [coordinates] if geometry_type == "Polygon" else coordinates if geometry_type == "MultiPolygon" else []
    paths: list[str] = []
    for polygon in polygons:
        rings = [ring_path(ring, bounds) for ring in polygon]
        path = " ".join(ring for ring in rings if ring)
        if path:
            paths.append(path)
    return paths


def render_svg(name: str, paths: list[str], source_url: str) -> str:
    land_d = " ".join(paths)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" role="img" aria-label="Map of {name}" data-map-style="{STYLE_VERSION}">
<metadata>geoBoundaries gbOpen ADM0 simplified geometry (CC BY 4.0): {source_url}</metadata>
<defs>
  <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".55" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
  <linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#e2dbad"/><stop offset=".52" stop-color="#d4cc9b"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/><feOffset in="b" dy="3" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .14 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
</defs>
<rect width="1200" height="760" fill="url(#sea)"/>
<ellipse cx="220" cy="130" rx="300" ry="125" fill="#fbf7ec" opacity=".34"/><ellipse cx="1000" cy="650" rx="330" ry="155" fill="#d5e4e2" opacity=".35"/>
<path d="{land_d}" fill="url(#land)" fill-rule="evenodd" stroke="#31576a" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#shadow)"/>
</svg>'''


def main() -> None:
    qa_dir = Path("map-quality-v2-qa")
    qa_dir.mkdir(exist_ok=True)
    metadata_out = {}

    for iso, config in CONFIGS.items():
        api_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM0/"
        metadata = fetch_json(api_url)
        source_url = metadata["simplifiedGeometryGeoJSON"]
        geojson = fetch_json(source_url)

        paths: list[str] = []
        point_count = 0
        for feature in geojson.get("features", []):
            geometry = feature.get("geometry") or {}
            paths.extend(geometry_paths(geometry, config["bounds"]))
            coords = geometry.get("coordinates") or []
            point_count += len(json.dumps(coords))  # stable relative complexity signal for QA metadata

        if not paths:
            raise RuntimeError(f"No geometry produced for {iso}")

        svg = render_svg(config["name"], paths, source_url)
        config["output"].parent.mkdir(parents=True, exist_ok=True)
        config["output"].write_text(svg, encoding="utf-8")

        metadata_out[config["slug"]] = {
            "api": api_url,
            "source": source_url,
            "boundaryLicense": metadata.get("boundaryLicense"),
            "boundarySource": metadata.get("boundarySource"),
            "buildDate": metadata.get("buildDate"),
            "bounds": config["bounds"],
            "pathCount": len(paths),
            "svgBytes": len(svg.encode("utf-8")),
            "geometryComplexity": point_count,
        }
        print(config["slug"], metadata_out[config["slug"]])

    (qa_dir / "metadata.json").write_text(json.dumps(metadata_out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
