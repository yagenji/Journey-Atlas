#!/usr/bin/env python3
"""Focused quality gate for the published New Caledonia Region."""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/regions/france/new-caledonia.json"
CHECKSUMS = ROOT / "docs/region-images/new-caledonia-manifest.json"


def die(message: str) -> None:
    raise AssertionError(message)


def collect_sources(value: object) -> list[str]:
    keys: list[str] = []
    if isinstance(value, list):
        for v in value:
            keys += collect_sources(v)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k in ("sourceKey", "coordinateSourceKey") and v:
                keys.append(str(v))
            elif k == "sourceKeys":
                keys += [str(item) for item in v]
            else:
                keys += collect_sources(v)
    return keys


def expected_hashes() -> dict[str, str]:
    manifest = json.loads(CHECKSUMS.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for item in manifest["items"]:
        filename = item["name"]
        digest = item["sha256"]
        if filename in result or not re.fullmatch(r"[a-f0-9]{64}", digest):
            die("Invalid image checksum in approved manifest")
        result[filename] = digest
    return result


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert (data["parentSlug"], data["slug"], data["regionPublished"]) == (
        "france", "new-caledonia", True
    )
    assert data["schemaVersion"] == 1
    scenes, taste = data["scenes"], data["taste"]["items"]
    assert len(scenes) == 8 and len(taste) == 4
    assert len({scene["id"] for scene in scenes}) == 8
    assert len({food["id"] for food in taste}) == 4
    keys = set(collect_sources(data))
    assert not (keys - set(data["sources"])), f"Unknown source keys: {keys - set(data['sources'])}"

    paths = [data["hero"]["image"]] + [s["image"] for s in scenes] + [
        f["image"] for f in taste
    ]
    assert len(paths) == len(set(paths)) == 13
    hashes = expected_hashes()
    assert len(hashes) == 13
    assert {Path(p).name for p in paths} == set(hashes)
    thumbnails: dict[str, list[int]] = {}
    for i, relative in enumerate(paths):
        path = ROOT / relative
        if not path.is_file():
            die(f"Approved image is missing: {relative}")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != hashes[path.name]:
            die(f"Image bytes differ from the approved file: {relative}")
        with Image.open(io.BytesIO(raw)) as img:
            img.load()
            assert img.format == "WEBP", relative
            width, height = img.size
            minimum = (1200, 760) if i == 0 else (1200, 800)
            assert width >= minimum[0] and height >= minimum[1], (relative, img.size)
            # The already-approved hero is 1672×941 (16:9). Do NOT silently crop.
            if i:
                assert abs(width / height - 1.5) <= 0.015, (relative, img.size)
            thumbs = img.convert("L").resize((32, 32))
            thumbnails[relative] = list(thumbs.getdata())
    for (an, aa), (bn, bb) in combinations(thumbnails.items(), 2):
        average_difference = sum(abs(a - b) for a, b in zip(aa, bb)) / len(aa)
        if average_difference < 5.0:
            die(f"Potentially duplicated image content: {an}, {bn}")
    print("PASS: 13 approved WebPs, exact SHA-256, dimensions, uniqueness")

    svg = ET.parse(ROOT / data["map"]["svg"]).getroot()
    assert svg.attrib.get("viewBox") == "0 0 1200 760"
    assert svg.attrib.get("data-map-projection") == "local-equirectangular-fit-v1"
    bounds = data["map"]["bounds"]
    w, s, e, n = (bounds[k] for k in ("west", "south", "east", "north"))
    cosine = math.cos(math.radians((s + n) / 2))
    scale = min(1200 / ((e - w) * cosine), 760 / (n - s))
    x0 = (1200 - (e - w) * cosine * scale) / 2
    y0 = (760 - (n - s) * scale) / 2
    for marker_id, item in [("hero-marker", data["hero"])] + [
        (f"scene-marker-{i}", scene) for i, scene in enumerate(scenes, 1)
    ]:
        coords = item["coordinates"]
        lon, lat = coords["longitude"], coords["latitude"]
        expected_x, expected_y = x0 + (lon - w) * cosine * scale, y0 + (n - lat) * scale
        node = svg.find(f".//*[@id='{marker_id}']")
        if node is None:
            die(f"Missing georeferenced map point: {marker_id}")
        assert abs(float(node.get("data-x", "NaN")) - expected_x) < 0.02, marker_id
        assert abs(float(node.get("data-y", "NaN")) - expected_y) < 0.02, marker_id
        assert abs(float(node.get("data-latitude", "NaN")) - lat) < 1e-6
        assert abs(float(node.get("data-longitude", "NaN")) - lon) < 1e-6
    inset = svg.find(".//*[@id='new-caledonia-overview-inset']")
    assert inset is not None
    assert len(svg.findall(".//*[@id='remote-island-location-points']/*")) == 8

    # Guard against the inset covering any real islands (regression 2026-11-07).
    transform = re.fullmatch(
        r"translate\((-?[\d.]+) (-?[\d.]+)\) scale\(([\d.]+)\)",
        inset.get("transform", ""),
    )
    assert transform is not None, "Unexpected overview inset transform"
    tx, ty, factor = (float(v) for v in transform.groups())
    frame = next((child for child in inset if child.tag.endswith("}rect")), None)
    assert frame is not None
    assert frame.get("fill") == "none", "Overview inset must not have an opaque/white background"
    pad = 20  # SVG pixels; keep visible sea between inset and island coastline.
    left = tx + factor * float(frame.get("x")) - pad
    top = ty + factor * float(frame.get("y")) - pad
    right = tx + factor * (float(frame.get("x")) + float(frame.get("width"))) + pad
    bottom = ty + factor * (float(frame.get("y")) + float(frame.get("height"))) + pad
    assert 0 <= left < right <= 1200 and 0 <= top < bottom <= 760
    land = svg.find(".//*[@id='new-caledonia-land']")
    assert land is not None
    shore_vertices = [
        (float(x), float(y))
        for x, y in re.findall(r"[ML](-?[\d.]+),(-?[\d.]+)", land.get("d", ""))
    ]
    assert len(shore_vertices) > 100, "Map coastline has too few points"
    assert not any(
        left <= x <= right and top <= y <= bottom for x, y in shore_vertices
    ), "Overview inset overlaps real coastline"
    # Hero Kanumera and S01 Upi Bay are only 17 canvas pixels apart in reality.
    # Their independent display markers must be visible even on narrow screens;
    # the geographic anchors remain unchanged and callout lines identify them.
    labels = []
    for marker_id, item, line_id in (
        ("hero-marker", data["hero"], "hero-callout-line"),
        ("scene-marker-1", scenes[0], "scene-1-callout-line"),
    ):
        node = svg.find(f".//*[@id='{marker_id}']")
        line = svg.find(f".//*[@id='{line_id}']")
        assert node is not None and line is not None, marker_id
        offset = item.get("mapOffset")
        assert isinstance(offset, dict), f"{marker_id} needs label-only mapOffset"
        dx, dy = offset["x"], offset["y"]
        assert math.hypot(12 * dx, 7.6 * dy) <= 60, marker_id
        x, y = float(node.get("data-x")), float(node.get("data-y"))
        lx, ly = x + 12 * dx, y + 7.6 * dy
        assert abs(float(node.get("data-label-x", "NaN")) - lx) < .02
        assert abs(float(node.get("data-label-y", "NaN")) - ly) < .02
        assert 0 < lx < 1200 and 0 < ly < 760
        labels.append((lx, ly))
    # 110/1200 of map width is >32px on a 350px mobile map.
    assert math.dist(*labels) > 110, "Hero/S01 labels overlap on small screens"
    print("PASS: Hero and S01 separated with two georeferenced callouts")
    print("PASS: all 9 geographic anchors, island-free overview inset, and margins")

    # Test the actual shared Region builder; this intentionally demands assets.
    import importlib.util
    import sys

    builder_path = ROOT / "scripts/build_region_pages.py"
    spec = importlib.util.spec_from_file_location("build_region_pages", builder_path)
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = builder
    spec.loader.exec_module(builder)
    page, canonical, published = builder.render_region(
        data, site_url="https://atlas.yagenji.com/", version="new-caledonia-publication-qa"
    )
    assert published
    assert 'name="robots" content="index,follow"' in page
    assert canonical.endswith("/countries/france/new-caledonia/")
    assert "NEW CALEDONIA" in page and "ニューカレドニア" in page
    assert "src=" in page
    print("PASS: shared Region renderer, index, correct canonical URL")
    print("All focused checks passed. Region is published.")


if __name__ == "__main__":
    main()
