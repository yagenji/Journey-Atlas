#!/usr/bin/env python3
"""Import the approved New Caledonia image bundle for the draft Region page.

Run only after receiving the exact 13-image handoff ZIP from the project owner.
No image is generated, renamed based on guesswork, or substituted from another
Region. This script does not change publication status.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "assets/images/france/new-caledonia/approved/"
EXPECTED_NAMES = (
    "hero-kanumera-bay.webp",
    "scene-01-upi-bay.webp",
    "scene-02-heart-of-voh.webp",
    "scene-03-poule-hienghene.webp",
    "scene-04-jokin-cliffs.webp",
    "scene-05-mouli-bridge.webp",
    "scene-06-tjibaou.webp",
    "scene-07-riviere-bleue.webp",
    "scene-08-grandes-fougeres.webp",
    "food-01-bougna.webp",
    "food-02-langouste-grillee.webp",
    "food-03-bulimes.webp",
    "food-04-salade-cerf.webp",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path, help="13-image approved ZIP")
    parser.add_argument("--check-only", action="store_true", help="Validate without writing files")
    args = parser.parse_args()
    if not args.zip.is_file():
        parser.error(f"ZIP not found: {args.zip}")

    expected = {PREFIX + name for name in EXPECTED_NAMES}
    with zipfile.ZipFile(args.zip) as zf:
        members = [entry for entry in zf.infolist() if not entry.is_dir()]
        paths = [entry.filename for entry in members]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate archive paths are forbidden")
        found = {name for name in paths if name.endswith(".webp")}
        missing, extra = expected - found, found - expected
        if missing or extra:
            raise ValueError(
                "Unexpected image set: missing="
                + ", ".join(sorted(missing))
                + "; extra="
                + ", ".join(sorted(extra))
            )
        if zf.testzip() is not None:
            raise ValueError("ZIP checksum verification failed")
        staged: dict[str, bytes] = {}
        for relative in sorted(expected):
            payload = zf.read(relative)
            if len(payload) < 5000 or payload[:4] != b"RIFF" or payload[8:12] != b"WEBP":
                raise ValueError(f"Not a valid WEBP envelope: {relative}")
            try:
                from PIL import Image
            except ImportError:
                raise RuntimeError("Install Pillow to validate dimensions and image integrity")
            with Image.open(io.BytesIO(payload)) as image:
                image.verify()
            with Image.open(io.BytesIO(payload)) as image:
                width, height = image.size
                if width < 1000 or height < 600 or not 1.4 <= width / height <= 2:
                    raise ValueError(f"Unexpected image dimensions: {relative}: {width}x{height}")
            staged[relative] = payload

    print(f"PASS: {len(staged)} distinct, readable WebP images verified")
    if args.check_only:
        return 0
    for relative, payload in staged.items():
        target = ROOT / relative
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite an existing asset: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        print(f"  Imported {relative}: {len(payload):,} bytes")
    print("Imported the 13-image bundle. Region remains unpublished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
