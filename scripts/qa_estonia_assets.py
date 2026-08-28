#!/usr/bin/env python3
# source-refresh: upgraded Estonia set
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "assets/images/estonia/approved"
OUT = ROOT / ".qa"
OUT.mkdir(exist_ok=True)

FILES = [
    ("HERO Tallinn", "hero-tallinn-old-town.webp"),
    ("1 Viru Bog", "viru-bog.webp"),
    ("2 Soomaa", "soomaa.webp"),
    ("3 Panga Cliff", "panga-cliff.webp"),
    ("4 Kaali Crater", "kaali-crater.webp"),
    ("5 Narva Castle", "narva-castle.webp"),
    ("6 Suur Taevaskoda", "suur-taevaskoda.webp"),
    ("7 Kõpu Lighthouse", "kopu-lighthouse.webp"),
    ("8 Suur Munamägi", "suur-munamagi.webp"),
]

CELL_W, IMAGE_H, LABEL_H = 400, 267, 33
sheet = Image.new("RGB", (CELL_W * 3, (IMAGE_H + LABEL_H) * 3), "white")
draw = ImageDraw.Draw(sheet)

for index, (label, name) in enumerate(FILES):
    path = BASE / name
    with Image.open(path) as im:
        im.load()
        assert im.format == "WEBP", f"{name}: {im.format}"
        assert im.size == (1200, 800), f"{name}: {im.size}"
        thumb = ImageOps.fit(im.convert("RGB"), (CELL_W, IMAGE_H), method=Image.Resampling.LANCZOS)
    x = (index % 3) * CELL_W
    y = (index // 3) * (IMAGE_H + LABEL_H)
    sheet.paste(thumb, (x, y))
    draw.text((x + 10, y + IMAGE_H + 9), label, fill="black")

sheet.save(OUT / "estonia-contact-sheet.jpg", quality=92)
print("Estonia asset QA passed: 9 WebP files at 1200x800.")
