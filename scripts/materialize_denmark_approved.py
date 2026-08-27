#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "transfer/denmark-approved/denmark-approved-assets.zip"
OUTPUT = ROOT / "assets/images/denmark/approved"
COUNTRY = ROOT / "data/countries/denmark.json"
SELF = ROOT / "scripts/materialize_denmark_approved.py"
WORKFLOW = ROOT / ".github/workflows/materialize-denmark-approved.yml"

EXPECTED = {
    "hero-copenhagen.webp",
    "mons-klint.webp",
    "kronborg.webp",
    "grenen.webp",
    "wadden-sea-mando.webp",
    "ribe.webp",
    "silkeborg-lakes.webp",
    "aeroskobing.webp",
    "hammershus.webp",
}

def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)

def main() -> int:
    require(ARCHIVE.exists(), "Denmark approved asset archive missing")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ARCHIVE) as z:
        names = {Path(n).name for n in z.namelist() if not n.endswith("/")}
        require(names == EXPECTED, f"Unexpected archive contents: {sorted(names)}")
        for name in sorted(EXPECTED):
            dst = OUTPUT / name
            with z.open(name) as src, dst.open("wb") as out:
                shutil.copyfileobj(src, out)

    for name in sorted(EXPECTED):
        p = OUTPUT / name
        raw = p.read_bytes()
        require(len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP", f"Invalid WebP: {name}")
        require(int.from_bytes(raw[4:8], "little") + 8 == len(raw), f"Truncated WebP: {name}")
        with Image.open(p) as im:
            im.load()
            require(im.format == "WEBP", f"Wrong format: {name}")
            require(im.size == (1200, 800), f"Wrong dimensions: {name} / {im.size}")

    data = json.loads(COUNTRY.read_text(encoding="utf-8"))
    paths = [data["hero"]["image"], *[s["image"] for s in data["scenes"]]]
    require(len(paths) == 9 and len(set(paths)) == 9, "Denmark JSON must reference 9 unique images")
    require(all(p.startswith("assets/images/denmark/approved/") for p in paths), "Denmark JSON points outside approved assets")
    for rel in paths:
        require((ROOT / rel).exists(), f"Missing referenced asset: {rel}")

    shutil.rmtree(ROOT / "transfer/denmark-approved", ignore_errors=True)
    SELF.unlink(missing_ok=True)
    WORKFLOW.unlink(missing_ok=True)

    print("Denmark approved Hero + 8 scenes validated and materialized.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
