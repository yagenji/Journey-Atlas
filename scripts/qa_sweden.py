#!/usr/bin/env python3
"""Branch QA for the Sweden v3 build without publishing Sweden."""

from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_PATH = ROOT / "data/countries/sweden.json"
REGISTRY_PATH = ROOT / "data/atlas-destinations.json"

EXPECTED_SCENES = {
    "gamla-stan",
    "lapporten",
    "high-coast",
    "siljan",
    "visby",
    "langhammars",
    "smogen",
    "gota-canal",
}
MAP_PALETTE = {
    "#eef2ef",
    "#e4eceb",
    "#dce7e7",
    "#e2dbad",
    "#d4cc9b",
    "#c8bf8a",
}
BASE64_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def decode_manifest(relative_path: str) -> None:
    manifest_path = ROOT / relative_path
    require(manifest_path.exists(), f"Missing manifest: {relative_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = manifest.get("parts") or []
    require(parts, f"Manifest has no parts: {relative_path}")

    chunks = []
    invalid_by_part: list[str] = []
    for part in parts:
        raw = (ROOT / part).read_text(encoding="utf-8").strip().lstrip("\ufeff")
        invalid = sorted({ch for ch in raw if not ch.isspace() and ch not in BASE64_CHARS})
        if invalid:
            invalid_by_part.append(f"{part}: {invalid!r}")
        chunks.append(raw)
    require(not invalid_by_part, f"Non-base64 characters in {relative_path}: {'; '.join(invalid_by_part)}")

    encoded = "".join("".join(chunks).split())
    signature = manifest.get("signature")
    if signature:
        require(encoded.startswith(signature), f"Signature mismatch: {relative_path}")

    try:
        binary = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise AssertionError(
            f"Invalid base64 in {relative_path}: {exc}; normalized length={len(encoded)}, mod4={len(encoded) % 4}"
        ) from exc

    if manifest.get("mime") == "image/webp":
        require(len(binary) >= 12, f"Decoded WebP too small: {relative_path}")
        require(binary[:4] == b"RIFF" and binary[8:12] == b"WEBP", f"Invalid WebP: {relative_path}")


def check_scene_svg(relative_path: str) -> None:
    svg_path = ROOT / relative_path
    require(svg_path.exists(), f"Missing scene artwork: {relative_path}")
    svg = svg_path.read_text(encoding="utf-8")
    require('viewBox="0 0 1200 800"' in svg, f"Scene artwork must be 1200x800: {relative_path}")
    require('role="img"' in svg and "aria-label=" in svg, f"Scene artwork accessibility metadata missing: {relative_path}")
    require("feTurbulence" in svg, f"Watercolor/paper texture filter missing: {relative_path}")


def check_map(relative_path: str) -> None:
    map_path = ROOT / relative_path
    require(map_path.exists(), f"Missing Sweden map: {relative_path}")
    svg = map_path.read_text(encoding="utf-8")
    require('viewBox="0 0 1200 760"' in svg, "Sweden map must use the 1200x760 master canvas")
    require('aria-label="Map of Sweden"' in svg, "Sweden map aria-label missing")
    for color in MAP_PALETTE:
        require(color in svg, f"Sweden map palette mismatch; missing {color}")

    for reference in ("assets/images/iceland/map-atlas-v2.svg", "assets/images/norway/map-atlas-v1.svg"):
        reference_svg = (ROOT / reference).read_text(encoding="utf-8")
        for color in MAP_PALETTE:
            require(color in reference_svg, f"Reference map palette unexpectedly changed: {reference}")


def main() -> int:
    data = json.loads(COUNTRY_PATH.read_text(encoding="utf-8"))
    require(data.get("slug") == "sweden", "Wrong country slug")

    scenes = data.get("scenes") or []
    require(len(scenes) == 8, f"Expected 8 Sweden scenes, found {len(scenes)}")
    require({scene.get("id") for scene in scenes} == EXPECTED_SCENES, "Sweden scene set changed unexpectedly")

    hero_image = data.get("hero", {}).get("image", "")
    require(hero_image.startswith("assets/images/sweden/v3/"), "Sweden Hero is not using v3 artwork")

    artwork_paths = [hero_image]
    for scene in scenes:
        image = scene.get("image", "")
        require(image.startswith("assets/images/sweden/v3/"), f"Legacy Sweden scene artwork referenced: {scene.get('id')}")
        artwork_paths.append(image)

    require(len(set(artwork_paths)) == 9, "Hero and scene artwork paths must be unique")

    for artwork in artwork_paths:
        if artwork.endswith(".parts.json"):
            decode_manifest(artwork)
        elif artwork.endswith(".svg"):
            check_scene_svg(artwork)
        else:
            raise AssertionError(f"Unsupported Sweden v3 artwork format: {artwork}")

    check_map(data.get("map", {}).get("svg", ""))

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sweden = next((item for item in registry.get("destinations", []) if item.get("slug") == "sweden"), None)
    require(sweden is not None, "Sweden missing from atlas registry")
    require(sweden.get("atlasPublished") is False, "Sweden must remain unpublished during v3 review")
    require(sweden.get("href") == "", "Unpublished Sweden must not expose a public href")

    serialized = json.dumps(data, ensure_ascii=False)
    require("assets/images/sweden/v1/" not in serialized, "v1 Sweden artwork leaked into sweden.json")
    require("assets/images/sweden/v2/" not in serialized, "v2 Sweden artwork leaked into sweden.json")

    print("Sweden v3 QA passed: 1 Hero + 8 scenes, master map styling, valid encoded WebP, no legacy references, unpublished registry state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
