#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import urllib.parse
import urllib.error
import urllib.request
import time
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/estonia/approved"
WIDTH, HEIGHT = 1200, 800

SOURCES = [
    {
        "output": "hero-tallinn-old-town.webp",
        "file": "Tallinn panorama from Toomkirik, June 2010.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Tallinn_panorama_from_Toomkirik,_June_2010.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.50],
    },
    {
        "output": "viru-bog.webp",
        "file": "Sunset over dark forest (Unsplash).jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Sunset_over_dark_forest_(Unsplash).jpg",
        "license": "CC0 1.0",
        "centering": [0.50, 0.48],
    },
    {
        "output": "soomaa.webp",
        "file": "Fifth Season Kuusekaara Soomaa.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Fifth_Season_Kuusekaara_Soomaa.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.50],
    },
    {
        "output": "panga-cliff.webp",
        "file": "Panga cliff1.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Panga_cliff1.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.45],
    },
    {
        "output": "kaali-crater.webp",
        "file": "Kaali meteorite crater.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Kaali_meteorite_crater.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.52],
    },
    {
        "output": "narva-castle.webp",
        "file": "Narva Castle, Estonia.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Narva_Castle,_Estonia.jpg",
        "license": "CC0 1.0",
        "centering": [0.50, 0.48],
    },
    {
        "output": "suur-taevaskoda.webp",
        "file": "Tartumaa, Taevaskoja vaade.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Tartumaa,_Taevaskoja_vaade.jpg",
        "license": "Public domain",
        "centering": [0.50, 0.50],
    },
    {
        "output": "kopu-lighthouse.webp",
        "file": "View from Kõpu lighthouse.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:View_from_K%C3%B5pu_lighthouse.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.50],
    },
    {
        "output": "suur-munamagi.webp",
        "file": "Suur-Munamäe vaatetorn.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Suur-Munam%C3%A4e_vaatetorn.jpg",
        "license": "Public domain (PD-self)",
        "centering": [0.50, 0.45],
    },
]

def download(filename: str) -> bytes:
    url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + urllib.parse.quote(filename, safe="") + "?width=1600"
    headers = {"User-Agent": "Journey-Atlas/1.0 (contact: github.com/yagenji/Journey-Atlas)"}
    last_error = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read()
            if len(raw) < 20_000:
                raise RuntimeError(f"Downloaded file too small for {filename}: {len(raw)} bytes")
            time.sleep(5.0)
            return raw
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 5:
                raise
            wait = 8 * (attempt + 1)
            print(f"Wikimedia rate-limited {filename}; retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Download failed for {filename}: {last_error}")

def materialize(item: dict) -> None:
    raw = download(item["file"])
    with Image.open(io.BytesIO(raw)) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        fitted = ImageOps.fit(
            source,
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=tuple(item["centering"]),
        )
        destination = OUT / item["output"]
        fitted.save(destination, "WEBP", quality=90, method=6)
        with Image.open(destination) as check:
            check.load()
            if check.size != (WIDTH, HEIGHT) or check.format != "WEBP":
                raise RuntimeError(f"Invalid output: {destination} / {check.size} / {check.format}")

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for item in SOURCES:
        print(f"Materializing {item['output']} from {item['file']}")
        materialize(item)

    (OUT / "PHOTO_SOURCES.json").write_text(
        json.dumps(
            {
                "note": "Source photographs are public-domain/CC0 Wikimedia Commons files; resized/cropped only for JOURNEY ATLAS.",
                "assets": SOURCES,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print("Estonia Hero + 8 scene assets materialized at 1200x800.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
