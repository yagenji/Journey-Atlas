# Map geographic context — rollout handoff

Status: PREPARATION ONLY. This document records the planned migration; it does not authorize a Country publication, change existing map assets, or replace `docs/MAP_SYSTEM.md`.

## Approved appearance

Azerbaijan's published SVG is the reference: sea gradient `#eaf2f4` → `#dcebf0` → `#d0e3eb`, surrounding land `#e4e0ce`, subtle coast outline `#b6bbaf`, approved target-country land, 1200×760 canvas. Surrounding geography must fill all available space, including aspect-fit sidebands, without any artificial inland cutoff. No neighboring country labels or invented border lines.

## Opt-in shared stage

`scripts/add_country_map_context.py` takes an existing SVG and the matching Country JSON. It derives full-canvas geographic bounds from the existing local-equirectangular fit, uses the installed GSHHS coast polygons via Basemap, preserves target-country SVG path bytes, and writes a **separate preview**. It never modifies the input in place. Example after the ordinary `scripts/generate_country_map.py` step:

```bash
python3 scripts/add_country_map_context.py \
  --country-json data/countries/example.json \
  --input assets/images/example/map-atlas-v1.svg \
  --output /tmp/example-map-context-review.svg
```

A generic filename here illustrates use; do not create a Country called `example`. Inspect source-data metadata, the exact country shape, shoreline detail, the actual rendered preview, and all markers before replacing any production asset. The existing Azerbaijan map already has context; do not run the stage again over that asset.

## Explicit non-goals and blockers during preparation

- The stage currently accepts one untransformed target `<path fill="url(#land)">` with the canonical local-equirectangular projection. It **rejects** transformed SVG paths and `map.regions` multi-region maps, including United States-style insets. Those maps require a reviewed, shared region-aware implementation and QA before migration. Do not flatten regions or use fake geographic coordinates.
- It rejects dateline/polar canvases that cannot be represented safely by the current projection. Do not fill gaps with manually drawn land or silently omit unsupported Countries.
- Existing maps, Country JSON, Production States, publication flags, sitemap, and discovery links remain unchanged on this preparation branch.
- Keep Belize and Honduras in their existing in-flight workflows. When both have completed their current work, refresh main and derive the final completed-Country roster from the canonical registry and the actual Production States. Include both if they qualify; never assume all 201 destinations are finished.

## Migration gate after both Countries finish

1. Extend/test the shared stage for the actual completed-Country SVG formats and region/inset topology; classify unsupported maps instead of silently overwriting them.
2. Generate reviewed SVGs from each Country's existing bounds and approved target geometry; no marker-coordinate, framing, or Country content changes. For maps without foreign land in view, the sea palette may change without adding nonexistent shorelines.
3. Verify GSHHS source/version/licensing metadata, geographic correctness, XML, full SVG raster decode at 1200×760, size, approved geometry parity, country/scene/Hero/capital positions, coastline and island detail, and edge-to-edge land where it exists. Compare against Iceland/Norway and the approved Azerbaijan result.
4. Run actual Desktop/Tablet/Mobile Country-page QA for **every** target, plus relevant shared regression tests, before the publication PR. Do not equate CI success with visual QA.
5. Integrate as one reviewed batch after main rebase; preserve the existing published/unpublished states. Verify deployment SHA, actual Country routes, asset delivery, navigation, robots and sitemap; no approval-free publication of new Countries.
6. After shared behavior is verified, update the human new-Country procedure to require this map context at the CONTENT + MAP stage. Do not silently migrate in-flight legacy Countries.

The future integration PR must not merge while the single-region-only limitation leaves completed map types unsupported. The isolated preparation branch can be reviewed independently.
