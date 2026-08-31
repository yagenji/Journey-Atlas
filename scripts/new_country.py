#!/usr/bin/env python3
"""Create a schema-v2 JOURNEY ATLAS country JSON scaffold from the 201-destination registry."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [
    ROOT / "data" / "atlas-destinations.json",
    ROOT / "data" / "atlas-destinations-editorial.json",
]


def destination_for_slug(slug: str) -> dict | None:
    for path in REGISTRY_PATHS:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            if item.get("slug") == slug:
                return item
    return None


def blank_scene(index: int, slug: str) -> dict:
    return {
        "id": f"scene-{index}",
        "name": "",
        "nameLocal": "",
        "mapLabel": "",
        "description": "",
        "coordinates": {"latitude": None, "longitude": None},
        "image": f"assets/images/{slug}/scene-{index}.webp",
    }


def blank_extra() -> dict:
    return {
        "topicKey": "",
        "themeEn": "",
        "themeJa": "",
        "title": "",
        "text": "",
        "points": ["", ""],
    }


def blank_persona() -> dict:
    return {"title": "", "text": ""}


def blank_tip() -> dict:
    return {"topicKey": "", "title": "", "text": ""}


def blank_related() -> dict:
    return {"slug": "", "nameEn": "", "nameJa": "", "flag": "", "reason": ""}


def scaffold(destination: dict) -> dict:
    slug = destination["slug"]
    return {
        "schemaVersion": 2,
        "contentQaVersion": 1,
        "slug": slug,
        "nameEn": destination.get("nameEn", ""),
        "nameJa": destination.get("nameJa", ""),
        "region": "",
        "seo": {"description": ""},
        "capital": {
            "nameEn": "",
            "nameJa": "",
            "coordinates": {"latitude": None, "longitude": None},
        },
        "hero": {
            "lead": "",
            "image": f"assets/images/{slug}/hero.webp",
            "location": "",
            "coordinates": {"latitude": None, "longitude": None},
        },
        "map": {
            "bounds": {"north": None, "south": None, "west": None, "east": None},
            "svg": f"assets/images/{slug}/map-atlas.svg",
            "route": None,
            "source": "",
        },
        "scenes": [blank_scene(index, slug) for index in range(1, 9)],
        "encounters": [{"title": ""} for _ in range(8)],
        "atlasExtras": [blank_extra() for _ in range(6)],
        "travelTrivia": [
            {"topicKey": "", "categoryEn": "", "categoryJa": "", "title": "", "text": "", "icon": "", "sourceKey": ""}
            for _ in range(5)
        ],
        "seasons": [
            {"months": "", "color": "", "text": ""}
            for _ in range(4)
        ],
        "transport": {"title": "", "text": ""},
        "personas": [blank_persona() for _ in range(3)],
        "facts": [
            {"label": "地域", "value": ""},
            {"label": "首都", "value": ""},
            {"label": "人口", "value": ""},
            {"label": "面積", "value": ""},
            {"label": "言語", "value": ""},
            {"label": "主な宗教", "value": ""},
            {"label": "通貨", "value": ""},
        ],
        "signatureFacts": [
            {"topicKey": "", "label": "", "value": "", "note": ""}
            for _ in range(3)
        ],
        "tips": [blank_tip() for _ in range(3)],
        "relatedCountries": [blank_related() for _ in range(3)],
        "updatedAt": date.today().isoformat(),
        "sources": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a JOURNEY ATLAS country JSON scaffold")
    parser.add_argument("slug", help="Destination slug already present in the 201-destination registry")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing country JSON")
    args = parser.parse_args()

    destination = destination_for_slug(args.slug)
    if not destination:
        parser.error(f"Unknown destination slug: {args.slug}")

    output = COUNTRY_DIR / f"{args.slug}.json"
    if output.exists() and not args.force:
        parser.error(f"Country JSON already exists: {output.relative_to(ROOT)} (use --force only intentionally)")

    output.write_text(json.dumps(scaffold(destination), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {output.relative_to(ROOT)}")
    print("Next: fill content/assets, run strict validation, then set atlasPublished=true only when release-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
