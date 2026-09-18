# Map geographic context — rollout handoff

Status: **PREPARATION ONLY**. No approved map asset, Country JSON, Production State or publication setting is changed. This is not a replacement for `docs/MAP_SYSTEM.md` and does not authorize release.

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

For an **existing approved SVG**, `scripts/add_country_map_context.py` preserves the existing target path bytes, bounds and markers, changes the sea palette and inserts GSHHS context below the target. It uses the complete map/region canvas including aspect-fit margins and always creates a distinct preview file:

```bash
python3 scripts/add_country_map_context.py \
  --country-json data/countries/example.json \
  --input assets/images/example/map-atlas-v1.svg \
  --output /tmp/example-map-context-review.svg
```

The placeholder example is not a Country to create. Azerbaijan's existing SVG already includes context; the tool rejects adding it again.

### Supported in preparation

- Single-region local-equirectangular maps with one approved target path; the accepted legacy aspect-fit `matrix(...)` is checked against Country JSON bounds. An arbitrary or unexplained transform is rejected.
- Multi-region maps with `map.regions`, exactly matching SVG `data-map-region` groups, valid non-overlapping canvas rectangles, and paths inside the declared groups. GSHHS context is projected **per region**, clipped to its rectangle and placed below the untouched target geometry. No global-bounds flattening.
- Alaska-style normalized WGS84 longitude bounds such as −190° to −129° when the actual coast dataset resolves correctly. Ambiguous longitude spans, unsupported polar canvases and incompatible layout formats are rejected.

The source-data dependency in local preparation is Basemap 2.0.0 with `basemap-data` 2.0.0 (package license LGPL-3.0-or-later); identify and record the actual GSHHS source/version/license at the release gate. Intermediate resolution `i` is the default. Do not invent missing source details.

### What remains before migration

The new region implementation has synthetic SVG/unit-test coverage and real GSHHS Alaska geometry checks, **not yet visual approval of all actual completed-Country multi-region SVGs**. Inspect Portugal, United States and Kuwait actual previews, verify every other completed-Country SVG format, calibrate the context against the approved shoreline, and repair any genuine mismatch in the shared stage before rolling out. A JSON region rectangle by itself is not proof of geographical alignment. `generate_country_map_with_context.py` still handles new single-region maps only; do not use it to regenerate bespoke multi-region geometry.

Existing production SVGs, the current default map generator, Country JSON, Production States, publication flags, sitemap, and discovery links remain unchanged. Keep Belize and Honduras on their established in-flight workflows. After both complete, refresh main, re-evaluate actual completion states and select only completed destinations; do not assume 201 finished Countries.

## Batch rollout gate

1. Finish the actual completed-Country format inventory; classify incompatible SVGs instead of forcing conversion. Compare region projection against target paths and markers in real rendered previews.
2. Generate previews using each Country's existing bounds and approved target geometry. Do not edit scene coordinates, Country content, framing, or image assets.
3. Record authoritative source/version/license; verify coastline and border fidelity, XML parse, complete 1200×760 raster decode, size, source-to-preview target-path parity, islands, exclaves, markers, labels, and frame-edge continuity. Compare with Iceland/Norway and Azerbaijan.
4. Run actual Desktop/Tablet/Mobile rendered-page QA for **every** updated Country; shared regression QA must pass. CI alone is not visual approval.
5. Rebase a single reviewed batch on latest main; keep all publication and robots/index settings unchanged. Confirm production build SHA, real Country URLs, asset responses and browser rendering after deployment. Do not publish an unapproved Country.
6. Once the shared behavior and production rollout are verified, update the human new-Country production procedure to use the context generator at CONTENT + MAP. Never silently migrate existing in-flight Countries.

The draft preparation PR remains unmerged until the actual Country formats and above gates are verified; local synthetic region tests alone cannot authorize release.
