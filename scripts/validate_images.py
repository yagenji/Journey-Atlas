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
import hashlib
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

DUPLICATE_THUMB_SIZE = (32, 32)
DUPLICATE_HASH_SIZE = 8
NEAR_DUPLICATE_DHASH_MAX = 2
NEAR_DUPLICATE_AHASH_MAX = 2
NEAR_DUPLICATE_RMS_MAX = 12.0


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


def _resample_lanczos():
    resampling = getattr(Image, "Resampling", Image)
    return resampling.LANCZOS


def _bit_hash(values: list[int], threshold: float) -> tuple[bool, ...]:
    return tuple(value >= threshold for value in values)


def _hamming(left: tuple[bool, ...], right: tuple[bool, ...]) -> int:
    return sum(a != b for a, b in zip(left, right))


def visual_fingerprint(path: Path) -> dict[str, object]:
    """Return a conservative fingerprint for exact/near-duplicate detection."""
    try:
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            thumb = rgb.resize(DUPLICATE_THUMB_SIZE, _resample_lanczos())
            gray = thumb.convert("L")

            gray_values = list(gray.getdata())
            average = sum(gray_values) / len(gray_values)
            ahash = _bit_hash(gray_values, average)

            dhash_image = gray.resize(
                (DUPLICATE_HASH_SIZE + 1, DUPLICATE_HASH_SIZE),
                _resample_lanczos(),
            )
            dhash_values = list(dhash_image.getdata())
            dhash_bits: list[bool] = []
            row_width = DUPLICATE_HASH_SIZE + 1
            for y in range(DUPLICATE_HASH_SIZE):
                row = dhash_values[y * row_width : (y + 1) * row_width]
                dhash_bits.extend(row[x] > row[x + 1] for x in range(DUPLICATE_HASH_SIZE))

            payload = thumb.tobytes()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"duplicate fingerprint decode failed: {exc}") from exc

    return {
        "digest": hashlib.sha256(payload).hexdigest(),
        "ahash": ahash,
        "dhash": tuple(dhash_bits),
        "thumb": payload,
    }


def _thumbnail_rms(left: bytes, right: bytes) -> float:
    if len(left) != len(right) or not left:
        return float("inf")
    squared = sum((a - b) ** 2 for a, b in zip(left, right))
    return math.sqrt(squared / len(left))


def validate_duplicate_group(
    errors: list[str],
    slug: str,
    label: str,
    members: list[tuple[str, str]],
) -> int:
    fingerprints: dict[str, dict[str, object]] = {}
    compared = 0

    for owner, asset in members:
        path = ROOT / asset
        if not path.exists() or path.suffix.lower() not in RASTER_SUFFIXES:
            continue
        try:
            fingerprints[owner] = visual_fingerprint(path)
        except ValueError as exc:
            errors.append(f"{slug}:{owner}: {exc}")
            continue

    active = [(owner, asset) for owner, asset in members if owner in fingerprints]
    for index, (left_owner, left_asset) in enumerate(active):
        left = fingerprints[left_owner]
        for right_owner, right_asset in active[index + 1 :]:
            right = fingerprints[right_owner]
            compared += 1

            if left_asset == right_asset:
                errors.append(
                    f"{slug}:{label}: duplicate asset path reused by {left_owner} and {right_owner}: {left_asset}"
                )
                continue

            if left["digest"] == right["digest"]:
                errors.append(
                    f"{slug}:{label}: visually identical normalized image used by "
                    f"{left_owner} and {right_owner}: {left_asset} / {right_asset}"
                )
                continue

            dhash_distance = _hamming(left["dhash"], right["dhash"])
            ahash_distance = _hamming(left["ahash"], right["ahash"])
            rms = _thumbnail_rms(left["thumb"], right["thumb"])

            if (
                dhash_distance <= NEAR_DUPLICATE_DHASH_MAX
                and ahash_distance <= NEAR_DUPLICATE_AHASH_MAX
                and rms <= NEAR_DUPLICATE_RMS_MAX
            ):
                errors.append(
                    f"{slug}:{label}: near-duplicate images detected between "
                    f"{left_owner} and {right_owner} "
                    f"(dHash={dhash_distance}, aHash={ahash_distance}, RMS={rms:.2f}): "
                    f"{left_asset} / {right_asset}"
                )

    return compared


def scan_duplicates(slugs: list[str]) -> tuple[list[str], int]:
    """Check Hero+Scenes and Taste groups for duplicate/near-duplicate imagery."""
    errors: list[str] = []
    compared = 0

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"{slug}: Country JSON missing for duplicate scan")
            continue

        data = json.loads(path.read_text(encoding="utf-8"))

        scene_members: list[tuple[str, str]] = []
        hero_asset = data.get("hero", {}).get("image")
        if isinstance(hero_asset, str):
            scene_members.append(("hero", hero_asset))
        for index, scene in enumerate(data.get("scenes", []), 1):
            asset = scene.get("image") if isinstance(scene, dict) else None
            if isinstance(asset, str):
                scene_members.append((f"scene:{index}", asset))

        taste_members: list[tuple[str, str]] = []
        taste = data.get("taste", {})
        if isinstance(taste, dict):
            for index, item in enumerate(taste.get("items", []), 1):
                asset = item.get("image") if isinstance(item, dict) else None
                if isinstance(asset, str):
                    taste_members.append((f"taste:{index}", asset))

        compared += validate_duplicate_group(errors, slug, "hero-scenes", scene_members)
        compared += validate_duplicate_group(errors, slug, "taste", taste_members)

    return errors, compared


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


def production_asset_hygiene(errors: list[str], slug: str, referenced: set[str]) -> None:
    """Ensure renewed production folders contain only currently referenced final assets."""
    roots: set[Path] = set()
    for asset in referenced:
        parts = Path(asset).parts
        if len(parts) >= 3 and parts[:2] == ("assets", "images"):
            roots.add(ROOT.joinpath(*parts[:3]))

        path = Path(asset)
        if path.suffix.lower() in RASTER_SUFFIXES and "approved" not in path.parts:
            errors.append(f"{slug}: production raster must live in approved/: {asset}")

    for root in sorted(roots):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative not in referenced:
                errors.append(f"{slug}: unreferenced file remains in production asset folder: {relative}")


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
                width, height, _fmt = embedded
                validate_dimensions(errors, asset, owners, width, height)
                decoded += 1

    for slug in slugs:
        production_asset_hygiene(errors, slug, per_country.get(slug, set()))

    return errors, decoded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "hard"), default="audit")
    parser.add_argument("--duplicates-only", action="store_true")
    parser.add_argument("--slug", action="append", default=[])
    args = parser.parse_args()

    if args.duplicates_only:
        if not args.slug:
            parser.error("--duplicates-only requires at least one --slug")
        slugs = list(dict.fromkeys(args.slug))
        errors, compared = scan_duplicates(slugs)
        if errors:
            print("Image QA DUPLICATE-GATE FAILURES:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(
            f"Image duplicate QA passed: {len(slugs)} country page(s), "
            f"{compared} pair(s) compared."
        )
        return 0

    if args.slug:
        slugs = list(dict.fromkeys(args.slug))
    else:
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
