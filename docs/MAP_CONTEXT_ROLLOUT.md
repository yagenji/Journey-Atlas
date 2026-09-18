# Map geographic context — rollout handoff

Status (2026-09-18): **TECHNICAL PREPARATION COMPLETE; NOT RELEASED.** The preparation branch changes only opt-in preview/migration scripts, tests, CI and this handoff. The normal generator, existing production SVG/JSON, Country Production States and publication/index/sitemap flags are untouched. Keep PR #935 DRAFT and unmerged until the separate release gates below are satisfied. This document does not replace `docs/MAP_SYSTEM.md`.

## Approved map language

Azerbaijan's published map is the visual reference: sea `#eaf2f4` → `#dcebf0` → `#d0e3eb`, surrounding land `#e4e0ce`, subtle coastline `#b6bbaf`, and the original target-country geometry. The canvas remains 1200×760. Context reaches the frame edge without artificial inland cutoffs; do not invent coastlines, international boundaries or neighboring-country labels. Keep the target country legible and dominant.

## Prepared tools

- `scripts/generate_country_map_with_context.py`: opt-in wrapper for **new single-region Countries**. It invokes the current generator using a verified national boundary and adds separate real-geography GSHHS surrounding land. It does not alter the generator used by currently in-flight Countries. The actual target boundary comes from verified Natural Earth/geoBoundaries data, not from GSHHS alone.
- `scripts/add_country_map_context.py`: shared preview adapter for supported existing approved SVGs; retains all target-country path bytes, map bounds and marker geometry. A separate file is mandatory.
- `scripts/add_country_map_context_existing.py` and `scripts/add_country_map_context_legacy.py`: migration-only dispatch and verified historical SVG layouts. The legacy adapter covers Brunei, Hong Kong, Maldives, Antigua & Barbuda, Bahrain, Qatar and Russia without converting those maps to a new projection. Region/inset clips, raw-grid matrices, shared Hong Kong target `<use>` references and the single valid world cycle in Russia are handled separately; unsupported layouts fail closed.
- `scripts/stage_map_context_rollout.py`: derives the latest completed roster from **`data/atlas-destinations.json` plus Production States**, stages output outside the repository and records each source/output SHA-256 in `manifest.json`. Published Countries and genuinely `COMPLETE` unpublished Countries are eligible; QA/in-progress Countries are excluded. Azerbaijan's already approved context is copied unchanged.

Example preview (not an instruction to modify a production asset):

```bash
python3 scripts/add_country_map_context_existing.py \
  --country-json data/countries/example.json \
  --input assets/images/example/map-atlas-v1.svg \
  --output /tmp/example-context-preview.svg
```

New Country example, with a separately verified national boundary dataset:

```bash
python3 scripts/generate_country_map_with_context.py \
  --country-json data/countries/example.json \
  --source natural-earth --dataset /path/to/verified/admin0.geojson \
  --country-name 'Example Country' \
  --output /tmp/example-context-preview.svg
```

Batch preparation on a **fresh checkout of the intended main**:

```bash
python3 scripts/stage_map_context_rollout.py \
  --output-dir /tmp/journey-atlas-map-context-rollout-stage
```

The output directory must be new or empty and outside the repository. The sample paths above are placeholders, not destinations to create.

## Verified baseline and evidence

- Initial 2026-09-18 baseline: 201 canonical destinations and 103 published Countries, 87 previews, one already approved Azerbaijan and 15 legacy-format holds. [Initial audit](https://github.com/yagenji/Journey-Atlas/actions/runs/35309348351).
- After inherited-fill and multipart-target checks: 95 previews, one approved Azerbaijan and seven remaining historical formats. [Intermediate audit](https://github.com/yagenji/Journey-Atlas/actions/runs/35310624987).
- **Final technical audit:** 104 published Countries in the checkout, **103 successful separate previews + one unchanged Azerbaijan**, zero held formats. Every staged source country's approved shape/path markup remains unchanged and published SVG previews fully rasterize at 1200×760. [Four-shard full inventory](https://github.com/yagenji/Journey-Atlas/actions/runs/35314444444). Honduras had reached `COMPLETE` and is included; Belize was still `QA` and is excluded.
- **Final end-to-end staging rehearsal:** 18 focused tests PASS, real Iceland/Portugal/United States/Kuwait source checks PASS, 104 maps staged to `/tmp` with a SHA-256 manifest and no edits to source assets. Manifest records **104 published / zero completed-unpublished; 103 new previews / one preserved Azerbaijan**. [Successful preflight and manifest artifact](https://github.com/yagenji/Journey-Atlas/actions/runs/35314795607). The rehearsal `sourceCommit` was the PR test merge `ac3f54ffdbf75917f7e482957ae6c3e90de1e981`, **not a permanent release SHA**; recompute on latest main before applying.
- The full-size visual review has included exceptional geography/layout examples, but the contact sheets and successful machine audit do **not** constitute per-Country full-size geographic approval or live Desktop/Tablet/Mobile page QA for every affected Country. These remain explicit release gates.

For audit reproducibility, the Python preview environment used Basemap/basemap-data 2.0.0, shapely 2.x, CairoSVG and Pillow. The basemap-data package declares LGPL-3.0-or-later; confirm the underlying coast dataset's actual GSHHS/GSHHG version and redistribution license at the release gate, rather than inferring them from package licensing.

## Release gate — only after Belize finishes

1. Recheck **latest main**, the canonical 201-destination registry and every relevant Production State. Wait until Belize's existing Country workflow reaches `COMPLETE`; do not modify its active QA branch. Recompute the entire roster, do not reuse the rehearsal's 104-country manifest or merge SHA. Keep each Country's current publication state.
2. Rebase/merge the preparation branch safely against latest main and resolve any PR mergeability issue; check that no concurrent Country assets or common changes are overwritten. Rerun shared tests, all-Country inventory, full decode and shape parity for the final roster. Confirm source/version/license and country-to-context coastline alignment, islands, exclaves, insets, labels and antimeridian/polar behavior.
3. Inspect **every changed map individually at full 1200×760**, not only contact sheets, against the original and the Azerbaijan/Iceland/Norway series. Check the detailed Singapore shoreline especially. Do not equate target-path byte equality with geographic alignment of the new surrounding layer.
4. On the actual Country pages, verify **every affected Country** at Desktop/Tablet/Mobile, accessibility and relevant shared regressions. CI success alone does not approve visual quality.
5. Apply the reviewed assets as one coordinated migration. Preserve JSON, coordinates, all approved land geometry and `atlasPublished`/robots/navigation/sitemap states. Verify final deployment success, deployed SHA, live URL rendering, cache and navigation. Never publish a Country without its own final user approval.
6. Once the shared implementation and release are verified, update `docs/COUNTRY_PRODUCTION_RULES.md` so *future* Country maps use the context generator from the start. Do not silently migrate any still-in-flight Country.

**Do not merge PR #935 or copy any staged SVG to production solely because the technical rehearsal is green.**