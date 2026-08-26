#!/usr/bin/env python3
"""Build Sweden v4 production scenery from license-compatible Wikimedia Commons photos.

The source photographs are selected by place-specific queries, transformed only lightly
to match JOURNEY ATLAS's watercolor-adjacent visual language, and stored locally as
self-hosted WebP files. Source/author/license metadata is written alongside the build.
"""

from __future__ import annotations

import html
import json
import math
import random
import re
import sys
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets/images/sweden/v4"
COUNTRY_PATH = ROOT / "data/countries/sweden.json"
CREDITS_PATH = ROOT / "data/sweden-image-credits.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "JourneyAtlas/1.0 (https://github.com/yagenji/Journey-Atlas)"

TARGET_W = 1200
TARGET_H = 800
MIN_SOURCE_W = 1200
MIN_SOURCE_H = 700

ASSETS = [
    {
        "key": "hero",
        "query": 'Grinda Stockholm archipelago Sweden',
        "preferred": ["grinda", "stockholm", "archipelago"],
        "output": "hero-grinda.webp",
    },
    {
        "key": "gamla-stan",
        "query": '"Gamla Stan" Stockholm waterfront',
        "preferred": ["gamla", "stan", "stockholm"],
        "output": "gamla-stan.webp",
    },
    {
        "key": "lapporten",
        "query": 'Lapporten Abisko Sweden landscape',
        "preferred": ["lapporten", "abisko"],
        "output": "lapporten.webp",
    },
    {
        "key": "high-coast",
        "query": '"Höga Kusten" Sweden landscape',
        "preferred": ["höga", "kusten", "high coast"],
        "output": "high-coast.webp",
    },
    {
        "key": "siljan",
        "query": 'Siljan Dalarna Sweden lake',
        "preferred": ["siljan", "dalarna"],
        "output": "siljan-dalarna.webp",
    },
    {
        "key": "visby",
        "query": 'Visby city wall Gotland Sweden',
        "preferred": ["visby", "gotland", "wall"],
        "output": "visby.webp",
    },
    {
        "key": "langhammars",
        "query": 'Langhammars Fårö rauk Sweden',
        "preferred": ["langhammars", "fårö", "faro", "rauk"],
        "output": "langhammars-faro.webp",
    },
    {
        "key": "smogen",
        "query": 'Smögen',
        "preferred": ["smögen", "smogen", "harbor", "boathouse"],
        "output": "smogen.webp",
    },
    {
        "key": "gota-canal",
        "query": 'Göta kanal Sweden',
        "preferred": ["göta", "gota", "canal"],
        "output": "gota-canal.webp",
    },
]

ALLOWED_LICENSE_TOKENS = (
    "cc by",
    "cc-by",
    "cc by-sa",
    "cc-by-sa",
    "cc0",
    "public domain",
    "pd-",
)


def api_get(params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{COMMONS_API}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return " ".join(text.split())


def metadata_value(meta: dict[str, Any], key: str) -> str:
    value = meta.get(key, {})
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


def license_allowed(meta: dict[str, Any]) -> bool:
    short = metadata_value(meta, "LicenseShortName").lower()
    terms = metadata_value(meta, "UsageTerms").lower()
    combined = f"{short} {terms}"
    return any(token in combined for token in ALLOWED_LICENSE_TOKENS)


def search_candidates(asset: dict[str, Any]) -> list[dict[str, Any]]:
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrsearch": asset["query"],
            "gsrlimit": 20,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1800,
            "redirects": 1,
        }
    )
    pages = list((data.get("query", {}).get("pages", {}) or {}).values())
    candidates: list[dict[str, Any]] = []
    for rank, page in enumerate(pages):
        info_list = page.get("imageinfo") or []
        if not info_list:
            continue
        info = info_list[0]
        meta = info.get("extmetadata") or {}
        mime = str(info.get("mime") or "")
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        if width < MIN_SOURCE_W or height < MIN_SOURCE_H:
            continue
        if not license_allowed(meta):
            continue

        title = str(page.get("title") or "")
        title_lower = title.lower()
        preferred_hits = sum(1 for token in asset["preferred"] if token.lower() in title_lower)
        aspect = width / max(1, height)
        landscape_bonus = 2.0 if 1.2 <= aspect <= 2.2 else (0.5 if aspect > 1.0 else -1.0)
        resolution_bonus = min(3.0, math.log2(max(1, width * height) / 1_000_000 + 1))
        score = preferred_hits * 3.0 + landscape_bonus + resolution_bonus - rank * 0.08

        candidates.append(
            {
                "score": score,
                "rank": rank,
                "title": title,
                "width": width,
                "height": height,
                "url": info.get("thumburl") or info.get("url"),
                "originalUrl": info.get("url"),
                "descriptionUrl": info.get("descriptionurl"),
                "meta": meta,
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def center_crop_3x2(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    w, h = image.size
    target_ratio = TARGET_W / TARGET_H
    ratio = w / h
    if ratio > target_ratio:
        crop_w = int(h * target_ratio)
        left = (w - crop_w) // 2
        box = (left, 0, left + crop_w, h)
    else:
        crop_h = int(w / target_ratio)
        top = max(0, int((h - crop_h) * 0.42))
        box = (0, top, w, top + crop_h)
    return image.crop(box).resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)


def atlas_treatment(image: Image.Image, seed: int) -> Image.Image:
    """Keep the source recognizably photographic; add only subtle watercolor softness."""
    image = center_crop_3x2(image)
    image = ImageEnhance.Color(image).enhance(0.91)
    image = ImageEnhance.Contrast(image).enhance(0.97)
    image = ImageEnhance.Brightness(image).enhance(1.015)
    soft = image.filter(ImageFilter.GaussianBlur(radius=0.65))
    image = Image.blend(image, soft, 0.15)
    random.seed(seed)
    noise = Image.effect_noise((TARGET_W, TARGET_H), 18).convert("L")
    paper = Image.merge("RGB", (noise, noise, noise))
    paper = ImageEnhance.Brightness(paper).enhance(1.06)
    image = Image.blend(image, paper, 0.025)
    wash = Image.new("RGB", image.size, (244, 241, 232))
    image = Image.blend(image, wash, 0.025)
    return ImageEnhance.Sharpness(image).enhance(1.04)


def credit_record(asset: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    meta = chosen["meta"]
    return {
        "key": asset["key"],
        "output": f"assets/images/sweden/v4/{asset['output']}",
        "commonsTitle": chosen["title"],
        "sourcePage": chosen["descriptionUrl"],
        "originalUrl": chosen["originalUrl"],
        "author": clean_html(metadata_value(meta, "Artist")),
        "credit": clean_html(metadata_value(meta, "Credit")),
        "license": clean_html(metadata_value(meta, "LicenseShortName")),
        "licenseUrl": metadata_value(meta, "LicenseUrl"),
        "usageTerms": clean_html(metadata_value(meta, "UsageTerms")),
        "sourceDimensions": [chosen["width"], chosen["height"]],
        "selectionQuery": asset["query"],
    }


def update_country_json() -> None:
    data = json.loads(COUNTRY_PATH.read_text(encoding="utf-8"))
    data["hero"]["image"] = "assets/images/sweden/v4/hero-grinda.webp"
    replacements = {
        "gamla-stan": "assets/images/sweden/v4/gamla-stan.webp",
        "lapporten": "assets/images/sweden/v4/lapporten.webp",
        "high-coast": "assets/images/sweden/v4/high-coast.webp",
        "siljan": "assets/images/sweden/v4/siljan-dalarna.webp",
        "visby": "assets/images/sweden/v4/visby.webp",
        "langhammars": "assets/images/sweden/v4/langhammars-faro.webp",
        "smogen": "assets/images/sweden/v4/smogen.webp",
        "gota-canal": "assets/images/sweden/v4/gota-canal.webp",
    }
    for scene in data.get("scenes", []):
        if scene.get("id") in replacements:
            scene["image"] = replacements[scene["id"]]
    COUNTRY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    credits: list[dict[str, Any]] = []

    for index, asset in enumerate(ASSETS):
        print(f"[{index + 1}/{len(ASSETS)}] {asset['key']}: searching Commons")
        candidates = search_candidates(asset)
        if not candidates:
            raise RuntimeError(f"No license-compatible high-resolution Commons image found for {asset['key']}")

        errors: list[str] = []
        chosen = None
        rendered = None
        for candidate in candidates[:8]:
            try:
                print(
                    f"  trying {candidate['title']} "
                    f"({candidate['width']}x{candidate['height']}, score={candidate['score']:.2f})"
                )
                payload = download(candidate["url"])
                with Image.open(BytesIO(payload)) as source:
                    source.load()
                    rendered = atlas_treatment(source, seed=1000 + index)
                chosen = candidate
                break
            except Exception as exc:
                errors.append(f"{candidate['title']}: {exc}")

        if chosen is None or rendered is None:
            raise RuntimeError(
                f"Could not render a Commons source for {asset['key']}: " + " | ".join(errors)
            )

        output_path = OUT_DIR / asset["output"]
        rendered.save(output_path, "WEBP", quality=86, method=6)
        with Image.open(output_path) as verify:
            verify.load()
            if verify.size != (TARGET_W, TARGET_H):
                raise RuntimeError(f"Unexpected output size for {output_path}: {verify.size}")

        size = output_path.stat().st_size
        if size < 20_000:
            print(f"  warning: {output_path.name} is compact ({size} bytes) but decoded successfully")
        print(f"  saved {output_path.relative_to(ROOT)} ({size} bytes)")
        credits.append(credit_record(asset, chosen))

    CREDITS_PATH.write_text(
        json.dumps(
            {
                "country": "sweden",
                "treatment": "JOURNEY ATLAS subtle watercolor treatment applied to license-compatible Wikimedia Commons photographs",
                "assets": credits,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    update_country_json()
    print("Sweden v4 scenery build complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
