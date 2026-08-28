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
        "file": "Tallinn Town Hall tower from Kohtuotsa viewing platform.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Tallinn_Town_Hall_tower_from_Kohtuotsa_viewing_platform.jpg",
        "author": "Ymblanter",
        "license": "CC BY-SA 4.0",
        "centering": [0.50, 0.48],
    },
    {
        "output": "viru-bog.webp",
        "file": "Viru bog - Boardwalk 01.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Viru_bog_-_Boardwalk_01.jpg",
        "author": "Syrio",
        "license": "CC BY-SA 4.0",
        "centering": [0.50, 0.52],
    },
    {
        "output": "soomaa.webp",
        "file": "Üleujutatud lammimets Soomaal.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:%C3%9Cleujutatud_lammimets_Soomaal.jpg",
        "author": "Ruukel",
        "license": "CC BY-SA 4.0",
        "centering": [0.50, 0.50],
    },
    {
        "output": "panga-cliff.webp",
        "file": "Panga cliff.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Panga_cliff.jpg",
        "author": "KalervoK",
        "license": "CC BY-SA 3.0",
        "centering": [0.50, 0.50],
    },
    {
        "output": "kaali-crater.webp",
        "file": "Kaali meteorite crater.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Kaali_meteorite_crater.jpg",
        "author": "Hannu",
        "license": "Public domain",
        "centering": [0.50, 0.52],
    },
    {
        "output": "narva-castle.webp",
        "file": "Narva Castle, Estonia.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Narva_Castle,_Estonia.jpg",
        "author": "KalervoK",
        "license": "CC0 1.0",
        "centering": [0.50, 0.48],
    },
    {
        "output": "suur-taevaskoda.webp",
        "file": "Suur-Taevaskoda.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:Suur-Taevaskoda.jpg",
        "author": "Külli Kolina",
        "license": "CC BY-SA 3.0 EE",
        "centering": [0.50, 0.50],
    },
    {
        "output": "kopu-lighthouse.webp",
        "file": "Kõpu lighthouse (2025).jpg",
        "source": "https://commons.wikimedia.org/wiki/File:K%C3%B5pu_lighthouse_(2025).jpg",
        "author": "Monika mich",
        "license": "CC BY-SA 4.0",
        "centering": [0.50, 0.50],
    },
    {
        "output": "suur-munamagi.webp",
        "file": "View from the Suur Munamägi observation tower 1.jpg",
        "source": "https://commons.wikimedia.org/wiki/File:View_from_the_Suur_Munam%C3%A4gi_observation_tower_1.jpg",
        "author": "Reosarevok",
        "license": "CC BY-SA 4.0",
        "centering": [0.50, 0.50],
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
                "note": "Wikimedia Commons source photographs. Files were resized/cropped to 1200x800; attribution and license are recorded per asset.",
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
