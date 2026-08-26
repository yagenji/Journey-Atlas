#!/usr/bin/env python3
"""Repair Sweden source transport artifacts and materialize production artwork."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_MARKER = re.compile(r"\[\.\.\.[^\]]*\.\.\.\]")


def read_encoded(path: str) -> str:
    raw = (ROOT / path).read_text(encoding="utf-8").strip().lstrip("\ufeff")
    raw = TRANSPORT_MARKER.sub("", raw)
    return "".join(raw.split())


def materialize(output: str, parts: list[str]) -> None:
    encoded = "".join(read_encoded(part) for part in parts)
    binary = base64.b64decode(encoded, validate=True)
    if len(binary) < 12 or binary[:4] != b"RIFF" or binary[8:12] != b"WEBP":
        raise ValueError(f"Invalid WebP source for {output}")
    target = ROOT / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(binary)
    print(f"materialized {output}: {len(binary)} bytes")


def main() -> int:
    outputs = {
        "assets/images/sweden/v3/hero.webp": ["assets/images/sweden/v3/hero.b64"],
        "assets/images/sweden/v3/gamla-stan.webp": [
            "assets/images/sweden/v3/gamla-stan-parts/part-01.b64",
            "assets/images/sweden/v3/gamla-stan-parts/part-02.b64",
            "assets/images/sweden/v3/gamla-stan-parts/part-03.b64",
        ],
        "assets/images/sweden/v3/lapporten.webp": ["assets/images/sweden/v2/lapporten.b64"],
        "assets/images/sweden/v3/high-coast.webp": ["assets/images/sweden/v2/high-coast.b64"],
    }
    for output, parts in outputs.items():
        materialize(output, parts)

    country_path = ROOT / "data/countries/sweden.json"
    data = json.loads(country_path.read_text(encoding="utf-8"))
    data["hero"]["image"] = "assets/images/sweden/v3/hero.webp"
    replacements = {
        "gamla-stan": "assets/images/sweden/v3/gamla-stan.webp",
        "lapporten": "assets/images/sweden/v3/lapporten.webp",
        "high-coast": "assets/images/sweden/v3/high-coast.webp",
    }
    for scene in data["scenes"]:
        if scene["id"] in replacements:
            scene["image"] = replacements[scene["id"]]
    country_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
