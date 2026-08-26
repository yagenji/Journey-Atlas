#!/usr/bin/env python3
"""Materialize the approved Sweden Hero artwork from temporary base64 transport parts."""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "assets/images/sweden/v5-input/hero-grinda"
OUTPUT = ROOT / "assets/images/sweden/v5/hero-grinda.webp"


def main() -> int:
    parts = sorted(INPUT_DIR.glob("part-*.b64"))
    if not parts:
        if OUTPUT.exists():
            with Image.open(OUTPUT) as image:
                image.load()
                if image.format != "WEBP" or image.size != (1200, 800):
                    raise RuntimeError(f"Existing Hero is invalid: {image.format} {image.size}")
            print("Approved Sweden Hero already materialized.")
            return 0
        raise RuntimeError("No Sweden Hero transport parts found")

    encoded = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    payload = base64.b64decode(encoded, validate=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)

    with Image.open(OUTPUT) as image:
        image.load()
        if image.format != "WEBP":
            raise RuntimeError(f"Approved Hero is not WebP: {image.format}")
        if image.size != (1200, 800):
            raise RuntimeError(f"Approved Hero has wrong dimensions: {image.size}")

    shutil.rmtree(ROOT / "assets/images/sweden/v5-input")
    print(f"Materialized approved Sweden Hero: {OUTPUT.relative_to(ROOT)} ({len(payload)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
