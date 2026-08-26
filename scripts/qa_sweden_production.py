#!/usr/bin/env python3
"""Production-candidate QA for Sweden while atlasPublished remains false."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
COUNTRY = ROOT / "data/countries/sweden.json"
REGISTRY = ROOT / "data/atlas-destinations.json"
CREDITS = ROOT / "data/sweden-v5-image-credits.json"
EXPECTED_SCENES = {
    "gamla-stan", "lapporten", "high-coast", "siljan",
    "visby", "langhammars", "smogen", "gota-canal",
}
MAP_PALETTE = {"#eef2ef", "#e4eceb", "#dce7e7", "#e2dbad", "#d4cc9b", "#c8bf8a"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def check_webp(relative: str) -> None:
    path = ROOT / relative
    require(path.exists(), f"Missing WebP: {relative}")
    raw = path.read_bytes()
    require(len(raw) >= 12, f"WebP too small: {relative}")
    require(raw[:4] == b"RIFF" and raw[8:12] == b"WEBP", f"Invalid WebP signature: {relative}")
    declared_size = int.from_bytes(raw[4:8], "little") + 8
    require(declared_size == len(raw), f"Truncated WebP: {relative}; declared={declared_size}, actual={len(raw)}")
    try:
        with Image.open(path) as image:
            image.load()
            require(image.format == "WEBP", f"Unexpected image format: {relative} / {image.format}")
            require(image.size == (1200, 800), f"Wrong Sweden artwork size: {relative} / {image.size}")
    except Exception as exc:
        raise AssertionError(f"WebP decode failed: {relative}: {exc}") from exc


def check_map(relative: str) -> None:
    path = ROOT / relative
    require(path.exists(), f"Missing map: {relative}")
    text = path.read_text(encoding="utf-8")
    require('viewBox="0 0 1200 760"' in text, "Sweden map must use 1200x760 master canvas")
    require('aria-label="Map of Sweden"' in text, "Sweden map aria-label missing")
    for color in MAP_PALETTE:
        require(color in text, f"Sweden map palette mismatch: {color}")
    for reference in ("assets/images/iceland/map-atlas-v2.svg", "assets/images/norway/map-atlas-v1.svg"):
        ref = (ROOT / reference).read_text(encoding="utf-8")
        require('viewBox="0 0 1200 760"' in ref, f"Reference map canvas changed: {reference}")
        for color in MAP_PALETTE:
            require(color in ref, f"Reference map palette changed: {reference} / {color}")


def check_scene_credits(scene_artworks: list[str]) -> None:
    require(CREDITS.exists(), "Sweden v5 image credit metadata missing")
    credits = json.loads(CREDITS.read_text(encoding="utf-8"))
    items = credits.get("assets") or []
    require(len(items) == 8, f"Expected 8 Sweden v5 scene credit records, found {len(items)}")
    credited = {item.get("output") for item in items}
    require(set(scene_artworks) == credited, "Sweden v5 scene references and credit metadata do not match")
    for item in items:
        require(item.get("sourcePage"), f"Missing source page in credits: {item.get('key')}")
        require(item.get("author"), f"Missing author in credits: {item.get('key')}")
        require(item.get("license"), f"Missing license in credits: {item.get('key')}")
        require("watercolor" in str(item.get("treatment", "")).lower(), f"Treatment metadata missing: {item.get('key')}")


def main() -> int:
    data = json.loads(COUNTRY.read_text(encoding="utf-8"))
    require(data.get("slug") == "sweden", "Wrong country slug")
    scenes = data.get("scenes") or []
    require(len(scenes) == 8, f"Expected 8 scenes, found {len(scenes)}")
    require({scene.get("id") for scene in scenes} == EXPECTED_SCENES, "Unexpected Sweden scene set")

    for scene in scenes:
        coords = scene.get("coordinates") or {}
        require(scene.get("mapLabel"), f"Missing dynamic map label: {scene.get('id')}")
        require(isinstance(coords.get("latitude"), (int, float)), f"Missing map latitude: {scene.get('id')}")
        require(isinstance(coords.get("longitude"), (int, float)), f"Missing map longitude: {scene.get('id')}")

    capital = data.get("capital") or {}
    hero = data.get("hero") or {}
    require(capital.get("nameEn") and capital.get("coordinates"), "Capital map marker data missing")
    require(hero.get("coordinates") and hero.get("location"), "Hero map marker data missing")

    hero_artwork = hero["image"]
    scene_artworks = [scene["image"] for scene in scenes]
    artworks = [hero_artwork, *scene_artworks]
    require(len(set(artworks)) == 9, "Hero and 8 scene artwork paths must be unique")
    require(hero_artwork == "assets/images/sweden/v5/hero-grinda.webp", "Approved Grinda Hero is not connected")
    for artwork in artworks:
        require(artwork.startswith("assets/images/sweden/v5/"), f"Non-v5 production artwork referenced: {artwork}")
        require(artwork.endswith(".webp"), f"Sweden v5 production artwork must be WebP: {artwork}")
        check_webp(artwork)

    check_scene_credits(scene_artworks)
    check_map(data["map"]["svg"])

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sweden = next((item for item in registry["destinations"] if item.get("slug") == "sweden"), None)
    require(sweden is not None, "Sweden missing from registry")
    require(sweden.get("atlasPublished") is False, "Sweden must remain unpublished before review")
    require(sweden.get("href") == "", "Unpublished Sweden must not have a public href")

    serialized = json.dumps(data, ensure_ascii=False)
    for old in ("/v1/", "/v2/", "/v3/", "/v4/"):
        require(f"assets/images/sweden{old}" not in serialized, f"Old Sweden artwork leaked into production JSON: {old}")
    require(".b64" not in serialized and ".parts.json" not in serialized, "Encoded source leaked into production references")

    print("Sweden production QA passed: approved Hero + 8 v5 WebP scenes decode at 1200x800, 1200x760 master map, credits, unpublished state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
