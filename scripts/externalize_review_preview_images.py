#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


def rewrite_value(value: Any, image_origin: str) -> Any:
    if isinstance(value, str):
        clean = value.split("?", 1)[0]
        if clean.startswith("assets/images/"):
            suffix = value[len(clean):]
            return urljoin(image_origin, clean) + suffix
        return value
    if isinstance(value, dict):
        return {key: rewrite_value(item, image_origin) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_value(item, image_origin) for item in value]
    return value


def contains_relative_image(value: Any) -> bool:
    if isinstance(value, str):
        return value.split("?", 1)[0].startswith("assets/images/")
    if isinstance(value, dict):
        return any(contains_relative_image(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_relative_image(item) for item in value)
    return False


def externalize(dist: Path, image_origin: str, site_url: str) -> None:
    image_origin = image_origin.rstrip("/") + "/"
    site_url = site_url.rstrip("/") + "/"

    for path in sorted((dist / "data").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload = rewrite_value(payload, image_origin)
        if contains_relative_image(payload):
            raise ValueError(f"Relative image reference remained in {path}")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_prefix = urljoin(site_url, "assets/images/")
    external_prefix = urljoin(image_origin, "assets/images/")
    for path in sorted(dist.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        text = text.replace(local_prefix, external_prefix)
        path.write_text(text, encoding="utf-8")

    image_dir = dist / "assets" / "images"
    if image_dir.exists():
        shutil.rmtree(image_dir)

    for path in sorted((dist / "data").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if contains_relative_image(payload):
            raise ValueError(f"Preview JSON still depends on packaged Country images: {path}")

    for path in sorted(dist.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        if local_prefix in text:
            raise ValueError(f"Preview HTML still points at removed packaged images: {path}")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp) / "dist"
        data = dist / "data" / "countries"
        images = dist / "assets" / "images" / "alpha" / "approved"
        page = dist / "countries" / "alpha"
        data.mkdir(parents=True)
        images.mkdir(parents=True)
        page.mkdir(parents=True)
        (images / "hero.webp").write_bytes(b"preview")
        (data / "alpha.json").write_text(
            json.dumps({"hero": {"image": "assets/images/alpha/approved/hero.webp?v=x"}}),
            encoding="utf-8",
        )
        site_url = "https://example.test/reviews/alpha/"
        image_origin = "https://raw.example.test/commit/"
        (page / "index.html").write_text(
            f'<link rel="preload" href="{site_url}assets/images/alpha/approved/hero.webp">',
            encoding="utf-8",
        )
        externalize(dist, image_origin, site_url)
        payload = json.loads((data / "alpha.json").read_text(encoding="utf-8"))
        assert payload["hero"]["image"].startswith(image_origin)
        assert not (dist / "assets" / "images").exists()
        assert image_origin in (page / "index.html").read_text(encoding="utf-8")
    print("Review preview image externalization self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--image-origin")
    parser.add_argument("--site-url")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.image_origin or not args.site_url:
        parser.error("--image-origin and --site-url are required unless --self-test is used")
    externalize(Path(args.dist), args.image_origin, args.site_url)
    print(f"Externalized preview imagery to immutable origin: {args.image_origin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
