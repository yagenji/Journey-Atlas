#!/usr/bin/env python3
"""One-time QA builder for Sweden/Finland detailed JOURNEY ATLAS maps."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import unary_union

WIDTH = 1200
HEIGHT = 760

CONFIGS = {
    "SWE": {
        "slug": "sweden",
        "name": "Sweden",
        "bounds": (10.2, 55.0, 24.9, 69.4),
        "output": "assets/images/sweden/map-atlas-v2.svg",
    },
    "FIN": {
        "slug": "finland",
        "name": "Finland",
        "bounds": (18.8, 59.4, 31.9, 70.4),
        "output": "assets/images/finland/map-atlas-v2.svg",
    },
}


def project(lon: float, lat: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    west, south, east, north = bounds
    return (
        (lon - west) / (east - west) * WIDTH,
        (north - lat) / (north - south) * HEIGHT,
    )


def polygon_parts(geometry) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    return []


def ring_path(coords, bounds) -> str:
    points = []
    previous = None
    for lon, lat in coords:
        x, y = project(lon, lat, bounds)
        point = (round(x, 1), round(y, 1))
        if point != previous:
            points.append(point)
            previous = point
    if len(points) < 3:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z"


def polygon_path(polygon: Polygon, bounds) -> str:
    parts = [ring_path(polygon.exterior.coords, bounds)]
    parts.extend(ring_path(ring.coords, bounds) for ring in polygon.interiors)
    return " ".join(part for part in parts if part)


def render_svg(name: str, source_url: str, pieces: list[Polygon], bounds) -> str:
    land_d = " ".join(polygon_path(piece, bounds) for piece in pieces)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 760" role="img" aria-label="Map of {name}" data-map-style="journey-atlas-map-v1">
<metadata>geoBoundaries gbOpen ADM1 dissolved; {source_url}</metadata>
<defs>
  <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eef2ef"/><stop offset=".55" stop-color="#e4eceb"/><stop offset="1" stop-color="#dce7e7"/></linearGradient>
  <linearGradient id="land" x1=".12" y1=".08" x2=".88" y2=".92"><stop offset="0" stop-color="#e2dbad"/><stop offset=".52" stop-color="#d4cc9b"/><stop offset="1" stop-color="#c8bf8a"/></linearGradient>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/><feOffset in="b" dy="3" result="o"/><feColorMatrix in="o" type="matrix" values="0 0 0 0 .12 0 0 0 0 .22 0 0 0 0 .28 0 0 0 .14 0"/><feBlend in="SourceGraphic" mode="normal"/></filter>
</defs>
<rect width="1200" height="760" fill="url(#sea)"/>
<ellipse cx="220" cy="130" rx="300" ry="125" fill="#fbf7ec" opacity=".34"/>
<ellipse cx="1000" cy="650" rx="330" ry="155" fill="#d5e4e2" opacity=".35"/>
<path d="{land_d}" fill="url(#land)" fill-rule="evenodd" stroke="#31576a" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#shadow)"/>
</svg>"""


def main() -> None:
    previews = []
    metadata = {}

    for iso, config in CONFIGS.items():
        api_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM1/"
        with urllib.request.urlopen(api_url) as response:
            api = json.load(response)

        source_url = api["gjDownloadURL"]
        with urllib.request.urlopen(source_url) as response:
            geojson = json.load(response)

        merged = unary_union([shape(feature["geometry"]) for feature in geojson["features"]])
        merged = merged.simplify(0.0015, preserve_topology=True)
        pieces = sorted(polygon_parts(merged), key=lambda geometry: geometry.area, reverse=True)

        svg = render_svg(config["name"], source_url, pieces, config["bounds"])
        output = Path(config["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg, encoding="utf-8")

        preview = Path(f"/tmp/{config['slug']}-map-v2.png")
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(preview),
            output_width=WIDTH,
            output_height=HEIGHT,
        )
        previews.append((config["slug"], preview))

        metadata[config["slug"]] = {
            "api": api_url,
            "source": source_url,
            "boundaryLicense": api.get("boundaryLicense"),
            "boundarySource": api.get("boundarySource"),
            "buildDate": api.get("buildDate"),
            "pieces": len(pieces),
            "bytes": len(svg.encode("utf-8")),
        }
        print(config["slug"], metadata[config["slug"]])

    sheet = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(sheet)
    y = 0
    for slug, preview in previews:
        image = Image.open(preview).convert("RGB")
        draw.text((10, y + 8), slug.upper(), fill="black")
        sheet.paste(image, (0, y + 40))
        y += 800
    sheet.save("/tmp/map-quality-v2-contact-sheet.png")
    Path("/tmp/map-quality-v2-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
