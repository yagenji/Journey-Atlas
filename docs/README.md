# Documentation index

JOURNEY ATLAS keeps new-Country production intentionally small.

## New Country — startup

Read:
1. `../AGENTS.md`;
2. `COUNTRY_PRODUCTION_RULES.md`;
3. the target `../data/countries/{slug}.json` if it exists.

Phase-specific quality references:
- `IMAGE_QUALITY.md`;
- `CONTENT_QUALITY.md`;
- `MAP_QUALITY.md`.

There is no Country Production State source of truth and no image-generation ledger.

## Data source of truth

- `../data/atlas-destinations.json` — canonical destination scope and publication discovery;
- `../data/countries/{slug}.json` — Country content, coordinates and asset references;
- `../data/theme-taxonomy.json` — TRAVEL THEMES;
- `../data/region-taxonomy.json` — Region taxonomy;
- `../assets/images/{slug}/` — approved production assets.

## Shared product references

- `COUNTRY_TEMPLATE.md` — Country JSON / Template contract;
- `COUNTRY_PAGE_TEMPLATE.md` — Country Page information structure;
- `DESIGN_SPEC.md` — shared visual system;
- `THEME_SYSTEM.md` — theme system;
- `CLOUDFLARE_PAGES.md` — deployment infrastructure;
- `PUBLISHED_COUNTRY_RENEWAL.md` — published-Country renewal work.

Iceland / Norway remain visual-series references. Spain remains the Taste/information-density reference.

## Quality automation

Quality scripts inspect finished artifacts. They do not represent a production workflow.

Core new-Country checks:
- `scripts/validate_country.py`;
- `scripts/validate_country_editorial_v2.py`;
- `scripts/validate_country_quality_v5.py`;
- `scripts/validate_country_map_v6.py`;
- `scripts/validate_images.py`;
- Browser QA.

## Do not use as production source of truth

- branch names;
- generated `countries/{slug}/index.html`;
- retired Production State files;
- retired image-generation policy/ledger files;
- old protocol documents;
- CI success alone.

Git history remains the archive for retired production machinery and historical Country work.
