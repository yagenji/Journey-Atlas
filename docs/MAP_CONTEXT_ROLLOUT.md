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

- Single-region local-equirectangular maps with one or more approved `url(#land)` target paths, including inherited parent-group fills. All target paths must use the same verified transform chain. The accepted legacy aspect-fit `matrix(...)` is checked against Country JSON bounds; arbitrary transforms and CSS-dependent styling fail closed. The inventory now compares **all** effective approved land paths, not just paths with an explicit `fill` attribute.
- Multi-region maps with `map.regions`, exactly matching SVG `data-map-region` groups, valid non-overlapping canvas rectangles, and paths inside the declared groups. GSHHS context is projected **per region**, clipped to its rectangle and placed below untouched target geometry. No global-bounds flattening.
- Alaska-style normalized WGS84 longitude bounds such as −190° to −129° when the actual coast dataset resolves correctly. Ambiguous longitude spans, unsupported polar canvases and incompatible layout formats are rejected.

The source-data dependency in local preparation is Basemap 2.0.0 with `basemap-data` 2.0.0 (package license LGPL-3.0-or-later); identify and record the actual GSHHS source/version/license at the release gate. Intermediate resolution `i` is the default. Do not invent missing source details.

## Published-Country inventory — 2026-09-18 snapshot

[Initial read-only four-shard audit](https://github.com/yagenji/Journey-Atlas/actions/runs/35309348351) used the canonical registry and actual Country JSON/SVG in the PR checkout. Scope: **201 destinations; 103 published at that snapshot**. Belize and Honduras had Production State `phase: QA` and `atlasPublished: false`; neither was modified or counted as published.

Initial audit: 87 separate previews with original explicit target paths identical and fully decoded 1200×760 PNGs; Azerbaijan already had approved context; 15 were held for incompatible SVG formats. [Detailed source SVG diagnostics](https://github.com/yagenji/Journey-Atlas/actions/runs/35309610744) recorded each exception's projection, bounds, actual path fills, transforms and declared regions. No original production SVG was declared defective or overwritten.

### Follow-up: verified new behavior, technical preflight only

[Updated four-shard audit](https://github.com/yagenji/Journey-Atlas/actions/runs/35310624987) rechecked all 103 published Country SVGs using the shared inherited/multipart path validator and checked that **every approved target-country path** remains identical. Updated result: **95 previews generated and fully decoded at 1200×760; 1 already approved (Azerbaijan); 7 held**. The newly previewable eight are Cambodia, Norway, Japan, Singapore, Myanmar, Bangladesh, Indonesia and Malaysia. CI also passed [focused map-context regression and real-source preview checks](https://github.com/yagenji/Journey-Atlas/actions/runs/35310625008).

The new eight are technically previewable, **not visually approved**. In particular, compare Singapore's detailed source coastline and islands against the GSHHS context at full size: small-scale coast geometry and joining at the target shoreline need explicit inspection. Full-size geography, marker positioning, inset alignment, license and final page render QA remain release gates for every Country.

| Remaining format | Countries | Required evidence before safe conversion |
| --- | --- | --- |
| Different `background` / `country` gradients | Brunei | Verify the exact original sea rectangle and country path, update the shared palette adapter only if target geometry and rendering are preserved. |
| Land paths lack a `url(#land)` fill | Hong Kong | Verify the actual target group and its rendering including inherited/default SVG fill; never treat all unrelated SVG paths as national territory. |
| Noncanonical historical transform | Maldives | Establish the true matrix-to-bounds relationship and atoll framing rather than forcing the canonical matrix. |
| Noncanonical inset projection / missing region groups | Antigua & Barbuda, Bahrain, Qatar | Prove per-region projection and clipping from the actual SVG before a shared adapter. |
| Longitude span exceeds the 180° guard | Russia | Resolve with authoritative unwrapped/cyclic regional geography; do not guess around the antimeridian. |

The audit's success means **the audit ran**. It does not certify either the seven held maps or final visual acceptance of the other 95.

## Migration gate after Belize and Honduras complete

1. Recheck latest main and current Production States; rederive the completed-Country roster (published plus genuinely finished unpublished reviewable Countries). Do not assume all 201 destinations are complete or automatically migrate either in-flight Country.
2. Resolve the seven structural blockers in the shared stage with focused tests; rerun the full inventory and preview raster/parity checks for every target. Preserve existing bounds, target geometry and marker coordinates. Classify any newly observed format rather than bypassing checks.
3. Verify authoritative geographic source/version/license, country boundary and coast alignment, islands/exclaves, region inset positioning, label/marker positions, edge continuity, full raster decode and visual series quality for every Country; compare with Iceland/Norway and the approved Azerbaijan reference. Contact sheets are triage, not full-size per-Country review.
4. Run actual Desktop/Tablet/Mobile browser QA on **every** changed Country page and shared regression tests. CI success alone is insufficient.
5. Integrate as one reviewed batch on latest main; retain all publication/robots/index/sitemap states. Verify production SHA, real URLs and asset delivery after deployment. Do not publish an unapproved Country.
6. Only after shared behavior and rollout are verified, update the human new-Country procedure to use the context generator at CONTENT + MAP. Never silently migrate legacy in-flight Countries.

The preparation PR remains **draft and unmerged** until the full inventory's blockers and above review gates are resolved; no Country or publication changes belong in this preparation PR.
