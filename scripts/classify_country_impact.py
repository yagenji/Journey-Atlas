#!/usr/bin/env python3
"""Classify JOURNEY ATLAS change impact for fast, risk-based QA."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    "data/atlas-destinations.json",
    "data/atlas-destinations-editorial.json",
]
THEME_PATH = "data/theme-taxonomy.json"
STATUS_PATH = "data/country-renewal-status.json"

COUNTRY_SHARED_FILES = {
    "country.html",
    "assets/js/app.js",
    "assets/css/style.css",
    "assets/css/country.css",
    "assets/css/atlas-overrides.css",
    "assets/css/country-fixes.css",
    "assets/css/country-layout-final.css",
    "assets/css/country-atlas-depth.css",
    "assets/css/country-polish.css",
    "assets/css/country-refine.css",
    "assets/css/country-template-v2.css",
    "assets/css/country-icon-system.css",
    "assets/css/country-trivia.css",
    "assets/css/country-discovery-v3.css",
    "assets/css/photo-credits.css",
    "assets/css/site-unify.css",
    "assets/css/site-footer.css",
    "scripts/build_site.py",
    "scripts/package_site.py",
    "scripts/build_cloudflare.py",
}

QA_SHARED_FILES = {
    "scripts/qa_published_browser.py",
    "scripts/classify_country_impact.py",
    ".github/workflows/browser-country-qa.yml",
}

PRODUCTION_PREFIXES = (
    "assets/css/",
    "assets/js/",
    "assets/images/",
    "assets/icons/",
    "data/countries/",
    "faq/",
    "privacy/",
)

PRODUCTION_EXACT = {
    "index.html",
    "country.html",
    "404.html",
    "_redirects",
    "data/theme-taxonomy.json",
    "data/atlas-destinations.json",
    "data/atlas-destinations-editorial.json",
    "scripts/build_site.py",
    "scripts/package_site.py",
    "scripts/build_cloudflare.py",
}

COUNTRY_JSON_RE = re.compile(r"^data/countries/([^/]+)\.json$")
COUNTRY_IMAGE_RE = re.compile(r"^assets/images/([^/]+)/")


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def changed_files(base: str, head: str) -> list[str]:
    try:
        out = run_git("diff", "--name-only", f"{base}...{head}")
    except Exception:
        out = run_git("diff", "--name-only", base, head)
    return sorted({line.strip() for line in out.splitlines() if line.strip()})


def show_json(ref: str, path: str) -> dict:
    try:
        raw = run_git("show", f"{ref}:{path}")
    except Exception:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def current_json(path: str) -> dict:
    p = ROOT / path
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def registry_rows(payload: dict) -> dict[str, dict]:
    return {
        row["slug"]: row
        for row in payload.get("destinations", [])
        if isinstance(row, dict) and isinstance(row.get("slug"), str)
    }


def changed_registry_slugs(base: str, head: str, path: str) -> set[str]:
    before = registry_rows(show_json(base, path))
    after = registry_rows(show_json(head, path))
    slugs = set(before) | set(after)
    return {slug for slug in slugs if before.get(slug) != after.get(slug)}


def taxonomy_assignments(payload: dict) -> dict[str, tuple[str, ...]]:
    assignments: dict[str, set[str]] = {}
    for theme in payload.get("themes", []):
        if not isinstance(theme, dict):
            continue
        theme_id = theme.get("id")
        if not isinstance(theme_id, str):
            continue
        for slug in theme.get("examples", []):
            if isinstance(slug, str):
                assignments.setdefault(slug, set()).add(theme_id)
    return {slug: tuple(sorted(ids)) for slug, ids in assignments.items()}


def changed_taxonomy_slugs(base: str, head: str) -> set[str]:
    before = taxonomy_assignments(show_json(base, THEME_PATH))
    after = taxonomy_assignments(show_json(head, THEME_PATH))
    slugs = set(before) | set(after)
    return {slug for slug in slugs if before.get(slug) != after.get(slug)}


def status_rows(payload: dict) -> dict[str, dict]:
    return {
        row["slug"]: row
        for row in payload.get("countries", [])
        if isinstance(row, dict) and isinstance(row.get("slug"), str)
    }


def changed_status_slugs(base: str, head: str) -> set[str]:
    before = status_rows(show_json(base, STATUS_PATH))
    after = status_rows(show_json(head, STATUS_PATH))
    slugs = set(before) | set(after)
    return {slug for slug in slugs if before.get(slug) != after.get(slug)}


def is_production_file(path: str) -> bool:
    if path in PRODUCTION_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PRODUCTION_PREFIXES)


def load_current_registry() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in REGISTRY_PATHS:
        payload = current_json(path)
        rows.update(registry_rows(payload))
    return rows


def classify(base: str, head: str) -> dict:
    files = changed_files(base, head)
    target_slugs: set[str] = set()
    browser_scope = "none"

    for path in files:
        match = COUNTRY_JSON_RE.match(path)
        if match:
            target_slugs.add(match.group(1))
            continue
        match = COUNTRY_IMAGE_RE.match(path)
        if match and (COUNTRY_DIR / f"{match.group(1)}.json").exists():
            target_slugs.add(match.group(1))

    if any(path in REGISTRY_PATHS for path in files):
        for path in REGISTRY_PATHS:
            if path in files:
                target_slugs |= changed_registry_slugs(base, head, path)

    if THEME_PATH in files:
        target_slugs |= changed_taxonomy_slugs(base, head)

    if STATUS_PATH in files:
        target_slugs |= changed_status_slugs(base, head)

    if any(path in COUNTRY_SHARED_FILES or path in QA_SHARED_FILES for path in files):
        browser_scope = "all"
    elif target_slugs:
        browser_scope = "targeted"

    production_changed = any(is_production_file(path) for path in files)

    registry = load_current_registry()
    published: list[str] = []
    reviewable: list[str] = []

    if browser_scope == "targeted":
        for slug in sorted(target_slugs):
            row = registry.get(slug)
            country_path = COUNTRY_DIR / f"{slug}.json"
            if not row or not country_path.exists():
                continue
            try:
                country = json.loads(country_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if row.get("atlasPublished"):
                published.append(slug)
            elif country.get("schemaVersion") == 2:
                reviewable.append(slug)

    if browser_scope == "targeted" and not published and not reviewable:
        browser_scope = "none"

    result = {
        "base": base,
        "head": head,
        "changedFiles": files,
        "productionChanged": production_changed,
        "browserScope": browser_scope,
        "targetSlugs": sorted(target_slugs),
        "publishedSlugs": published,
        "reviewableSlugs": reviewable,
    }
    return result


def write_github_output(path: Path, result: dict) -> None:
    values = {
        "production_changed": str(result["productionChanged"]).lower(),
        "browser_scope": result["browserScope"],
        "target_slugs": ",".join(result["targetSlugs"]),
        "published_slugs": ",".join(result["publishedSlugs"]),
        "reviewable_slugs": ",".join(result["reviewableSlugs"]),
    }
    with path.open("a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def self_test() -> int:
    assert COUNTRY_JSON_RE.match("data/countries/ukraine.json").group(1) == "ukraine"
    assert COUNTRY_IMAGE_RE.match("assets/images/czechia/approved/a.webp").group(1) == "czechia"
    assert is_production_file("data/countries/ukraine.json")
    assert is_production_file("assets/css/country.css")
    assert not is_production_file("ops/country-production/ukraine.json")
    assert not is_production_file("docs/COUNTRY_PRODUCTION_STATE.md")
    assert "country.html" in COUNTRY_SHARED_FILES
    print("Impact classifier self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--github-output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.base:
        parser.error("--base is required unless --self-test is used")

    result = classify(args.base, args.head)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.github_output:
        write_github_output(Path(args.github_output), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
