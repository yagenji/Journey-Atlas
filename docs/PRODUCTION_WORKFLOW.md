# JOURNEY ATLAS Production Workflow

Iceland is the visual and data benchmark. New country pages are produced through the same shared template; do not copy Iceland-specific code.

## 1. Create the country scaffold

The slug must already exist in either the 199-destination core registry or the 2-destination editorial registry.

```bash
python scripts/new_country.py norway
```

This creates `data/countries/norway.json` with the schema-v2 structure, exactly 8 scenery slots, the fixed 7-item basic-fact order, 3 signature-fact slots, and travel-trivia slots.

The script never changes `atlasPublished`. A draft cannot become public by being scaffolded.

## 2. Complete content and assets

Required before publication:

- Hero image and location coordinates
- accurate map SVG and bounds
- capital coordinates
- exactly 8 scenery entries and assets
- 8 encounter terms
- common basic facts in the fixed order
- exactly 3 signature facts
- Beyond the Scenery content
- 4–6 sourced Travel Trivia items
- seasons, transport, personas and travel notes
- related destinations
- `seo.description`
- source notes / source keys

Follow `docs/COUNTRY_TEMPLATE.md`, `docs/MAP_SYSTEM.md`, and `docs/ILLUSTRATION_STYLE_GUIDE.md`.

## 3. Validate before publication

Draft files may remain incomplete while being edited. Publication is gated by strict validation.

```bash
python scripts/validate_country.py --published
```

Set `atlasPublished: true` in the appropriate registry only when the country is release-ready. The validator then treats the full production contract as mandatory.

## 4. Production build

GitHub Pages automatically runs:

```text
source validation
→ CSS bundle build
→ encoded-image materialization
→ static country page generation
→ sitemap / robots generation
→ production validation
→ Pages deployment
```

`build_site.py` combines the two source registries into one logical 201-destination scope. Hong Kong and Macau therefore use the same publication pipeline as the 199 core destinations.

The browser receives normal WebP files in production even when a source asset had to be stored as `.b64` or `.parts.json` because of repository tooling limitations.

## 5. Canonical URL

Published country pages use:

```text
/countries/{slug}/
```

`country.html?country={slug}` remains a compatibility route and is `noindex,follow` in the production artifact.

The canonical site origin comes from `data/site.json`. When `atlas.yagenji.com` becomes the canonical domain, update `baseUrl` there rather than changing every country page.

## 6. Release QA

Automation catches structural/data failures. A human visual check is still required for:

- desktop layout
- tablet layout
- ~390px mobile layout
- header behavior while scrolling
- map marker collisions / label readability
- Japanese line breaks
- image crop and watercolor consistency
- factual/contextual duplication across sections

Do not publish the next batch solely because CI is green; CI confirms structure, not editorial quality.
