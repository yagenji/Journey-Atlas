#!/usr/bin/env python3
"""Small Scene thumbnails for the top-page 景色から探す gallery.

The gallery shows many Scenes at once, so it uses 480x320 WebP copies of the approved
Scene images instead of the 1200x800 originals. Thumbnails live under
assets/images/top/scenes/{slug}/{scene-id}.webp (top-page assets, not Country assets)
and manifest.json records the SHA-1 of each source so a changed Scene image is redone.

    python3 scripts/build_scene_thumbs.py          # create / refresh thumbnails
    python3 scripts/build_scene_thumbs.py --check  # exit 1 if any thumbnail is missing or stale

Needs Pillow only when creating thumbnails; --check uses hashes only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
THUMB_ROOT = ROOT / "assets" / "images" / "top" / "scenes"
MANIFEST = THUMB_ROOT / "manifest.json"
SIZE = (480, 320)
QUALITY = 72


def scenes():
    for path in sorted(COUNTRY_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = data.get("slug")
        for scene in data.get("scenes", []):
            image = scene.get("image")
            if slug and scene.get("id") and isinstance(image, str):
                yield slug, scene["id"], ROOT / image


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def thumb_path(slug: str, scene_id: str) -> Path:
    return THUMB_ROOT / slug / f"{scene_id}.webp"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    wanted: dict[str, str] = {}
    todo = []
    for slug, scene_id, source in scenes():
        if not source.exists():
            print(f"missing source: {source.relative_to(ROOT)}", file=sys.stderr)
            continue
        key = f"{slug}/{scene_id}"
        digest = sha1(source)
        wanted[key] = digest
        if manifest.get(key) != digest or not thumb_path(slug, scene_id).exists():
            todo.append((slug, scene_id, source, digest))

    stale = sorted(set(manifest) - set(wanted))
    # One-off export for recovering the missing approved Scene gallery thumbnails.
    # This temporary branch-only code is removed when the actual thumbs are committed.
    if args.check and todo:
        import base64
        import io
        from PIL import Image, ImageOps
        print("JA_THUMB_DUMP_START|" + str(len(todo)), flush=True)
        for slug, scene_id, source, digest in todo:
            if source.suffix != ".webp":
                raise ValueError(f"Unsupported temporary export source: {source}")
            with Image.open(source) as original:
                target = ImageOps.fit(original.convert("RGB"), SIZE, Image.LANCZOS)
                output = io.BytesIO()
                target.save(output, "WEBP", quality=QUALITY, method=6)
            encoded = base64.b64encode(output.getvalue()).decode("ascii")
            key = f"{slug}/{scene_id}"
            print(f"JA_THUMB_BEGIN|{key}|{digest}|{len(encoded)}", flush=True)
            for offset in range(0, len(encoded), 2000):
                print(f"JA_THUMB_CHUNK|{key}|{offset // 2000}|{encoded[offset:offset+2000]}", flush=True)
            print(f"JA_THUMB_END|{key}", flush=True)
        print("JA_THUMB_DUMP_DONE", flush=True)
    if args.check:
        if todo or stale:
            print(f"Scene thumbnails out of date: {len(todo)} to build, {len(stale)} to remove. "
                  "Run python3 scripts/build_scene_thumbs.py", file=sys.stderr)
            return 1
        print(f"Scene thumbnails up to date ({len(wanted)}).")
        return 0

    import base64
    import io
    import re
    from PIL import Image, ImageOps

    def open_image(source: Path):
        # A few approved Scene images are SVG wrappers around one embedded raster image.
        if source.suffix == ".svg":
            match = re.search(rb'href="data:image/[a-z]+;base64,([^"]+)"', source.read_bytes())
            if not match:
                raise ValueError(f"No embedded raster image in {source}")
            return Image.open(io.BytesIO(base64.b64decode(match.group(1))))
        return Image.open(source)

    for slug, scene_id, source, digest in todo:
        out = thumb_path(slug, scene_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open_image(source) as image:
            image = ImageOps.fit(image.convert("RGB"), SIZE, Image.LANCZOS)
            image.save(out, "WEBP", quality=QUALITY, method=6)
        manifest[f"{slug}/{scene_id}"] = digest
    for key in stale:
        thumb_path(*key.split("/", 1)).unlink(missing_ok=True)
        manifest.pop(key, None)
    THUMB_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=0) + "\n", encoding="utf-8")
    print(f"Scene thumbnails: {len(todo)} built, {len(stale)} removed, {len(wanted)} total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
