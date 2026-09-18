# Map geographic context — rollout handoff

Status: **PREPARATION ONLY**. No approved map asset, Country JSON, Production State or publication setting is changed. This does not replace `docs/MAP_SYSTEM.md` and does not authorize release.

## Approved appearance

Azerbaijan's published SVG is the visual reference: sea gradient `#eaf2f4` → `#dcebf0` → `#d0e3eb`, surrounding land `#e4e0ce`, subtle coastline `#b6bbaf`, approved target-country geometry, 1200×760 canvas. Surrounding land reaches the frame edge without artificial inland cutoffs; no fictional borders or neighboring-country labels. The main country stays the visual focus.

## Opt-in preview generation

For a new **single-region** Country, `scripts/generate_country_map_with_context.py` runs the existing `generate_country_map.py` and then the context stage. It uses bounds from Country JSON and a country-specific Natural Earth/geoBoundaries administrative boundary; GSHHS alone does not identify the target country's national border. This is an opt-in wrapper, not the default generator used by in-flight Countries.

```bash
python3 scripts/generate_country_map_with_context.py \
  --country-json data/countries/example.json \
  --source natural-earth --dataset /path/to/verified/admin0.geojson \
  --country-name 'Example Country' \
  --output /tmp/example-map-context-review.svg
```

For an **existing approved SVG**, `scripts/add_country_map_context.py` preserves existing target path bytes, bounds and markers, changes the sea palette and inserts GSHHS context below the target. It uses the complete map/region canvas including aspect-fit margins and always creates a distinct preview file:

```bash
python3 scripts/add_country_map_context.py \
  --country-json data/countries/example.json \
  --input assets/images/example/map-atlas-v1.svg \
  --output /tmp/example-map-context-review.svg
```

The placeholder example is not a Country to create. Azerbaijan's existing SVG already includes context; the tool rejects adding it again.

### Supported in preparation

- Single-region local-equirectangular maps with one explicit approved target path; the accepted legacy aspect-fit `matrix(...)` is checked against Country JSON bounds. An arbitrary or unexplained transform is rejected.
- Multi-region maps with `map.regions`, exactly matching SVG `data-map-region` groups, valid non-overlapping canvas rectangles, and paths inside the declared groups. GSHHS context is projected **per region**, clipped to its rectangle and placed below untouched target geometry. No global-bounds flattening.
- Alaska-style normalized WGS84 longitude bounds such as −190° to −129° when the actual coast dataset resolves correctly. Ambiguous longitude spans, unsupported polar canvases and incompatible layout formats are rejected.

The source-data dependency in local preparation is Basemap 2.0.0 with `basemap-data` 2.0.0 (package license LGPL-3.0-or-later); identify and record the actual GSHHS source/version/license at the release gate. Intermediate resolution `i` is the default. Do not invent missing source details.

## Published-Country inventory — 2026-09-18 snapshot

[Read-only four-shard audit](https://github.com/yagenji/Journey-Atlas/actions/runs/35309348351) used the canonical registry and actual Country JSON/SVG in the PR checkout (merge-checkout SHA `6a41e68990f3…`). Scope: **201 destinations; 103 published at that snapshot**. The independent inventory checks confirmed 103 unique published slugs. Belize and Honduras both had Production State `phase: QA` and `atlasPublished: false`; neither was modified or counted as published.

- **87**: separate context SVGs generated, original explicitly filled target paths compared unchanged, XML parsed and PNGs fully decoded at 1200×760. This is technical preflight only, not geographical/visual approval. Four contact-sheet previews and per-Country PNG/SVG reports are available in the short-lived CI artifacts.
- **1**: Azerbaijan already has the approved palette/context; never add the context twice.
- **15**: deliberately held for review rather than forced conversion, split as follows.

| Actual legacy format | Countries | Next shared implementation decision |
| --- | --- | --- |
| Multiple explicitly filled country paths | Cambodia | Accept multiple preserved targets with exact path parity and checked projection. |
| Target paths inherit `fill="url(#land)"` from parent groups | Norway, Japan, Singapore, Myanmar, Bangladesh, Indonesia, Malaysia | Resolve effective SVG fill without treating sea/terrain overlay paths as country geometry; preserve the original group styling and all path bytes. |
| Other land styling or no explicit country-path fill | Brunei (`url(#country)`), Hong Kong (unfilled paths) | Identify and verify actual target-path grouping and source geometry; no guessed fill or invented shapes. |
| Legacy noncanonical transform | Maldives | Validate the actual historical matrix and its relationship to Country bounds; do not change the approved atoll framing. |
| Different multi-region projection / no canonical `data-map-region` groups | Antigua & Barbuda, Bahrain, Qatar | Review the real SVG inset projection/layout and add a shared adapter only where its mapping can be proven. |
| Longitude span over the current 180° guard | Russia | Use a verified unwrapped/cyclic regional projection and real GSHHS geography; no guessed clipping across the antimeridian. |

[Detailed source SVG diagnostics](https://github.com/yagenji/Journey-Atlas/actions/runs/35309610744) capture each exception's projection, bounds, actual SVG path fills, transforms and declared regions. A successful CI run here reports the blockers; it **does not** mean those fifteen passed migration. The existing map files are not thereby declared defective.

## Migration gate after Belize and Honduras complete

1. Recheck latest main and current Production States; rederive the completed-Country roster (published plus genuinely finished unpublished reviewable Countries). Do not assume all 201 destinations are complete or automatically migrate either in-flight Country.
2. Resolve the fifteen structural blockers in the shared stage with focused tests; rerun the full inventory and preview raster/parity checks for every target. Preserve existing bounds, target geometry and marker coordinates. Classify any newly observed format rather than silently bypassing checks.
3. Verify authoritative geographic source/version/license, country boundary and coast alignment, islands/exclaves, region inset positioning, label/marker positions, edge continuity, full raster decode and visual series quality for every Country; compare with Iceland/Norway and the approved Azerbaijan reference. The contact sheets are for triage only, not a substitute for full-size per-Country review.
4. Run actual Desktop/Tablet/Mobile browser QA on **every** changed Country page and shared regression tests. CI success alone is insufficient.
5. Integrate as one reviewed batch on latest main; retain all publication/robots/index/sitemap states. Verify production SHA, real URLs and asset delivery after deployment. Do not publish an unapproved Country.
6. Only after the shared behavior and rollout are verified, update the human new-Country procedure to use the context generator at CONTENT + MAP. Never silently migrate legacy in-flight Countries.

The preparation PR remains **draft and unmerged** until the full inventory's blockers and above review gates are resolved; no Country or publication changes belong in this preparation PR.
