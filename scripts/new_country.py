#!/usr/bin/env python3
"""Create a schema-v2 JOURNEY ATLAS country JSON scaffold from the 201-destination registry."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY_PATHS = [ROOT / "data" / "atlas-destinations.json", ROOT / "data" / "atlas-destinations-editorial.json"]
TAXONOMY_PATH = ROOT / "data" / "region-taxonomy.json"


def destination_for_slug(slug: str) -> dict | None:
    for path in REGISTRY_PATHS:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for item in registry.get("destinations", []):
            if item.get("slug") == slug:
                return item
    return None


def taxonomy_region_for_iso2(iso2: str) -> str | None:
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    for region in taxonomy.get("regions", []):
        subregions = region.get("subregions") or []
        if subregions:
            for subregion in subregions:
                if iso2 in subregion.get("iso2", []):
                    return subregion.get("labelEn")
        elif iso2 in region.get("iso2", []):
            return region.get("labelEn")
    return None


def blank_scene(index: int, slug: str) -> dict:
    return {"id":f"scene-{index}","name":"","nameLocal":"","mapLabel":"","description":"","coordinates":{"latitude":None,"longitude":None},"image":f"assets/images/{slug}/approved/scene-{index}.webp"}


def blank_taste(index: int, slug: str) -> dict:
    return {"id":f"food-{index}","name":"","nameLocal":"","text":"","image":f"assets/images/{slug}/approved/food-{index}.webp","imageState":"PENDING"}


def blank_extra() -> dict:
    return {"topicKey":"","themeEn":"","themeJa":"","title":"","text":"","points":["",""]}


def blank_persona() -> dict:
    return {"title":"","text":""}


def blank_tip() -> dict:
    return {"topicKey":"","title":"","text":""}


def blank_related() -> dict:
    return {"slug":"","nameEn":"","nameJa":"","flag":"","reason":"","affinityType":""}


def blank_travel_scale() -> dict:
    return {
        "kicker":"DURATION","title":"旅の目安日程","intro":"滞在日数と、どこまで旅を広げるかで選ぶ。",
        "items":[
            {"duration":"○〜○日","title":"","text":"例：","icon":"city"},
            {"duration":"○〜○日","title":"","text":"例：","icon":"map"},
            {"duration":"○日以上","title":"","text":"例：","icon":"compass"},
        ],
    }


def scaffold(destination: dict, region_label: str) -> dict:
    slug = destination["slug"]
    name_en = destination.get("nameEn", "")
    name_ja = destination.get("nameJa", "")
    today = date.today().isoformat()
    return {
        "schemaVersion":2,"contentQaVersion":6,"publicationPipelineVersion":2,"slug":slug,"nameEn":name_en,"nameJa":name_ja,"region":region_label,
        "seo":{"description":""},
        "capital":{"nameEn":"","nameJa":"","coordinates":{"latitude":None,"longitude":None},"labelPosition":"right","labelOffset":{"x":0,"y":0}},
        "hero":{"lead":"","image":f"assets/images/{slug}/approved/hero.webp","location":"","coordinates":{"latitude":None,"longitude":None}},
        "map":{"bounds":{"north":None,"south":None,"west":None,"east":None},"svg":f"assets/images/{slug}/map-atlas-v1.svg","route":None,"source":""},
        "scenes":[blank_scene(index,slug) for index in range(1,9)],
        "encounters":[{"title":"","category":""} for _ in range(8)],
        "atlasExtras":[blank_extra() for _ in range(6)],
        "travelTrivia":[{"topicKey":"","categoryEn":"","categoryJa":"","title":"","text":"","icon":"","sourceKey":""} for _ in range(5)],
        "taste":{"kicker":f"TASTE OF {name_en.upper()}","title":f"{name_ja}で食べたいもの","intro":"","items":[blank_taste(index,slug) for index in range(1,5)]},
        "travelScale":blank_travel_scale(),
        "seasons":[{"months":"","color":"","text":""} for _ in range(4)],
        "transport":{"title":"","text":""},
        "personas":[blank_persona() for _ in range(3)],
        "facts":[{"label":"地域","value":""},{"label":"首都","value":""},{"label":"人口","value":""},{"label":"面積","value":""},{"label":"言語","value":""},{"label":"主な宗教","value":""},{"label":"通貨","value":""}],
        "signatureFacts":[{"topicKey":"","label":"","value":"","note":"","icon":"","interestReason":""} for _ in range(3)],
        "tips":[blank_tip() for _ in range(3)],
        "nextRoutes":[],
        "relatedCountries":[blank_related() for _ in range(3)],
        "updatedAt":today,"sourcesVerifiedAt":today,"sourceDates":{},"sources":{},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a JOURNEY ATLAS country JSON scaffold")
    parser.add_argument("slug", help="Destination slug already present in the 201-destination registry")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing country JSON")
    args = parser.parse_args()
    destination = destination_for_slug(args.slug)
    if not destination:
        parser.error(f"Unknown destination slug: {args.slug}")
    region_label = taxonomy_region_for_iso2(destination.get("iso2", ""))
    if not region_label:
        parser.error(f"No region-taxonomy assignment for {args.slug}: {destination.get('iso2')!r}")
    output = COUNTRY_DIR / f"{args.slug}.json"
    if output.exists() and not args.force:
        parser.error(f"Country JSON already exists: {output.relative_to(ROOT)} (use --force only intentionally)")
    output.write_text(json.dumps(scaffold(destination, region_label), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {output.relative_to(ROOT)}")
    print(f"Region taxonomy label locked: {region_label}")
    print("Content QA v6 locked: one-pass editorial selection gate for cross-section subjects, Signature Facts, ENCOUNTERS, Taste headings, NEXT ROUTES, NEXT DESTINATIONS, Travel Scale and capital-label collision safety.")
    print("Run-to-gate policy locked: deterministic non-gate NEXT ACTIONS must continue without asking the user to say 進めて.")
    print("Publication Pipeline v2 locked for this new Country: post-handoff targeted QA, persistent review deployment, State reconciliation and post-approval publication are automated.")
    print("Hero / Scene / Taste final approved-path placeholders are present so the page can be prebuilt before image generation.")
    print("After map.bounds is final: run python3 scripts/normalize_country_region_labels.py, then python3 scripts/audit_country_region_labels.py.")
    print("Before Hero production: complete editorial content + Map, then run scripts/validate_country_editorial_v2.py and scripts/validate_country_quality_v5.py for the Country JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
