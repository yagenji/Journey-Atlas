#!/usr/bin/env python3
"""Audit published Country Pages against the renewal registry.

This script does not rewrite country content. It validates registry coverage and
prints a compact structural audit that can be used to plan renewal work.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "data" / "country-renewal-status.json"
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRIES = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]
THEMES = ROOT / "data" / "theme-taxonomy.json"


def published_slugs() -> list[str]:
    out, seen = [], set()
    for path in REGISTRIES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("destinations", []):
            slug = item.get("slug")
            if item.get("atlasPublished") and slug and slug not in seen:
                seen.add(slug)
                out.append(slug)
    return out


def theme_counts() -> dict[str, list[str]]:
    data = json.loads(THEMES.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for theme in data.get("themes", []):
        label = theme.get("label") or theme.get("id") or "theme"
        for slug in theme.get("examples", []):
            out.setdefault(slug, []).append(label)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status_rows = status.get("countries", [])
    status_slugs = [row.get("slug") for row in status_rows]
    published = published_slugs()

    errors = []
    missing = sorted(set(published) - set(status_slugs))
    extra = sorted(set(status_slugs) - set(published))
    duplicates = sorted({slug for slug in status_slugs if status_slugs.count(slug) > 1 and slug})
    if missing:
        errors.append(f"renewal status missing published countries: {', '.join(missing)}")
    if extra:
        errors.append(f"renewal status contains non-published countries: {', '.join(extra)}")
    if duplicates:
        errors.append(f"renewal status contains duplicate slugs: {', '.join(duplicates)}")

    themes = theme_counts()
    rows = []
    by_status = {row["slug"]: row for row in status_rows if row.get("slug")}
    for slug in published:
        path = COUNTRY_DIR / f"{slug}.json"
        if not path.exists():
            errors.append(f"published Country JSON missing: {slug}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        visible_facts = [f for f in data.get("facts", []) if f.get("label") != "地域"]
        row = {
            "slug": slug,
            "auditState": by_status.get(slug, {}).get("auditState"),
            "renewalClass": by_status.get(slug, {}).get("renewalClass"),
            "hardImageGate": bool(by_status.get(slug, {}).get("hardImageGate")),
            "visibleFacts": len(visible_facts),
            "scenes": len(data.get("scenes", [])),
            "encounters": len(data.get("encounters", [])),
            "beyond": len(data.get("atlasExtras", [])),
            "trivia": len(data.get("travelTrivia", [])),
            "themes": len(themes.get(slug, [])),
            "hasHero": bool(data.get("hero", {}).get("image")),
            "hasMap": bool(data.get("map", {}).get("svg")),
            "sourcesVerifiedAt": data.get("sourcesVerifiedAt"),
        }
        rows.append(row)

    if args.json:
        print(json.dumps({"published": len(published), "rows": rows, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(f"Published Country renewal audit: {len(published)} country page(s)")
        for row in rows:
            print(
                f"{row['slug']:<16} audit={row['auditState']:<7} class={row['renewalClass']:<12} "
                f"gate={'Y' if row['hardImageGate'] else 'N'} facts={row['visibleFacts']} scenes={row['scenes']} "
                f"enc={row['encounters']} beyond={row['beyond']} trivia={row['trivia']} themes={row['themes']}"
            )
        if errors:
            print("Registry errors:")
            for error in errors:
                print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
