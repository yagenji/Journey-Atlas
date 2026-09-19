# Existing Country geographic-context migration — handoff

Status (2026-09-19): **DRAFT / GEOGRAPHIC QA HOLD / NOT RELEASED.** This branch prepares an opt-in migration of approved existing maps. New Country geographic-context generation and its production rules are **already on main via PR #950**. Do not use this branch to overwrite that common generator, in-flight Country assets, Country JSON, Production State or publication settings. PR #935 remains draft and unmerged.

## Scope and map language

The canonical registry is `data/atlas-destinations.json` (201 destinations); use current registry and Production State to recalculate the finished roster, never hardcode the historical count. The migration retains every original country path and marker on the 1200×760 canvas, with existing national outlines dominant, sea `#eaf2f4` → `#dcebf0` → `#d0e3eb`, surrounding land `#e4e0ce`, and quiet coast stroke `#b6bbaf`. Context data must not invent coastlines, boundaries or labels. Azerbaijan and other already-context maps remain untouched.

## Prepared tools

- `scripts/add_country_map_context.py` is the shared generator already on main for canonical layouts. The Country's national boundary comes from its approved verified source; GSHHG supplies surrounding land only.
- `scripts/add_country_map_context_existing.py` dispatches migration previews to the canonical or `scripts/add_country_map_context_legacy.py` adapter. Seven reviewed historic SVG structures (Brunei, Hong Kong, Maldives, Antigua & Barbuda, Bahrain, Qatar, Russia) are supported without rewriting approved target geometry.
- `scripts/filter_duplicate_target_context.py` is **existing-map migration-only**. It compares a generated context ring against a temporary raster mask of the approved SVG land gradient and removes only a simple generated context ring whose area is >=250 pixels and whose overlap is >=80%. This addresses the common GSHHG self-land layer protruding beyond the approved outline. Holes, curves, unknown gradients and unrecognized structures are left unchanged. It never edits a source/approved path and is not a license to change the underlying coastline source.
- `scripts/stage_map_context_rollout.py` stages completed maps to a new directory **outside** the repository and records input/output SHA-256 in `manifest.json`; it never changes production assets or publication flags.

Read-only preview example:

```bash
python3 scripts/add_country_map_context_existing.py \
  --country-json data/countries/example.json \
  --input assets/images/example/map-atlas-v1.svg \
  --output /tmp/example-context-preview.svg
```

Fresh-main batch rehearsal:

```bash
python3 scripts/stage_map_context_rollout.py \
  --output-dir /tmp/journey-atlas-map-context-rollout-stage
```

The example names are placeholders. The output must be new and separate from any production asset.

## Dated verification, not release approval

- [2026-09-19 full four-shard inventory](https://github.com/yagenji/Journey-Atlas/actions/runs/35426483460) at the then-current main: **109 published Countries, 104 previewable, five already-context**, with path parity and full 1200×760 decode. Belize and Honduras both COMPLETE and published. The [stage rehearsal](https://github.com/yagenji/Journey-Atlas/actions/runs/35426483458) produced 109 entries, source/output hashes and no production mutations. New Country work can advance main; these numbers are a snapshot, not a permanent rollout roster.
- A full-gallery visual screen found false neighboring-land halos/wedges at **Singapore, Macau, Antigua & Barbuda and Malta**; Hong Kong, Bahrain, Qatar, Kuwait and Brunei require focused source/inset review. All remaining maps also require individual full-size geography and actual-page QA. Path parity and raster decode alone do not prove coastal alignment.
- [GSHHG full-resolution comparison](https://github.com/yagenji/Journey-Atlas/actions/runs/35426869138) did **not** fix Singapore/Macau. [Independent OSM coastline line-only diagnostic](https://github.com/yagenji/Journey-Atlas/actions/runs/35432056802) found nonuniform differences between source vintages. Never turn open coastline ways into guessed land polygons or switch licenses/sources without verifying them.
- The migration-only duplicate-self-land filter improves Malta and Antigua & Barbuda in 1200×760 comparison previews. It does **not** resolve the mainland/shoreline discrepancies in Singapore or Macau, nor independently prove any other map accurate. See the latest PR #935 discussion and CI for test status.

## Provenance and remaining release gates

The preview uses Basemap 2.0.0 data containing **GSHHG 2.3.6**, per [`basemap-data` distribution provenance](https://pypi.org/project/basemap-data/), under LGPL-3.0-or-later. Preserve source/version and check redistribution obligations. An independent OSM coastline diagnostic is ODbL and is **not** adopted as production geometry.

Before release: refresh latest main, registry, Production States and all source hashes; resolve held coastline cases against actual verified sources without changing approved country paths; inspect every changed 1200×760 map individually including islands, exclaves and insets; verify data license/attribution; build and inspect every affected *real Country page* at Desktop/Tablet/Mobile; then apply the separately reviewed coordinated migration and confirm deployed SHA, live map rendering, accessibility and unchanged indexing/navigation. Do not merge PR #935 or copy its staged preview SVGs into production because CI is green.
