#!/usr/bin/env python3
"""Materialize the user-approved Sweden v6 artwork from temporary transfer chunks.

The transfer chunks are authoring-only. This script validates the transfer archive,
fully decodes every WebP, writes production assets, updates only image references in
Sweden JSON, and removes all temporary transfer material.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TRANSFER = ROOT / "assets/images/sweden/v6-transfer"
READY = ROOT / "data/sweden-v6-transfer-ready.txt"
OUTPUT = ROOT / "assets/images/sweden/v6"
COUNTRY = ROOT / "data/countries/sweden.json"
TEST_ARTIFACT = ROOT / "assets/images/sweden/v6-test.txt"

ARCHIVE_SHA256 = "da47a65072794e82651c865126131eb0f309ff23ec90c4e8f0e37a9b23002e9d"
EXPECTED = {
    "hero-grinda.webp": "294965750b72902079747610abacabb608b26601a483c70910c216b5e223431e",
    "gamla-stan.webp": "fa97ac04d0ac85d3ae69f5a17a9e40efc275dfb5ca6f6bed1e8e654fd0999213",
    "lapporten.webp": "9a2a034a8e2f6842707aa3c84c4d5ddabc3a421e4147630d80387c226f0c8b76",
    "high-coast.webp": "03b648b66bfe146df86c8e27f1830c6f99bb885573c521c172c25891fa3ec9a2",
    "siljan-dalarna.webp": "1000f626ce1fdcac833e13a2ea488a14824ac229307483d5e5760460c91495c4",
    "visby.webp": "84eb0a26ba4fc6bc6b11332556aa2e966cdda0ace53e206e6d9120af77bcf6c0",
    "langhammars-faro.webp": "76ae5547a44a35e19591dc7e4cf81c9d8eeb266dd2a08248c613e8b84d6b5783",
    "smogen.webp": "b326613e1e8d665375ab8e9ee4cbd97a329a467fb7746050ecda8f20d0944019",
    "gota-canal.webp": "1b5ecd37524b06600fb8050d485ce628ce88c078a27659f8257b81a9e9537ec1",
}
SCENE_FILES = {
    "gamla-stan": "gamla-stan.webp",
    "lapporten": "lapporten.webp",
    "high-coast": "high-coast.webp",
    "siljan": "siljan-dalarna.webp",
    "visby": "visby.webp",
    "langhammars": "langhammars-faro.webp",
    "smogen": "smogen.webp",
    "gota-canal": "gota-canal.webp",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def validate_webp(name: str, raw: bytes) -> None:
    require(hashlib.sha256(raw).hexdigest() == EXPECTED[name], f"SHA-256 mismatch: {name}")
    require(len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP", f"Invalid WebP signature: {name}")
    require(int.from_bytes(raw[4:8], "little") + 8 == len(raw), f"Truncated WebP: {name}")
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        require(image.format == "WEBP", f"Wrong format: {name} / {image.format}")
        require(image.size == (1200, 800), f"Wrong dimensions: {name} / {image.size}")


def main() -> int:
    if not READY.exists():
        print("Sweden v6 transfer is not marked ready; nothing to do.")
        return 0

    parts = sorted(TRANSFER.glob("part-*.b64"))
    require(parts, "Sweden v6 transfer chunks are missing")
    encoded = "".join(part.read_text(encoding="ascii").strip() for part in parts)
    archive = base64.b64decode(encoded, validate=True)
    require(hashlib.sha256(archive).hexdigest() == ARCHIVE_SHA256, "Sweden v6 transfer archive SHA-256 mismatch")

    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = {Path(name).name for name in bundle.namelist() if not name.endswith("/")}
        require(set(EXPECTED) <= names, f"Sweden v6 archive incomplete: {sorted(names)}")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name in EXPECTED:
            raw = bundle.read(name)
            validate_webp(name, raw)
            (OUTPUT / name).write_bytes(raw)

    data = json.loads(COUNTRY.read_text(encoding="utf-8"))
    require(data.get("slug") == "sweden", "Wrong country JSON")
    data["hero"]["image"] = "assets/images/sweden/v6/hero-grinda.webp"
    scenes = data.get("scenes") or []
    require({scene.get("id") for scene in scenes} == set(SCENE_FILES), "Unexpected Sweden scene set")
    for scene in scenes:
        scene["image"] = f"assets/images/sweden/v6/{SCENE_FILES[scene['id']]}"
    COUNTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    serialized = COUNTRY.read_text(encoding="utf-8")
    require(serialized.count("assets/images/sweden/v6/") == 9, "Sweden JSON does not reference exactly nine v6 artworks")
    for old in ("/v1/", "/v2/", "/v3/", "/v4/", "/v5/"):
        require(f"assets/images/sweden{old}" not in serialized, f"Old Sweden artwork reference remains: {old}")
    require(".b64" not in serialized and ".parts.json" not in serialized, "Temporary encoded source leaked into Sweden JSON")

    shutil.rmtree(TRANSFER)
    READY.unlink(missing_ok=True)
    TEST_ARTIFACT.unlink(missing_ok=True)
    print("Sweden v6 materialized: approved Hero + 8 scenes verified, decoded, connected, and temporary transfer removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
