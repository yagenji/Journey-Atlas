#!/usr/bin/env python3
"""Validate JOURNEY LENS RSS slugs against the ATLAS destination registry."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "atlas-destinations.json"
RSS_URL = "https://journey.yagenji.com/rss.xml"
ARTICLE_URL_RE = re.compile(r"^https://journey\.yagenji\.com/([a-z]+)(\d+)/$")
LEGACY_URL_RE = re.compile(r"^https://journey\.yagenji\.com/([a-z]+)/$")
SLUG_RE = re.compile(r"^[a-z]+$")


def load_rss() -> bytes:
    request = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "JOURNEY-ATLAS-slug-validator/1.0"},
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

    if len(destinations) != 199:
        fail(errors, f"Expected 199 core destinations, found {len(destinations)}")
    if any(not isinstance(slug, str) or not SLUG_RE.fullmatch(slug) for slug in slugs):
        invalid = [slug for slug in slugs if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug)]
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
        f"Validated {item_count} LENS RSS item(s), {len(rss_slugs)} unique slug(s), "
        f"{len(declared_published)} mapped journeyLensPublished destination(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
