#!/usr/bin/env python3
"""Validate JOURNEY LENS RSS slugs against the canonical ATLAS registry."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "atlas-destinations.json"
RSS_URL = "https://journey.yagenji.com/rss.xml"
ARTICLE_URL_RE = re.compile(r"^https://journey\.yagenji\.com/([a-z]+)(\d+)/$")
LEGACY_URL_RE = re.compile(r"^https://journey\.yagenji\.com/([a-z]+)/$")
SLUG_RE = re.compile(r"^[a-z]+$")
# Hong Kong predates the letters-only slug contract and keeps its canonical
# published ATLAS route. New destination slugs must still follow SLUG_RE.
ATLAS_SLUG_EXCEPTIONS = {"hong-kong"}
# The published Hill of Crosses article predates numbered JOURNEY LENS story
# routes. Preserve its actual canonical URL; do not permit other unnumbered URLs.
VERIFIED_LEGACY_ARTICLE_URLS = {
    "https://journey.yagenji.com/lithuania/": "lithuania",
}
CANONICAL_DESTINATION_COUNT = 201


def load_rss() -> bytes:
    cache_busted_url = f"{RSS_URL}?atlas_check={time.time_ns()}"
    request = urllib.request.Request(
        cache_busted_url,
        headers={
            "User-Agent": "JOURNEY-ATLAS-slug-validator/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def fail(messages: list[str], message: str) -> None:
    messages.append(message)


def main() -> int:
    errors: list[str] = []
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    destinations = registry.get("destinations", [])
    slugs = [item.get("slug") for item in destinations]

    if registry.get("count") != CANONICAL_DESTINATION_COUNT:
        fail(
            errors,
            f"Registry count must be {CANONICAL_DESTINATION_COUNT}, found {registry.get('count')!r}",
        )
    if len(destinations) != CANONICAL_DESTINATION_COUNT:
        fail(errors, f"Expected {CANONICAL_DESTINATION_COUNT} canonical destinations, found {len(destinations)}")
    invalid = [
        slug
        for slug in slugs
        if not isinstance(slug, str)
        or (not SLUG_RE.fullmatch(slug) and slug not in ATLAS_SLUG_EXCEPTIONS)
    ]
    if invalid:
        fail(errors, f"Invalid registry slug(s): {invalid}")
    if len(set(slugs)) != len(slugs):
        fail(errors, "Duplicate slug(s) in atlas-destinations.json")

    registry_by_slug = {item["slug"]: item for item in destinations if isinstance(item.get("slug"), str)}
    scope_exceptions = {
        item["slug"]
        for item in registry.get("journeyLensRegistryExceptions", [])
        if isinstance(item, dict) and isinstance(item.get("slug"), str)
    }
    legacy_url_exceptions = {
        item["url"]: item.get("slug")
        for item in registry.get("journeyLensLegacyUrlExceptions", [])
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    }
    for url, slug in VERIFIED_LEGACY_ARTICLE_URLS.items():
        if url in legacy_url_exceptions and legacy_url_exceptions[url] != slug:
            fail(errors, f"Conflicting legacy URL exception: {url} -> {legacy_url_exceptions[url]}")
        legacy_url_exceptions.setdefault(url, slug)

    try:
        root = ET.fromstring(load_rss())
    except Exception as exc:
        print(f"JOURNEY LENS RSS validation failed: {exc}", file=sys.stderr)
        return 1

    rss_slugs: set[str] = set()
    legacy_seen: list[str] = []
    item_count = 0

    for item in root.findall("./channel/item"):
        item_count += 1
        link = (item.findtext("link") or "").strip()
        match = ARTICLE_URL_RE.fullmatch(link)
        if match:
            rss_slugs.add(match.group(1))
            continue

        legacy = LEGACY_URL_RE.fullmatch(link)
        if legacy and link in legacy_url_exceptions:
            declared_slug = legacy_url_exceptions[link]
            if declared_slug != legacy.group(1):
                fail(errors, f"Legacy URL exception slug mismatch: {link} -> {declared_slug}")
            rss_slugs.add(legacy.group(1))
            legacy_seen.append(link)
            continue

        fail(errors, f"LENS article URL violates /{{slug}}{{sequence}}/ convention: {link}")

    allowed_slugs = set(registry_by_slug) | scope_exceptions
    unknown = sorted(rss_slugs - allowed_slugs)
    if unknown:
        fail(errors, "LENS RSS slug(s) missing from atlas-destinations.json: " + ", ".join(unknown))

    declared_published = {
        item["slug"]
        for item in destinations
        if item.get("journeyLensPublished") is True and isinstance(item.get("slug"), str)
    }
    missing_from_rss = sorted(declared_published - rss_slugs)
    if missing_from_rss:
        fail(errors, "journeyLensPublished=true but no RSS article found: " + ", ".join(missing_from_rss))

    if errors:
        print("JOURNEY LENS slug drift validation failed:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1

    for slug in sorted(rss_slugs & scope_exceptions):
        print(f"WARNING: LENS slug '{slug}' uses an explicit ATLAS scope exception.")
    for url in legacy_seen:
        print(f"WARNING: legacy LENS article URL is temporarily allowed: {url}")

    print(
        f"Validated canonical {CANONICAL_DESTINATION_COUNT}-destination ATLAS registry; "
        f"{item_count} LENS RSS item(s), {len(rss_slugs)} unique slug(s), "
        f"{len(declared_published)} mapped journeyLensPublished destination(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
