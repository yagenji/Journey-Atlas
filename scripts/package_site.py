#!/usr/bin/env python3
"""Package the built JOURNEY ATLAS site into a clean static deploy directory.

Run scripts/build_site.py first. This packager intentionally excludes authoring
files, encoded source chunks, and the generic draft country route. Mature
schemaVersion=2 country pages are shipped for direct noindex review, while
atlasPublished=true still controls discovery, indexing and sitemap inclusion.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA_DIR = ROOT / "data"
COUNTRY_DIR = DATA_DIR / "countries"
REGISTRY_PATHS = [
    DATA_DIR / "atlas-destinations.json",
    DATA_DIR / "atlas-destinations-editorial.json",
]
ROOT_FILES = ["index.html", "404.html", "_redirects", "sitemap.xml", "robots.txt"]
STATIC_PAGE_DIRS = ["faq", "privacy"]
RUNTIME_DATA_FILES = [
    "atlas-destinations.json",
    "atlas-destinations-editorial.json",
    "region-taxonomy.json",
    "theme-taxonomy.json",
]


def published_slugs() -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for path in REGISTRY_PATHS:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            if not item.get("atlasPublished"):
                continue
            slug = item.get("slug")
            if not slug:
                raise ValueError(f"Published destination without slug in {path.name}")
            if slug in seen:
                raise ValueError(f"Duplicate published slug: {slug}")
            seen.add(slug)
            slugs.append(slug)
    return slugs


def reviewable_slugs() -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for path in REGISTRY_PATHS:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            slug = item.get("slug")
            if not slug or slug in seen:
                continue
            country_path = COUNTRY_DIR / f"{slug}.json"
            if not country_path.exists():
                continue
            data = json.loads(country_path.read_text(encoding="utf-8"))
            if data.get("schemaVersion") == 2:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def ignore_asset_sources(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name.endswith(".b64") or name.endswith(".parts.json") or name.endswith("-parts"):
            ignored.add(name)
    return ignored


def copy_path(source: Path, destination: Path, *, ignore=None) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, ignore=ignore)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def collect_image_refs(value: object, refs: set[str]) -> None:
    if isinstance(value, str):
        if value.startswith("assets/images/"):
            refs.add(value)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_image_refs(item, refs)
        return
    if isinstance(value, list):
        for item in value:
            collect_image_refs(item, refs)


def production_image_paths(slugs: list[str]) -> set[str]:
    refs: set[str] = set()

    # Top-page visual assets are direct runtime dependencies.
    top_root = ROOT / "assets" / "images" / "top"
    if top_root.exists():
        for path in top_root.rglob("*"):
            if path.is_file():
                refs.add(path.relative_to(ROOT).as_posix())

    # Destination registries may reference card art before a Country Page is reviewable.
    for registry_path in REGISTRY_PATHS:
        collect_image_refs(json.loads(registry_path.read_text(encoding="utf-8")), refs)

    # Reviewable Country JSON is the source of truth for Hero, Scene and Map assets.
    for slug in slugs:
        country_path = COUNTRY_DIR / f"{slug}.json"
        collect_image_refs(json.loads(country_path.read_text(encoding="utf-8")), refs)

    return refs


def prune_unreferenced_images(slugs: list[str]) -> set[str]:
    allowed = production_image_paths(slugs)
    image_root = DIST / "assets" / "images"
    if not image_root.exists():
        raise FileNotFoundError(f"Packaged image root missing: {image_root}")

    for path in sorted(image_root.rglob("*"), reverse=True):
        if path.is_file():
            relative = path.relative_to(DIST).as_posix()
            if relative not in allowed:
                path.unlink()
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    return allowed


def package_data(slugs: list[str]) -> None:
    target = DIST / "data"
    target.mkdir(parents=True, exist_ok=True)

    # Only browser/runtime data is shipped. Authoring-only source JSON and
    # map-generation inputs stay in the repository but never enter production.
    for name in RUNTIME_DATA_FILES:
        source = DATA_DIR / name
        if not source.exists():
            raise FileNotFoundError(f"Runtime data missing: {source}")
        copy_path(source, target / source.name)

    countries_target = target / "countries"
    countries_target.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        source = COUNTRY_DIR / f"{slug}.json"
        if not source.exists():
            raise FileNotFoundError(f"Reviewable country JSON missing: {source}")
        shutil.copy2(source, countries_target / source.name)


def package_country_pages(slugs: list[str]) -> None:
    for slug in slugs:
        source = ROOT / "countries" / slug
        if not (source / "index.html").exists():
            raise FileNotFoundError(f"Reviewable static country page missing: {source / 'index.html'}")
        shutil.copytree(source, DIST / "countries" / slug)


def write_cloudflare_headers() -> None:
    headers = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/*.html
  Cache-Control: public, max-age=0, must-revalidate

/data/*
  Cache-Control: public, max-age=0, must-revalidate

/assets/css/*
  Cache-Control: public, max-age=86400

/assets/js/*
  Cache-Control: public, max-age=86400

/assets/icons/*
  Cache-Control: public, max-age=86400

/assets/images/*
  Cache-Control: public, max-age=0, must-revalidate
"""
    (DIST / "_headers").write_text(headers, encoding="utf-8")


def validate_package(slugs: list[str], allowed_images: set[str]) -> None:
    for relative in ROOT_FILES:
        if not (DIST / relative).exists():
            raise FileNotFoundError(f"Packaged root file missing: {relative}")
    for relative in STATIC_PAGE_DIRS:
        if not (DIST / relative / "index.html").exists():
            raise FileNotFoundError(f"Packaged static page missing: {relative}/index.html")
    if (DIST / "country.html").exists():
        raise ValueError("Generic draft country route must not be shipped to production")
    if (DIST / "scripts").exists() or (DIST / ".github").exists():
        raise ValueError("Authoring or CI files leaked into production package")

    allowed_data = set(RUNTIME_DATA_FILES) | {"countries"}
    unexpected_data = sorted(path.name for path in (DIST / "data").iterdir() if path.name not in allowed_data)
    if unexpected_data:
        raise ValueError(f"Unexpected production data file(s): {unexpected_data}")

    packaged_images = {
        path.relative_to(DIST).as_posix()
        for path in (DIST / "assets" / "images").rglob("*")
        if path.is_file()
    }
    if packaged_images != allowed_images:
        missing = sorted(allowed_images - packaged_images)
        unexpected = sorted(packaged_images - allowed_images)
        raise ValueError(
            f"Production image set mismatch. missing={missing}, unexpected={unexpected}"
        )

    packaged = sorted(path.stem for path in (DIST / "data" / "countries").glob("*.json"))
    if packaged != sorted(slugs):
        raise ValueError(f"Packaged country JSON mismatch: expected {sorted(slugs)}, found {packaged}")


def main() -> int:
    published = published_slugs()
    slugs = reviewable_slugs()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for relative in ROOT_FILES:
        source = ROOT / relative
        if not source.exists():
            raise FileNotFoundError(f"Build output missing: {source}")
        shutil.copy2(source, DIST / relative)

    for relative in STATIC_PAGE_DIRS:
        source = ROOT / relative
        if not (source / "index.html").exists():
            raise FileNotFoundError(f"Static page missing: {source / 'index.html'}")
        copy_path(source, DIST / relative)

    copy_path(ROOT / "assets", DIST / "assets", ignore=ignore_asset_sources)
    allowed_images = prune_unreferenced_images(slugs)
    package_data(slugs)
    package_country_pages(slugs)
    write_cloudflare_headers()
    validate_package(slugs, allowed_images)

    file_count = sum(1 for path in DIST.rglob("*") if path.is_file())
    size_bytes = sum(path.stat().st_size for path in DIST.rglob("*") if path.is_file())
    print(
        f"Packaged {len(slugs)} reviewable country page(s) "
        f"({len(published)} published) into dist/: "
        f"{file_count} files, {size_bytes / (1024 * 1024):.1f} MiB."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
