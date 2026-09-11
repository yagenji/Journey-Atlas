#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--image-origin", required=True)
    parser.add_argument("--site-url", required=True)
    args = parser.parse_args()
    externalize(Path(args.dist), args.image_origin, args.site_url)
    print(f"Externalized preview imagery to immutable origin: {args.image_origin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
