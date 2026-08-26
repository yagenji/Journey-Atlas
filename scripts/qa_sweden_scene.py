#!/usr/bin/env python3
"""QA one Sweden v5 scenery asset before it is accepted into the build branch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CREDITS = ROOT / "data/sweden-v5-image-credits.json"
FILES = {
    "gamla-stan":"gamla-stan.webp",
    "lapporten":"lapporten.webp",
    "high-coast":"high-coast.webp",
    "siljan":"siljan-dalarna.webp",
    "visby":"visby.webp",
    "langhammars":"langhammars-faro.webp",
    "smogen":"smogen.webp",
    "gota-canal":"gota-canal.webp",
}
NON_PHOTO = (" study", "painting", "drawing", "nationalmuseum", "oil on", "etching", "lithograph", "sketch")


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in FILES:
        raise SystemExit("usage: qa_sweden_scene.py <scene-id>")
    key = sys.argv[1]
    relative = f"assets/images/sweden/v5/{FILES[key]}"
    path = ROOT / relative
    if not path.exists(): fail(f"missing scene artwork: {relative}")
    raw = path.read_bytes()
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP": fail(f"invalid WebP signature: {relative}")
    if int.from_bytes(raw[4:8], "little") + 8 != len(raw): fail(f"truncated WebP: {relative}")
    with Image.open(path) as image:
        image.load()
        if image.format != "WEBP" or image.size != (1200, 800):
            fail(f"invalid scene decode: {image.format} {image.size}")
    if not CREDITS.exists(): fail("missing Sweden v5 credit metadata")
    credits = json.loads(CREDITS.read_text(encoding="utf-8"))
    item = next((x for x in credits.get("assets", []) if x.get("key") == key), None)
    if not item: fail(f"missing credit record: {key}")
    if item.get("output") != relative: fail(f"credit/output mismatch: {key}")
    title = str(item.get("commonsTitle") or "").casefold()
    if any(token in f" {title}" for token in NON_PHOTO): fail(f"non-photo reference rejected: {title}")
    for field in ("sourcePage", "author", "license"):
        if not item.get(field): fail(f"missing {field}: {key}")
    if "watercolor" not in str(item.get("treatment", "")).casefold(): fail(f"missing treatment metadata: {key}")
    print(f"Sweden scene QA passed: {key} / 1200x800 / full WebP decode / photographic reference metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
