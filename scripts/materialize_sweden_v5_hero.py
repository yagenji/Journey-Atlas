#!/usr/bin/env python3
"""Materialize the approved Sweden Hero artwork from temporary transport chunks."""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "assets/images/sweden/v5-bin/hero-grinda"
TEXT_DIR = ROOT / "assets/images/sweden/v5-input/hero-grinda"
OUTPUT = ROOT / "assets/images/sweden/v5/hero-grinda.webp"


def existing_output_is_valid() -> bool:
    if not OUTPUT.exists():
        return False
    try:
        with Image.open(OUTPUT) as image:
            image.load()
            return image.format == "WEBP" and image.size == (1200, 800)
    except Exception:
        return False


def decode_payload() -> bytes:
    binary_parts = sorted(BIN_DIR.glob("part-*.bin"))
    if binary_parts:
        return b"".join(part.read_bytes() for part in binary_parts)

    text_parts = sorted(TEXT_DIR.glob("part-*.b64"))
    if text_parts:
        encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in text_parts)
        encoded += "=" * (-len(encoded) % 4)
        return base64.b64decode(encoded, validate=False)

    raise RuntimeError("No Sweden Hero transport chunks found")


def main() -> int:
    if not BIN_DIR.exists() and not TEXT_DIR.exists() and existing_output_is_valid():
        print("Approved Sweden Hero already materialized.")
        return 0

    payload = decode_payload()
    if len(payload) < 12 or payload[:4] != b"RIFF" or payload[8:12] != b"WEBP":
        raise RuntimeError("Decoded approved Hero is not a valid WebP payload")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)

    with Image.open(OUTPUT) as image:
        image.load()
        if image.format != "WEBP":
            raise RuntimeError(f"Approved Hero is not WebP: {image.format}")
        if image.size != (1200, 800):
            raise RuntimeError(f"Approved Hero has wrong dimensions: {image.size}")

    shutil.rmtree(ROOT / "assets/images/sweden/v5-bin", ignore_errors=True)
    shutil.rmtree(ROOT / "assets/images/sweden/v5-input", ignore_errors=True)
    print(f"Materialized approved Sweden Hero: {OUTPUT.relative_to(ROOT)} ({len(payload)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
