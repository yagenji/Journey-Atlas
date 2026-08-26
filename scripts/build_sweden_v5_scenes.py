#!/usr/bin/env python3
"""Build Sweden v5 scene illustrations from place-specific Wikimedia Commons sources.

The sources are used only as geographic/reference material. The output applies a
strong editorial-watercolor abstraction so final assets do not read as photographs.
Hero is separately approved and stored at assets/images/sweden/v5/hero-grinda.webp.
"""

from __future__ import annotations

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

TARGET_W = 1200
TARGET_H = 800
MIN_SOURCE_W = 1200
MIN_SOURCE_H = 700

ASSETS = [
    {"key":"gamla-stan","queries":["\"Gamla Stan\" Stockholm waterfront","Gamla Stan Stockholm Sweden"],"preferred":["gamla","stan","stockholm","waterfront"],"output":"gamla-stan.webp"},
    {"key":"lapporten","queries":["Lapporten Abisko Sweden landscape","Lapporten Abisko"],"preferred":["lapporten","abisko"],"output":"lapporten.webp"},
    {"key":"high-coast","queries":["\"Höga Kusten\" Sweden landscape","High Coast Sweden landscape"],"preferred":["höga","kusten","high coast"],"output":"high-coast.webp"},
    {"key":"siljan","queries":["Siljan Lake Dalarna Sweden","Siljan Dalarna Sweden lake","Siljan Sweden landscape"],"preferred":["siljan","dalarna"],"output":"siljan-dalarna.webp"},
    {"key":"visby","queries":["Visby city wall Gotland Sweden","Visby Gotland Sweden wall"],"preferred":["visby","gotland","wall"],"output":"visby.webp"},
    {"key":"langhammars","queries":["Langhammars Fårö rauk Sweden","Langhammars Faro Sweden"],"preferred":["langhammars","fårö","faro","rauk"],"output":"langhammars-faro.webp"},
    {"key":"smogen","queries":["Smögen Bohuslän harbor boathouses Sweden","Smögen Sweden harbor","Smogen Sweden harbor"],"preferred":["smögen","smogen","boathouse","harbor"],"output":"smogen.webp"},
    {"key":"gota-canal","queries":["Göta Canal Berg Locks Sweden","Bergs slussar Göta kanal","Gota Canal Berg Locks Sweden"],"preferred":["göta","gota","berg","locks","canal","sluss"],"output":"gota-canal.webp"},
]

ALLOWED_LICENSE_TOKENS = ("cc by","cc-by","cc by-sa","cc-by-sa","cc0","public domain","pd-")


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
    combined = f"{metadata_value(meta,'LicenseShortName')} {metadata_value(meta,'UsageTerms')}".lower()
    return any(token in combined for token in ALLOWED_LICENSE_TOKENS)


def search_one(query: str, asset: dict[str, Any]) -> list[dict[str, Any]]:
    data = api_get({
        "action":"query","format":"json","generator":"search","gsrnamespace":6,
        "gsrsearch":query,"gsrlimit":24,"prop":"imageinfo",
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
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        if width < MIN_SOURCE_W or height < MIN_SOURCE_H or not license_allowed(meta):
            continue
        title = str(page.get("title") or "")
        tl = title.casefold()
        hits = sum(1 for token in asset["preferred"] if token.casefold() in tl)
        aspect = width / max(height,1)
        landscape_bonus = 2.0 if 1.25 <= aspect <= 2.2 else (0.4 if aspect > 1 else -1.2)
        resolution_bonus = min(3.0, math.log2(max(1,width*height)/1_000_000 + 1))
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
        if merged:
            break
    return sorted(merged.values(), key=lambda x:x["score"], reverse=True)


def crop_3x2(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    w,h = image.size
    ratio = TARGET_W/TARGET_H
    if w/h > ratio:
        cw = int(h*ratio); left=(w-cw)//2; box=(left,0,left+cw,h)
    else:
        ch = int(w/ratio); top=max(0,int((h-ch)*0.42)); box=(0,top,w,top+ch)
    return image.crop(box).resize((TARGET_W,TARGET_H),Image.Resampling.LANCZOS)


def editorial_watercolor(image: Image.Image) -> Image.Image:
    """Convert photographic reference into clean illustrated watercolor-like artwork."""
    image = crop_3x2(image)
    image = ImageEnhance.Color(image).enhance(0.84)
    image = ImageEnhance.Contrast(image).enhance(0.91)
    image = ImageEnhance.Brightness(image).enhance(1.045)

    # Remove photographic micro-detail while preserving geographic/architectural masses.
    smooth = image.filter(ImageFilter.MedianFilter(size=5)).filter(ImageFilter.GaussianBlur(0.75))
    image = Image.blend(image, smooth, 0.58)

    # Compress color variation into clean editorial paint shapes.
    quant = image.quantize(colors=96, method=Image.Quantize.MEDIANCUT).convert("RGB")
    quant = quant.filter(ImageFilter.GaussianBlur(0.35))
    image = Image.blend(image, quant, 0.52)

    # Restrained structural definition, deliberately weaker than cartoon line art.
    gray = ImageOps.grayscale(image)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges).filter(ImageFilter.GaussianBlur(0.55))
    edges = ImageEnhance.Contrast(edges).enhance(0.72)
    ink = ImageOps.colorize(edges, black=(246,244,237), white=(55,66,67))
    image = Image.blend(image, ImageChops.multiply(image, ink), 0.09)

    # Luminous matte wash; explicitly no paper grain or photographic sharpening.
    wash = Image.new("RGB", image.size, (244,242,234))
    image = Image.blend(image, wash, 0.075)
    image = ImageEnhance.Sharpness(image).enhance(0.82)
    return image


def credit_record(asset: dict[str, Any], chosen: dict[str, Any]) -> dict[str, Any]:
    meta = chosen["meta"]
    return {
        "key":asset["key"],"output":f"assets/images/sweden/v5/{asset['output']}",
        "commonsTitle":chosen["title"],"sourcePage":chosen["descriptionUrl"],
        "originalUrl":chosen["originalUrl"],"author":clean_html(metadata_value(meta,"Artist")),
        "credit":clean_html(metadata_value(meta,"Credit")),"license":clean_html(metadata_value(meta,"LicenseShortName")),
        "licenseUrl":metadata_value(meta,"LicenseUrl"),"usageTerms":clean_html(metadata_value(meta,"UsageTerms")),
        "sourceDimensions":[chosen["width"],chosen["height"]],"selectionQuery":chosen["selectionQuery"],
        "treatment":"Strong clean editorial watercolor abstraction; source used as real-world geographic reference",
    }


def update_country_json() -> None:
    data = json.loads(COUNTRY_PATH.read_text(encoding="utf-8"))
    data["hero"]["image"] = "assets/images/sweden/v5/hero-grinda.webp"
    replacements = {asset["key"]:f"assets/images/sweden/v5/{asset['output']}" for asset in ASSETS}
    for scene in data.get("scenes",[]):
        if scene.get("id") in replacements:
            scene["image"] = replacements[scene["id"]]
    COUNTRY_PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def main() -> int:
    hero = OUT_DIR / "hero-grinda.webp"
    if not hero.exists():
        raise RuntimeError("Approved v5 Hero is missing; do not substitute a photograph")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    credits: list[dict[str, Any]] = []
    for index, asset in enumerate(ASSETS, start=1):
        print(f"[{index}/8] {asset['key']}: searching Commons reference")
        candidates=search_candidates(asset)
        if not candidates:
            raise RuntimeError(f"No suitable Commons reference for {asset['key']}")
        chosen=None; rendered=None; errors=[]
        for candidate in candidates[:10]:
            try:
                payload=download(candidate["url"])
                with Image.open(BytesIO(payload)) as source:
                    source.load(); rendered=editorial_watercolor(source)
                chosen=candidate; break
            except Exception as exc:
                errors.append(f"{candidate['title']}: {exc}")
        if chosen is None or rendered is None:
            raise RuntimeError(f"Could not build {asset['key']}: {' | '.join(errors)}")
        output=OUT_DIR/asset["output"]
        rendered.save(output,"WEBP",quality=89,method=6)
        with Image.open(output) as verify:
            verify.load()
            if verify.format!="WEBP" or verify.size!=(TARGET_W,TARGET_H):
                raise RuntimeError(f"Invalid output {output}: {verify.format} {verify.size}")
        print(f"  {chosen['title']} -> {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")
        credits.append(credit_record(asset,chosen))
    CREDITS_PATH.write_text(json.dumps({"country":"sweden","version":"v5","assets":credits},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    update_country_json()
    print("Sweden v5 scene build complete; atlas publication state unchanged.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
