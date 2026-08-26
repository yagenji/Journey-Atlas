#!/usr/bin/env python3
"""Build one Sweden v5 scenery illustration per invocation.

Real photographs from Wikimedia Commons are used only as geographic reference.
Final assets are strongly simplified into the fixed JOURNEY ATLAS editorial-watercolor
language. This script intentionally refuses bulk generation: use --scene once per asset.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets/images/sweden/v5"
COUNTRY_PATH = ROOT / "data/countries/sweden.json"
CREDITS_PATH = ROOT / "data/sweden-v5-image-credits.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "JourneyAtlas/1.0 (https://github.com/yagenji/Journey-Atlas)"
TARGET_W, TARGET_H = 1200, 800
MIN_SOURCE_W, MIN_SOURCE_H = 1200, 700

ASSETS = [
    {"key":"gamla-stan","queries":["\"Gamla Stan\" Stockholm waterfront","Gamla Stan Stockholm Sweden"],"preferred":["gamla","stan","stockholm","waterfront"],"output":"gamla-stan.webp"},
    {"key":"lapporten","queries":["Lapporten Abisko Sweden landscape","Lapporten Abisko"],"preferred":["lapporten","abisko"],"output":"lapporten.webp"},
    {"key":"high-coast","queries":["\"Höga Kusten\" Sweden landscape","High Coast Sweden landscape"],"preferred":["höga","kusten","high coast"],"output":"high-coast.webp"},
    {"key":"siljan","queries":["Siljan Dalarna lake Sweden photograph","Lake Siljan Dalarna Sweden landscape","Siljan Sweden lake village"],"preferred":["siljan","dalarna","lake"],"output":"siljan-dalarna.webp"},
    {"key":"visby","queries":["Visby city wall Gotland Sweden","Visby Gotland Sweden wall"],"preferred":["visby","gotland","wall"],"output":"visby.webp"},
    {"key":"langhammars","queries":["Langhammars Fårö rauk Sweden","Langhammars Faro Sweden"],"preferred":["langhammars","fårö","faro","rauk"],"output":"langhammars-faro.webp"},
    {"key":"smogen","queries":["Smögen Bohuslän harbor boathouses Sweden","Smögen Sweden harbor","Smogen Sweden harbor"],"preferred":["smögen","smogen","boathouse","harbor"],"output":"smogen.webp"},
    {"key":"gota-canal","queries":["Göta Canal Berg Locks Sweden","Bergs slussar Göta kanal","Gota Canal Berg Locks Sweden"],"preferred":["göta","gota","berg","locks","canal","sluss"],"output":"gota-canal.webp"},
]
ASSET_BY_KEY = {a["key"]: a for a in ASSETS}
ALLOWED_LICENSE_TOKENS = ("cc by","cc-by","cc by-sa","cc-by-sa","cc0","public domain","pd-")
NON_PHOTO_TOKENS = (
    " study", "painting", "drawing", "nationalmuseum", "oil on", "etching",
    "lithograph", "sketch", "watercolour painting", "watercolor painting",
)


def api_get(params: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{COMMONS_API}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def metadata_value(meta: dict[str, Any], key: str) -> str:
    value = meta.get(key, {})
    return str(value.get("value") or "") if isinstance(value, dict) else str(value or "")


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def license_allowed(meta: dict[str, Any]) -> bool:
    combined = f"{metadata_value(meta,'LicenseShortName')} {metadata_value(meta,'UsageTerms')}".casefold()
    return any(token in combined for token in ALLOWED_LICENSE_TOKENS)


def looks_like_photo(title: str, meta: dict[str, Any]) -> bool:
    description = clean_html(metadata_value(meta, "ImageDescription"))
    object_name = clean_html(metadata_value(meta, "ObjectName"))
    haystack = f" {title} {description} {object_name}".casefold()
    return not any(token in haystack for token in NON_PHOTO_TOKENS)


def search_one(query: str, asset: dict[str, Any]) -> list[dict[str, Any]]:
    data = api_get({
        "action":"query","format":"json","generator":"search","gsrnamespace":6,
        "gsrsearch":query,"gsrlimit":30,"prop":"imageinfo",
        "iiprop":"url|size|mime|extmetadata","iiurlwidth":2000,"redirects":1,
    })
    pages = list((data.get("query",{}).get("pages",{}) or {}).values())
    candidates: list[dict[str, Any]] = []
    for rank, page in enumerate(pages):
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        meta = info.get("extmetadata") or {}
        mime = str(info.get("mime") or "")
        width, height = int(info.get("width") or 0), int(info.get("height") or 0)
        title = str(page.get("title") or "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        if width < MIN_SOURCE_W or height < MIN_SOURCE_H or not license_allowed(meta):
            continue
        if not looks_like_photo(title, meta):
            continue
        tl = title.casefold()
        hits = sum(1 for token in asset["preferred"] if token.casefold() in tl)
        aspect = width / max(height, 1)
        landscape_bonus = 2.0 if 1.25 <= aspect <= 2.2 else (0.4 if aspect > 1 else -1.2)
        resolution_bonus = min(3.0, math.log2(max(1, width*height)/1_000_000 + 1))
        score = hits*3 + landscape_bonus + resolution_bonus - rank*0.08
        candidates.append({
            "score":score,"title":title,"width":width,"height":height,
            "url":info.get("thumburl") or info.get("url"),"originalUrl":info.get("url"),
            "descriptionUrl":info.get("descriptionurl"),"meta":meta,"selectionQuery":query,
        })
    return candidates


def search_candidates(asset: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for query in asset["queries"]:
        for item in search_one(query, asset):
            key = item["title"]
            if key not in merged or item["score"] > merged[key]["score"]:
                merged[key] = item
    return sorted(merged.values(), key=lambda x: x["score"], reverse=True)


def crop_3x2(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    w, h = image.size
    ratio = TARGET_W / TARGET_H
    if w / h > ratio:
        cw = int(h * ratio); left = (w-cw)//2; box = (left, 0, left+cw, h)
    else:
        ch = int(w / ratio); top = max(0, int((h-ch)*0.42)); box = (0, top, w, top+ch)
    return image.crop(box).resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)


def editorial_watercolor(image: Image.Image) -> Image.Image:
    """Remove photographic micro-detail while retaining real-world forms."""
    image = crop_3x2(image)
    image = ImageEnhance.Color(image).enhance(0.82)
    image = ImageEnhance.Contrast(image).enhance(0.90)
    image = ImageEnhance.Brightness(image).enhance(1.045)
    smooth = image.filter(ImageFilter.MedianFilter(size=5)).filter(ImageFilter.GaussianBlur(0.8))
    image = Image.blend(image, smooth, 0.62)
    broad = image.resize((300, 200), Image.Resampling.BILINEAR).resize((TARGET_W, TARGET_H), Image.Resampling.BICUBIC)
    image = Image.blend(image, broad, 0.16)
    quant = image.quantize(colors=72, method=Image.Quantize.MEDIANCUT).convert("RGB").filter(ImageFilter.GaussianBlur(0.35))
    image = Image.blend(image, quant, 0.58)
    gray = ImageOps.grayscale(image)
    edges = ImageEnhance.Contrast(ImageOps.autocontrast(gray.filter(ImageFilter.FIND_EDGES)).filter(ImageFilter.GaussianBlur(0.6))).enhance(0.68)
    ink = ImageOps.colorize(edges, black=(247,245,239), white=(58,67,67))
    image = Image.blend(image, ImageChops.multiply(image, ink), 0.075)
    wash = Image.new("RGB", image.size, (244,242,234))
    image = Image.blend(image, wash, 0.085)
    return ImageEnhance.Sharpness(image).enhance(0.80)


def credit_record(asset: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    meta = chosen["meta"]
    return {
        "key": asset["key"],
        "output": f"assets/images/sweden/v5/{asset['output']}",
        "commonsTitle": chosen["title"],
        "sourcePage": chosen["descriptionUrl"],
        "originalUrl": chosen["originalUrl"],
        "author": clean_html(metadata_value(meta,"Artist")) or "Wikimedia Commons contributor",
        "credit": clean_html(metadata_value(meta,"Credit")),
        "license": clean_html(metadata_value(meta,"LicenseShortName")),
        "licenseUrl": metadata_value(meta,"LicenseUrl"),
        "usageTerms": clean_html(metadata_value(meta,"UsageTerms")),
        "sourceDimensions": [chosen["width"], chosen["height"]],
        "selectionQuery": chosen["selectionQuery"],
        "treatment": "Clean editorial watercolor redraw from a real-world photographic reference",
    }


def upsert_credit(record: dict[str, Any]) -> None:
    data = {"country":"sweden","version":"v5","assets":[]}
    if CREDITS_PATH.exists():
        data = json.loads(CREDITS_PATH.read_text(encoding="utf-8"))
    by_key = {item.get("key"): item for item in (data.get("assets") or [])}
    by_key[record["key"]] = record
    order = {asset["key"]: idx for idx, asset in enumerate(ASSETS)}
    data["country"], data["version"] = "sweden", "v5"
    data["assets"] = sorted(by_key.values(), key=lambda item: order.get(item.get("key"), 999))
    CREDITS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def build_one(scene_key: str) -> None:
    asset = ASSET_BY_KEY[scene_key]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = search_candidates(asset)
    if not candidates:
        raise RuntimeError(f"No suitable real-world photographic reference for {scene_key}")
    errors: list[str] = []
    for candidate in candidates[:12]:
        try:
            payload = download(candidate["url"])
            with Image.open(BytesIO(payload)) as source:
                source.load()
                rendered = editorial_watercolor(source)
            output = OUT_DIR / asset["output"]
            rendered.save(output, "WEBP", quality=89, method=6)
            with Image.open(output) as verify:
                verify.load()
                if verify.format != "WEBP" or verify.size != (TARGET_W, TARGET_H):
                    raise RuntimeError(f"invalid output {verify.format} {verify.size}")
            upsert_credit(credit_record(asset, candidate))
            print(f"{scene_key}: {candidate['title']} -> {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")
            return
        except Exception as exc:
            errors.append(f"{candidate['title']}: {exc}")
    raise RuntimeError(f"Could not build {scene_key}: {' | '.join(errors)}")


def finalize_country_json() -> None:
    hero = OUT_DIR / "hero-grinda.webp"
    if not hero.exists():
        raise RuntimeError("Approved v5 Hero is missing")
    missing = [asset["output"] for asset in ASSETS if not (OUT_DIR/asset["output"]).exists()]
    if missing:
        raise RuntimeError(f"Cannot finalize; missing v5 scenes: {', '.join(missing)}")
    data = json.loads(COUNTRY_PATH.read_text(encoding="utf-8"))
    data["hero"]["image"] = "assets/images/sweden/v5/hero-grinda.webp"
    replacements = {asset["key"]: f"assets/images/sweden/v5/{asset['output']}" for asset in ASSETS}
    for scene in data.get("scenes", []):
        if scene.get("id") in replacements:
            scene["image"] = replacements[scene["id"]]
    COUNTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Sweden JSON finalized to approved v5 artwork; publication state untouched.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=list(ASSET_BY_KEY))
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    if args.finalize:
        finalize_country_json(); return 0
    if not args.scene:
        parser.error("--scene is required; Sweden artwork must be built one image at a time")
    build_one(args.scene)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
