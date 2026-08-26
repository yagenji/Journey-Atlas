#!/usr/bin/env python3
"""Production-candidate QA for Sweden while atlasPublished remains false."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY = ROOT / "data/countries/sweden.json"
REGISTRY = ROOT / "data/atlas-destinations.json"
EXPECTED_SCENES = {
    "gamla-stan", "lapporten", "high-coast", "siljan",
    "visby", "langhammars", "smogen", "gota-canal",
}
MAP_PALETTE = {"#eef2ef", "#e4eceb", "#dce7e7", "#e2dbad", "#d4cc9b", "#c8bf8a"}
MAP_LABELS = {"Stockholm", "Gamla Stan", "Lapporten", "Höga Kusten", "Siljan", "Visby", "Fårö", "Smögen", "Göta Canal"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def check_webp(relative: str) -> None:
    path = ROOT / relative
    require(path.exists(), f"Missing WebP: {relative}")
    data = path.read_bytes()
    require(len(data) >= 12, f"WebP too small: {relative}")
    require(data[:4] == b"RIFF" and data[8:12] == b"WEBP", f"Invalid WebP: {relative}")


def check_svg(relative: str) -> None:
    path = ROOT / relative
    require(path.exists(), f"Missing SVG: {relative}")
    text = path.read_text(encoding="utf-8")
    require('viewBox="0 0 1200 800"' in text, f"Scene canvas must be 1200x800: {relative}")
    require('role="img"' in text and "aria-label=" in text, f"Accessibility metadata missing: {relative}")
    require("feTurbulence" in text, f"Watercolor/paper texture missing: {relative}")


def check_map(relative: str) -> None:
    path = ROOT / relative
    require(path.exists(), f"Missing map: {relative}")
    text = path.read_text(encoding="utf-8")
    require('viewBox="0 0 1200 760"' in text, "Sweden map must use 1200x760 master canvas")
    require('aria-label="Map of Sweden"' in text, "Sweden map aria-label missing")
    for color in MAP_PALETTE:
        require(color in text, f"Sweden map palette mismatch: {color}")
    for label in MAP_LABELS:
        require(label in text, f"Sweden map label missing: {label}")
    for reference in ("assets/images/iceland/map-atlas-v2.svg", "assets/images/norway/map-atlas-v1.svg"):
        ref = (ROOT / reference).read_text(encoding="utf-8")
        require('viewBox="0 0 1200 760"' in ref, f"Reference map canvas changed: {reference}")
        for color in MAP_PALETTE:
            require(color in ref, f"Reference map palette changed: {reference} / {color}")


def main() -> int:
    data = json.loads(COUNTRY.read_text(encoding="utf-8"))
    require(data.get("slug") == "sweden", "Wrong country slug")
    scenes = data.get("scenes") or []
    require(len(scenes) == 8, f"Expected 8 scenes, found {len(scenes)}")
    require({scene.get("id") for scene in scenes} == EXPECTED_SCENES, "Unexpected Sweden scene set")

    artworks = [data["hero"]["image"], *[scene["image"] for scene in scenes]]
    require(len(set(artworks)) == 9, "Hero and 8 scene artwork paths must be unique")
    for artwork in artworks:
        require(artwork.startswith("assets/images/sweden/v3/"), f"Non-v3 artwork referenced: {artwork}")
        if artwork.endswith(".webp"):
            check_webp(artwork)
        elif artwork.endswith(".svg"):
            check_svg(artwork)
        else:
            raise AssertionError(f"Production artwork must be WebP or SVG: {artwork}")

    check_map(data["map"]["svg"])

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sweden = next((item for item in registry["destinations"] if item.get("slug") == "sweden"), None)
    require(sweden is not None, "Sweden missing from registry")
    require(sweden.get("atlasPublished") is False, "Sweden must remain unpublished before review")
    require(sweden.get("href") == "", "Unpublished Sweden must not have a public href")

    serialized = json.dumps(data, ensure_ascii=False)
    require("assets/images/sweden/v1/" not in serialized, "v1 artwork leaked into sweden.json")
    require("assets/images/sweden/v2/" not in serialized, "v2 artwork leaked into sweden.json")
    require(".b64" not in serialized and ".parts.json" not in serialized, "Encoded source leaked into production references")

    print("Sweden production QA passed: Hero + 8 scenes, detailed master map, v3-only production refs, unpublished state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
