#!/usr/bin/env python3
"""Create a temporary visual QA contact sheet for Sweden v5 scenery."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-output/sweden-v5-scenes.jpg"
SCENES = [
    ("1 Gamla Stan", "gamla-stan.webp"),
    ("2 Lapporten / Abisko", "lapporten.webp"),
    ("3 High Coast", "high-coast.webp"),
    ("4 Siljan / Dalarna", "siljan-dalarna.webp"),
    ("5 Visby / Gotland", "visby.webp"),
    ("6 Langhammars / Fårö", "langhammars-faro.webp"),
    ("7 Smögen / Bohuslän", "smogen.webp"),
    ("8 Göta Canal / Berg Locks", "gota-canal.webp"),
]
thumb_w, thumb_h = 600, 400
label_h = 52
canvas = Image.new("RGB", (thumb_w*2, (thumb_h+label_h)*4), "white")
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default(size=22)
for i, (label, filename) in enumerate(SCENES):
    path = ROOT / "assets/images/sweden/v5" / filename
    with Image.open(path) as im:
        im.load(); im = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    x=(i%2)*thumb_w; y=(i//2)*(thumb_h+label_h)
    canvas.paste(im,(x,y)); draw.text((x+16,y+thumb_h+13),label,fill="black",font=font)
OUT.parent.mkdir(parents=True,exist_ok=True)
canvas.save(OUT,"JPEG",quality=90,optimize=True)
print(OUT)
