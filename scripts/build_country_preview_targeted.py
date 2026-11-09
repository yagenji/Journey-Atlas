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
import unicodedata
from pathlib import Path
from typing import Any

import build_site
import package_site
from build_region_pages import generate_region_pages

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
COUNTRY_DIR = ROOT / "data" / "countries"
RUNTIME_DATA_FILES = [
    "atlas-destinations.json",
    "region-taxonomy.json",
    "theme-taxonomy.json",
    "map-data-sources.json",
    "scene-origins.json",
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


def include_pager_neighbors(slugs: list[str]) -> list[str]:
    """Package the adjacent pages and Heroes rendered/prefetched by atlas-pager.js.

    Keep the requested QA targets separate from these runtime dependencies. Order
    follows atlas-order.js: taxonomy chapters, then English names within each.
    """
    registry = json.loads((ROOT / "data/atlas-destinations.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((ROOT / "data/region-taxonomy.json").read_text(encoding="utf-8"))
    by_iso = {
        item["iso2"]: item for item in registry.get("destinations", [])
        if item.get("atlasPublished") and item.get("href")
    }
    pages: list[str] = []
    used: set[str] = set()
    for region in taxonomy.get("regions", []):
        for group in region.get("subregions") or [region]:
            items = [by_iso[iso] for iso in group.get("iso2", [])
                     if iso in by_iso and by_iso[iso]["slug"] not in used]
            items.sort(key=lambda item: "".join(
                char for char in unicodedata.normalize("NFKD", item["nameEn"]).casefold()
                if not unicodedata.combining(char)
            ))
            for item in items:
                pages.append(item["slug"])
                used.add(item["slug"])
    expanded = list(slugs)
    for slug in slugs:
        if slug in pages and len(pages) > 1:
            at = pages.index(slug)
            for neighbor in (pages[(at - 1) % len(pages)], pages[(at + 1) % len(pages)]):
                if neighbor not in expanded:
                    expanded.append(neighbor)
    return expanded


def version_runtime_image_refs(value: object) -> object:
    if isinstance(value, str):
        clean = value.split("?", 1)[0]
        if clean.startswith("assets/images/"):
            resolved = package_site.resolve_source_image_ref(clean)
            if "/approved/" in resolved:
                return build_site.versioned_approved_image(resolved)
            return resolved
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
    urls.extend(generate_region_pages(site_url=build_site.SITE_URL, version=build_site.BUILD_VERSION, parents=set(slugs)))
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

    # A targeted preview needs real, matching recommendations from at least six
    # other Country families. Keeping only the target Countries in this index
    # leaves Region pages with too few cards (and gives misleading browser QA).
    # Include a small, image-complete subset of published matching Scenes instead
    # of copying the entire global index and its >1,000 thumbnails.
    scene_index = json.loads((ROOT / "data" / "top-scene-index.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "atlas-destinations.json").read_text(encoding="utf-8"))
    published = {item["slug"] for item in registry["destinations"]
                 if item.get("atlasPublished") and item.get("href")}
    # The live similar-scenes UI needs up to six *distinct* other Country families\n    # per page. A fixed first-N subset can leave Regions with only 3-4 cards even\n    # though the full scene index has ample matching Scenes. Build a minimal\n    # image-complete support pool for every target Country and its Regions.\n    page_type_sets: list[set[str]] = []\n    for slug in slugs:\n        country = json.loads((COUNTRY_DIR / f"{slug}.json").read_text(encoding="utf-8"))\n        family_pages = [country] + [\n            json.loads(path.read_text(encoding="utf-8"))\n            for path in sorted((ROOT / "data" / "regions" / slug).glob("*.json"))\n        ]\n        for page in family_pages:\n            page_types = {\n                type_id\n                for entry in [page.get("hero", {}), *page.get("scenes", [])]\n                for type_id in entry.get("sceneTypes", [])\n            }\n            if page_types:\n                page_type_sets.append(page_types)\n\n    support: dict[str, list] = {}\n    for page_types in page_type_sets:\n        matched_families = 0\n        for slug, rows in scene_index.get("countries", {}).items():\n            if slug in slugs or slug not in published:\n                continue\n            match = next((row for row in rows\n                          if len(row) > 2 and page_types.intersection(row[2])), None)\n            if match is None:\n                continue\n            selected = support.setdefault(slug, [])\n            if not any(page_types.intersection(row[2]) for row in selected):\n                selected.append(match)\n            matched_families += 1\n            if matched_families >= 6:\n                break\n    scene_index["countries"] = {
        **{slug: rows for slug, rows in scene_index.get("countries", {}).items() if slug in slugs},
        **support,
    }
    for key in ("heroes", "heroTypes"):
        scene_index[key] = {slug: value for slug, value in scene_index.get(key, {}).items() if slug in slugs}
    scene_index["regionHeroes"] = [row for row in scene_index.get("regionHeroes", []) if row.get("parentSlug") in slugs]
    write_json(scene_index, DIST / "data" / "top-scene-index.json")
    for slug, rows in scene_index["countries"].items():
        if slug in support:
            for scene_id, *_ in rows:
                copy_file(
                    ROOT / "assets" / "images" / "top" / "scenes" / slug / f"{scene_id}.webp",
                    DIST / "assets" / "images" / "top" / "scenes" / slug / f"{scene_id}.webp",
                )
        else:
            scene_dir = ROOT / "assets" / "images" / "top" / "scenes" / slug
            if scene_dir.is_dir():
                copy_tree(scene_dir, DIST / "assets" / "images" / "top" / "scenes" / slug)

    for slug in slugs:
        source = COUNTRY_DIR / f"{slug}.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        collect_image_refs(payload, refs)
        write_json(version_runtime_image_refs(payload), DIST / "data" / "countries" / source.name)
        copy_tree(ROOT / "countries" / slug, DIST / "countries" / slug)
        # Country-style regional links reference a sibling Country's approved Hero.
        # Include only that image, not the sibling's entire page or image set.
        for region in payload.get("regionDiscoveries", []):
            if region.get("kind") != "country":
                continue
            child_slug = region.get("slug", "")
            if not isinstance(child_slug, str) or not child_slug.replace("-", "").isalnum():
                continue
            child_path = COUNTRY_DIR / f"{child_slug}.json"
            if child_path.exists():
                child_data = json.loads(child_path.read_text(encoding="utf-8"))
                collect_image_refs(child_data.get("hero", {}), refs)
        # Region imagery is a separate editorial layer, not part of Country JSON.
        for region_path in sorted((ROOT / "data" / "regions" / slug).glob("*.json")):
            collect_image_refs(json.loads(region_path.read_text(encoding="utf-8")), refs)
    return refs


def package_target_images(refs: set[str]) -> None:
    for relative in sorted(refs):
        if relative.endswith(".parts.json"):
            payload, output = package_site.decode_parts_manifest(relative)
            destination = DIST / output
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            continue
        copy_file(ROOT / relative, DIST / relative)


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
    resolved_refs = {package_site.resolve_source_image_ref(relative) for relative in refs}
    missing = [relative for relative in sorted(resolved_refs) if not (DIST / relative).exists()]
    if missing:
        raise FileNotFoundError(f"Targeted preview image set incomplete: {missing}")

    for slug in slugs:
        # All requested Region reviews must be present and carry their referenced assets.
        for region_path in sorted((ROOT / "data" / "regions" / slug).glob("*.json")):
            region = json.loads(region_path.read_text(encoding="utf-8"))
            region_page = DIST / "countries" / slug / region["slug"] / "index.html"
            if not region_page.is_file():
                raise FileNotFoundError(f"Target Region preview page missing: {region_page}")
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
    packaged_slugs = include_pager_neighbors(slugs)

    if DIST.exists():
        shutil.rmtree(DIST)
    build_target_pages(packaged_slugs)
    DIST.mkdir(parents=True, exist_ok=True)
    package_shared_runtime()
    refs = package_runtime_data(packaged_slugs)
    package_target_images(refs)
    write_preview_metadata(slugs)
    validate_preview(packaged_slugs, refs)

    file_count = sum(1 for path in DIST.rglob("*") if path.is_file())
    size_bytes = sum(path.stat().st_size for path in DIST.rglob("*") if path.is_file())
    print(
        f"Targeted Country preview ready: {', '.join(slugs)}; "
        f"{len(refs)} referenced image(s); {file_count} files; {size_bytes / (1024 * 1024):.1f} MiB."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
