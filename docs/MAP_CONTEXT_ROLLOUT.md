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
- Gallery screening found false neighboring-land halos/wedges at **Singapore, Macau, Antigua & Barbuda and Malta**. After the migration-only duplicate-self-land filter, 104 prior/new SVG+PNG pairs were compared: 94 unchanged; only the generated context path changed in 10. Malta's false self-land was removed and Antigua & Barbuda improved but retains a thin sliver. [Comparison evidence and exact changed-country list](https://github.com/yagenji/Journey-Atlas/pull/935#issuecomment-5740779678). This is not release QA.
- **Additional visual HOLD: Monaco.** Its unchanged-after-filter 1200×760 preview has a *single ~1,018-pixel straight generated surrounding-land edge* running from `(979.8, 0)` to `(302.2, 760)` across the entire city-scale map. This is an observable shape in the generated context path, not an independently verified coastline; do not publish it as Monaco/French coastal geography without source comparison. The same temporary numeric SVG inspection finds long context segments in Singapore and Macau; length alone does not establish inaccuracy and must not be used as a universal geometry-rejection rule. Hong Kong, Bahrain, Qatar, Kuwait and Brunei require focused source/inset review. Every remaining map still needs individual full-size geography and actual-page QA.
- [GSHHG full-resolution comparison](https://github.com/yagenji/Journey-Atlas/actions/runs/35426869138) did **not** fix Singapore/Macau. [Independent OSM coastline line-only diagnostic](https://github.com/yagenji/Journey-Atlas/actions/runs/35432056802) found nonuniform differences between source vintages. Never turn open coastline ways into guessed land polygons or switch licenses/sources without verifying them.

## Verified alternative-reference leads — NOT adopted geometry

- **Singapore:** its approved Country JSON cites Singapore Land Authority outlines; the agency's [National Map Polygon](https://data.gov.sg/datasets/d_29f066d67df3eae91df8a42f443863c8/view) covers June 2025 Singapore features, not the adjoining Johor coastline. A Singapore-only dataset therefore cannot repair the cross-border layer. The [Malaysia gbOpen ADM0 metadata](https://www.geoboundaries.org/api/current/gbOpen/MYS/ADM0/) describes an older 2017 boundary derived from OSM/Wambacher, under ODbL, and is not automatically a current compatible shoreline. [Assembled OSM land polygons](https://osmdata.openstreetmap.de/data/land-polygons.html) are a possible geometrically closed comparison source, but they are ODbL and have **not** been acquired, reconciled against the approved shape, or adopted.
- **Macau:** the approved Country JSON cites the SAR WebMap administrative `Freg` layer. The Macao government [published a separately surveyed 2025 SAR coastline](https://geomatics.dsscu.gov.mo/en/geo_coastline_intro_details/article/geo_coastline_intro.html), reference date 1 May 2025. Do not assume the administrative layer and surveyed shoreline have identical geometry or that the linked map grants vector-data redistribution. Verify adjacent Zhuhai land and the dataset's use conditions before making a filled polygon.
- **Monaco:** the [Shom/IGN Limite terre-mer reference](https://www.data.gouv.fr/datasets/limite-terre-mer-1) supplies a high-resolution coastal line under France's Open Licence 2.0; [IGN explicitly includes Monaco in its coverage](https://www.geoportail.gouv.fr/embed). It is a line reference, **not a preverified fill polygon**. Obtain only the relevant authentic features, respect required credit and datum/projection, compare to the existing Monaco target and neighboring coastline, and reject any inferred closure that invents land.

## Provenance and remaining release gates

The preview uses Basemap 2.0.0 data containing **GSHHG 2.3.6**, per [`basemap-data` distribution provenance](https://pypi.org/project/basemap-data/), under LGPL-3.0-or-later. Preserve source/version and check redistribution obligations. An independent OSM coastline diagnostic is ODbL and is **not** adopted as production geometry.

Before release: refresh latest main, registry, Production States and all source hashes; resolve held coastline cases against actual verified sources without changing approved country paths; inspect every changed 1200×760 map individually including islands, exclaves and insets; verify data license/attribution; build and inspect every affected *real Country page* at Desktop/Tablet/Mobile; then apply the separately reviewed coordinated migration and confirm deployed SHA, live map rendering, accessibility and unchanged indexing/navigation. Do not merge PR #935 or copy its staged preview SVGs into production because CI is green.
