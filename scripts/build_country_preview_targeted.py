#!/usr/bin/env python3
"""Build a fast local preview package for specific JOURNEY ATLAS Country pages.

This script is intentionally CI/review-only. It does NOT replace the production
Cloudflare build. It generates only the requested Country pages, packages only
their Country JSON plus referenced Country imagery, and copies shared runtime
assets needed by the browser QA.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

import build_site

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
COUNTRY_DIR = ROOT / "data" / "countries"
RUNTIME_DATA_FILES = [
    "atlas-destinations.json",
    "atlas-destinations-editorial.json",
    "region-taxonomy.json",
    "theme-taxonomy.json",
]
STATIC_PAGE_DIRS = ["about", "faq", "privacy"]


def parse_slugs(raw: str) -> list[str]:
    slugs = []
    seen: set[str] = set()
    for value in raw.replace(" ", ",").split(","):
        slug = value.strip()
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    if not slugs:
        raise ValueError("At least one target slug is required")
    return slugs


def collect_image_refs(value: object, refs: set[str]) -> None:
    if isinstance(value, str):
        clean = value.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("assets/images/"):
            refs.add(clean)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_image_refs(item, refs)
        return
    if isinstance(value, list):
        for item in value:
            collect_image_refs(item, refs)


def version_runtime_image_refs(value: object) -> object:
    if isinstance(value, str):
        clean = value.split("?", 1)[0]
        if clean.startswith("assets/images/") and "/approved/" in clean:
            return build_site.versioned_approved_image(clean)
        return value
    if isinstance(value, dict):
        return {key: version_runtime_image_refs(item) for key, item in value.items()}
    if isinstance(value, list):
        return [version_runtime_image_refs(item) for item in value]
    return value


def copy_file(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required preview file missing: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def write_json(payload: object, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def target_destinations(slugs: list[str]) -> tuple[list[dict[str, Any]], set[str]]:
    registries = build_site.load_registries()
    destinations = {item["slug"]: item for item in build_site.all_destinations(registries)}
    published = {item["slug"] for item in build_site.published_destinations(registries)}
    selected: list[dict[str, Any]] = []
    for slug in slugs:
        item = destinations.get(slug)
        if item is None:
            raise ValueError(f"Unknown target slug: {slug}")
        country_path = COUNTRY_DIR / f"{slug}.json"
        if not country_path.exists():
            raise FileNotFoundError(f"Country JSON missing: {country_path.relative_to(ROOT)}")
        data = json.loads(country_path.read_text(encoding="utf-8"))
        if data.get("schemaVersion") != 2:
            raise ValueError(f"Target Country is not schemaVersion=2: {slug}")
        selected.append(item)
    return selected, published


def build_target_pages(slugs: list[str]) -> None:
    selected, published = target_destinations(slugs)
    build_site.clean_generated_country_pages()
    build_site.bundle_css("assets/css/country.css", build_site.COUNTRY_CSS_SOURCES)
    build_site.prepare_app_js()
    build_site.prepare_generic_country_page()

    urls: list[str] = []
    for item in selected:
        canonical = build_site.generate_country_page(item, published=item["slug"] in published)
        if item["slug"] in published:
            urls.append(canonical)
    build_site.generate_sitemap(urls)


def package_shared_runtime() -> None:
    for name in ("index.html", "404.html", "_redirects", "sitemap.xml", "robots.txt"):
        copy_file(ROOT / name, DIST / name)
    for page in STATIC_PAGE_DIRS:
        source = ROOT / page
        if (source / "index.html").exists():
            copy_tree(source, DIST / page)

    assets = ROOT / "assets"
    for child in assets.iterdir():
        if child.name == "images":
            continue
        destination = DIST / "assets" / child.name
        if child.is_dir():
            copy_tree(child, destination)
        else:
            copy_file(child, destination)


def package_runtime_data(slugs: list[str]) -> set[str]:
    refs: set[str] = set()
    for name in RUNTIME_DATA_FILES:
        source = ROOT / "data" / name
        payload = json.loads(source.read_text(encoding="utf-8"))
        write_json(version_runtime_image_refs(payload), DIST / "data" / name)

    for slug in slugs:
        source = COUNTRY_DIR / f"{slug}.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        collect_image_refs(payload, refs)
        write_json(version_runtime_image_refs(payload), DIST / "data" / "countries" / source.name)
        copy_tree(ROOT / "countries" / slug, DIST / "countries" / slug)
    return refs


def package_target_images(refs: set[str]) -> None:
    for relative in sorted(refs):
        source = ROOT / relative
        if not source.exists():
            raise FileNotFoundError(f"Referenced target image missing: {relative}")
        copy_file(source, DIST / relative)


def write_preview_metadata(slugs: list[str]) -> None:
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n",
        encoding="utf-8",
    )
    write_json(
        {
            "mode": "TARGETED_COUNTRY_PREVIEW",
            "targets": slugs,
            "buildVersion": build_site.BUILD_VERSION,
            "siteUrl": build_site.SITE_URL,
        },
        DIST / "preview-build-meta.json",
    )


def validate_preview(slugs: list[str], refs: set[str]) -> None:
    packaged_country_json = sorted(path.stem for path in (DIST / "data" / "countries").glob("*.json"))
    if packaged_country_json != sorted(slugs):
        raise ValueError(
            f"Targeted preview packaged unexpected Country JSON: expected={sorted(slugs)} found={packaged_country_json}"
        )
    packaged_pages = sorted(path.parent.name for path in (DIST / "countries").glob("*/index.html"))
    if packaged_pages != sorted(slugs):
        raise ValueError(
            f"Targeted preview generated unexpected Country pages: expected={sorted(slugs)} found={packaged_pages}"
        )
    missing = [relative for relative in sorted(refs) if not (DIST / relative).exists()]
    if missing:
        raise FileNotFoundError(f"Targeted preview image set incomplete: {missing}")

    for slug in slugs:
        page = DIST / "countries" / slug / "index.html"
        if not page.exists():
            raise FileNotFoundError(f"Target Country preview page missing: {slug}")
        payload = json.loads((DIST / "data" / "countries" / f"{slug}.json").read_text(encoding="utf-8"))
        hero = payload.get("hero", {}).get("image", "")
        if isinstance(hero, str) and hero.startswith("assets/images/"):
            clean = hero.split("?", 1)[0]
            if not (DIST / clean).exists():
                raise FileNotFoundError(f"Target Country Hero missing from preview: {slug}: {clean}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build only the requested Country preview package")
    parser.add_argument(
        "--slugs",
        default=os.environ.get("TARGET_SLUGS", ""),
        help="Comma-separated Country slugs (defaults to TARGET_SLUGS)",
    )
    args = parser.parse_args()
    slugs = parse_slugs(args.slugs)

    if DIST.exists():
        shutil.rmtree(DIST)
    build_target_pages(slugs)
    DIST.mkdir(parents=True, exist_ok=True)
    package_shared_runtime()
    refs = package_runtime_data(slugs)
    package_target_images(refs)
    write_preview_metadata(slugs)
    validate_preview(slugs, refs)

    file_count = sum(1 for path in DIST.rglob("*") if path.is_file())
    size_bytes = sum(path.stat().st_size for path in DIST.rglob("*") if path.is_file())
    print(
        f"Targeted Country preview ready: {', '.join(slugs)}; "
        f"{len(refs)} referenced image(s); {file_count} files; {size_bytes / (1024 * 1024):.1f} MiB."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
