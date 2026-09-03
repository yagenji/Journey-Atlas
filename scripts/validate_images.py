#!/usr/bin/env python3
"""Two-stage image QA for published Country renewal.

AUDIT scans every published Country Page and reports legacy issues without
blocking unrelated renewal work.

HARD scans only countries explicitly marked `hardImageGate: true` in
`data/country-renewal-status.json`. Any issue in those renewed countries
fails CI.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
RENEWAL_STATUS = ROOT / "data" / "country-renewal-status.json"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SCENE_MIN = (1200, 800)
TASTE_MIN = (1200, 800)
HERO_MIN = (1200, 760)
RATIO_3_2 = 1.5
RATIO_TOLERANCE = 0.015


def published_slugs() -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for path in REGISTRY_PATHS:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("destinations", []):
            slug = item.get("slug")
            if item.get("atlasPublished") and slug and slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def hard_gate_slugs() -> list[str]:
    status = json.loads(RENEWAL_STATUS.read_text(encoding="utf-8"))
    return [
        row["slug"]
        for row in status.get("countries", [])
        if row.get("published") and row.get("hardImageGate")
    ]


def add_ref(refs: dict[str, set[str]], owner: str, value: object) -> None:
    if isinstance(value, str) and value.startswith("assets/images/"):
        refs.setdefault(value, set()).add(owner)


def country_refs(slug: str, data: dict) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    add_ref(refs, f"{slug}:hero", data.get("hero", {}).get("image"))
    add_ref(refs, f"{slug}:map", data.get("map", {}).get("svg"))
    for index, scene in enumerate(data.get("scenes", []), 1):
        if isinstance(scene, dict):
            add_ref(refs, f"{slug}:scene:{index}", scene.get("image"))
    taste = data.get("taste", {})
    if isinstance(taste, dict):
        for index, item in enumerate(taste.get("items", []), 1):
            if isinstance(item, dict):
                add_ref(refs, f"{slug}:taste:{index}", item.get("image"))
    for index, item in enumerate(data.get("photoCredits", []), 1):
        if isinstance(item, dict):
            add_ref(refs, f"{slug}:photoCredit:{index}", item.get("image"))
    return refs


def verify_raster(path: Path) -> tuple[int, int, str]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            fmt = image.format or path.suffix.lstrip(".").upper()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"decode failed: {exc}") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid dimensions: {width}x{height}")
    return width, height, fmt


def verify_embedded_svg_raster(path: Path) -> tuple[int, int, str] | None:
    try:
        root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"SVG parse failed: {exc}") from exc

    hrefs: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "image":
            continue
        href = element.attrib.get("href") or element.attrib.get("{http://www.w3.org/1999/xlink}href")
        if isinstance(href, str):
            hrefs.append(href)

    data_href = next(
        (href for href in hrefs if href.startswith("data:image/") and ";base64," in href),
        None,
    )
    if not data_href:
        return None

    header, encoded = data_href.split(",", 1)
    mime_match = re.match(r"data:image/([^;]+);base64$", header)
    mime = mime_match.group(1) if mime_match else "embedded"
    try:
        payload = base64.b64decode(encoded, validate=True)
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            width, height = image.size
            fmt = image.format or mime.upper()
    except Exception as exc:
        raise ValueError(f"embedded {mime} decode failed: {exc}") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"embedded raster has invalid dimensions: {width}x{height}")
    return width, height, fmt


def validate_dimensions(errors: list[str], asset: str, owners: set[str], width: int, height: int) -> None:
    ratio = width / height
    for owner in owners:
        if ":scene:" in owner:
            if width < SCENE_MIN[0] or height < SCENE_MIN[1]:
                errors.append(f"{owner}: scene image too small: {asset} ({width}x{height})")
            if not math.isclose(ratio, RATIO_3_2, abs_tol=RATIO_TOLERANCE):
                errors.append(f"{owner}: scene image is not 3:2: {asset} ({width}x{height})")
        elif ":taste:" in owner:
            if width < TASTE_MIN[0] or height < TASTE_MIN[1]:
                errors.append(f"{owner}: taste image too small: {asset} ({width}x{height})")
            if not math.isclose(ratio, RATIO_3_2, abs_tol=RATIO_TOLERANCE):
                errors.append(f"{owner}: taste image is not 3:2: {asset} ({width}x{height})")
        elif owner.endswith(":hero"):
            if width < HERO_MIN[0] or height < HERO_MIN[1] or width <= height:
                errors.append(
                    f"{owner}: hero image is not a sufficiently large landscape image: "
                    f"{asset} ({width}x{height})"
                )


def validate_map_svg(errors: list[str], owner: str, asset: str) -> None:
    path = ROOT / asset
    if not path.exists():
        errors.append(f"{owner}: map asset missing: {asset}")
        return
    try:
        root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{owner}: map SVG parse failed: {asset}: {exc}")
        return

    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    if len(view_box) != 4:
        errors.append(f"{owner}: map SVG viewBox missing/invalid: {asset}")
        return
    try:
        _x, _y, width, height = (float(value) for value in view_box)
    except ValueError:
        errors.append(f"{owner}: map SVG viewBox is non-numeric: {asset}")
        return
    if not math.isclose(width, 1200.0, abs_tol=0.01) or not math.isclose(height, 760.0, abs_tol=0.01):
        errors.append(f"{owner}: map SVG canvas must be 1200x760: {asset} ({width:g}x{height:g})")


def approved_folder_hygiene(errors: list[str], slug: str, referenced: set[str]) -> None:
    approved_dirs = {
        (ROOT / asset).parent
        for asset in referenced
        if Path(asset).parent.name == "approved"
    }
    for approved in sorted(approved_dirs):
        if not approved.exists():
            continue
        for path in sorted(approved.iterdir()):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative not in referenced:
                errors.append(f"{slug}: unreferenced file remains in approved folder: {relative}")


def scan(slugs: list[str]) -> tuple[list[str], int]:
    all_refs: dict[str, set[str]] = {}
    per_country: dict[str, set[str]] = {}
    errors: list[str] = []
    decoded = 0

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"{slug}: Country JSON missing")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        refs = country_refs(slug, data)
        per_country[slug] = set(refs)
        for asset, owners in refs.items():
            all_refs.setdefault(asset, set()).update(owners)

    for asset, owners in sorted(all_refs.items()):
        path = ROOT / asset
        if not path.exists():
            errors.append(f"{', '.join(sorted(owners))}: referenced asset missing: {asset}")
            continue
        suffix = path.suffix.lower()
        if suffix in RASTER_SUFFIXES:
            try:
                width, height, _fmt = verify_raster(path)
            except ValueError as exc:
                errors.append(f"{asset}: {exc}")
                continue
            validate_dimensions(errors, asset, owners, width, height)
            decoded += 1
        elif suffix == ".svg":
            if any(owner.endswith(":map") for owner in owners):
                for owner in sorted(owner for owner in owners if owner.endswith(":map")):
                    validate_map_svg(errors, owner, asset)
            try:
                embedded = verify_embedded_svg_raster(path)
            except ValueError as exc:
                errors.append(f"{asset}: {exc}")
                continue
            if embedded:
                decoded += 1

    for slug in slugs:
        approved_folder_hygiene(errors, slug, per_country.get(slug, set()))

    return errors, decoded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "hard"), default="audit")
    args = parser.parse_args()

    slugs = published_slugs() if args.mode == "audit" else hard_gate_slugs()
    if not slugs:
        print(f"Image QA ({args.mode}): no target countries.")
        return 0

    errors, decoded = scan(slugs)

    if errors:
        label = "AUDIT FINDINGS" if args.mode == "audit" else "HARD-GATE FAILURES"
        stream = sys.stdout if args.mode == "audit" else sys.stderr
        print(f"Image QA {label}:", file=stream)
        for error in errors:
            print(f"- {error}", file=stream)
        if args.mode == "audit":
            print(
                f"Audit completed: {len(slugs)} published country page(s), "
                f"{decoded} raster payload(s) fully decoded, {len(errors)} finding(s)."
            )
            return 0
        return 1

    print(
        f"Image QA passed ({args.mode}): {len(slugs)} country page(s), "
        f"{decoded} raster payload(s) fully decoded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
