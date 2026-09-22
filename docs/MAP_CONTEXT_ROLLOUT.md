# Existing Country geographic-context migration — handoff

Status (2026-09-22): **DRAFT / STAGE ② COMPLETE / STAGE ③ READY / NOT RELEASED.** This branch prepares an opt-in migration of approved existing maps. New Country geographic-context generation and its production rules are already on main via PR #950. Do not use this branch to overwrite that common generator, in-flight Country assets, Country JSON, Production State or publication settings. PR #935 remains draft and unmerged.

## Scope and map language

The canonical registry is `data/atlas-destinations.json` (201 destinations); use current registry and Production State to recalculate the finished roster before release. The migration retains every original country path and marker on the 1200×760 canvas, with existing national outlines dominant, sea `#eaf2f4` → `#dcebf0` → `#d0e3eb`, surrounding land `#e4e0ce`, and quiet coast stroke `#b6bbaf`. Context data must not invent coastlines, boundaries or labels.

## Stage ② completion — 2026-09-22

Stage ② is complete as a **QA disposition**, not as a release. The current registry/Production-State-derived roster is 109 selected published/completed maps: 94 freshly staged preview pairs and 15 maps already carrying reviewed context. All 94 fresh SVG/PNG pairs were hash-checked, parsed as `viewBox="0 0 1200 760"`, fully decoded at 1200×760, and visually screened across all four inventory contact sheets. Approved national paths remain unchanged. The staged 109-map set also passed the existing real Country-page browser QA at Desktop / Tablet / Mobile, and the latest map-context preflight at head `7544309af448a6310602cce33690c006d343b224` completed successfully, including the page-visible source-credit checks.

The common ordinary-map case uses Basemap 2.0.0 / GSHHG 2.3.6 for surrounding land only. Stage ② does not require replacing this verified common source with a different country-specific source where there is no observed mismatch. Country-specific source reconciliation was reserved for maps whose generated context showed a material seam, self-land duplication, false island appearance, or ambiguous legacy topology.

### Stage ② PASS / eligible for Stage ③

- Ordinary generated candidates with no material geographic anomaly in the full-size review: PASS under the common GSHHG source, original-path parity, full decode and page QA.
- Singapore / Macau: PASS. Their approved target silhouettes remain protected; neighboring land is source-backed by the reconciled OSM coastline plus the documented official/administrative classification inputs. Desktop / Tablet / Mobile pages show the required OSM/ODbL credit.
- Qatar / Kuwait: PASS for the reviewed migration state. Duplicate self-land in the Doha / Kuwait City insets was removed while preserving approved paths; exact-path guards, 1200×760 decode and page QA pass.
- Antigua & Barbuda: PASS after removal of the false Green Island-derived self-land artifact while retaining all three approved paths.
- Portugal: PASS for Stage ②. Mainland / Azores / Madeira keep their original projections and are explicitly framed as separate geographic viewports; the reviewed full-size result no longer presents the mainland clipping as an unexplained island-like cutout.
- Andorra / Liechtenstein / San Marino / Vatican City and other already-reviewed context maps: PASS where the branch preserves approved national geometry and the current attribution/browser checks succeed.
- Malta: no verified foreign land is introduced; the empty-context result is treated as a no-op rather than inventing nearby land.

### Stage ② FAIL / excluded from the coordinated Stage ③ promotion

These four candidates are **not unresolved work inside Stage ②**. Stage ② has completed by rejecting them from this coordinated migration. Their current approved production maps must remain unchanged unless a later separately sourced repair is approved.

- **Bahrain** — exclude. The generated candidate has a western-edge pale wedge and ambiguous Hawar/Qatar inset polygons. The available official SLRB Hawar/topographic products identify useful reference geography but do not provide a verified redistributable vector input for this migration. No inferred deletion or coastline repair is allowed.
- **Hong Kong** — exclude. The generated candidate leaves disconnected Shenzhen/mainland wedges and sea-colored breaks against the New Territories. Do not infer a cross-border land polygon from coastline fragments; keep the approved 18 target paths and existing production map unchanged.
- **Brunei** — exclude. The legacy generated ring combines real Malaysia with geometry overlapping almost the entire approved two-part Brunei target. Deleting the ring would erase genuine neighboring land; promoting it would retain misleading overlap. Preserve the approved current production map.
- **Monaco** — exclude. Source-backed French-land diagnostics remove the gross GSHHG diagonal, but the remaining cross-source seams are not acceptable for coordinated promotion. Do not smooth, pad or infer the interface.

This exclusion is the Stage ② result. Stage ③ must promote only the PASS set and must not copy the four excluded candidate SVGs into production.

## Stage ③ gate

Stage ③ may now begin on the PASS set only. Before any merge or deployment, regenerate the live roster from the latest `main`, verify source hashes, promote only reviewed assets, and inspect the affected real Country pages at Desktop / Tablet / Mobile with markers, attribution, accessibility, and publication/indexing unchanged. The four Stage ② exclusions remain on their current approved production maps.

## Stage ④ gate

Only after explicit user final approval: merge/deploy, verify deployed SHA, live URLs, navigation, `atlasPublished`, robots/noindex behavior and sitemap. No review-only Country may be published early.

## Prepared tools and provenance

- `scripts/add_country_map_context.py`: shared canonical generator; approved country boundary comes from the verified existing map and GSHHG supplies surrounding land only.
- `scripts/add_country_map_context_existing.py` / `scripts/add_country_map_context_legacy.py`: existing-map migration adapters; they do not authorize rewriting approved target geometry.
- `scripts/filter_duplicate_target_context.py`: migration-only suppression of clearly duplicated generated self-land rings; it never edits an approved source path and is not a license to invent neighboring geography.
- `scripts/stage_map_context_rollout.py`: stages outside the repository and records source/output SHA-256; it does not change publication flags.
- Basemap 2.0.0 includes GSHHG 2.3.6 under the basemap-data distribution terms. OSM-derived exception context is ODbL and must retain page-visible attribution.

Evidence: PR #935 discussion and the latest successful map-context preflight `35719353622`. Do not merge PR #935 merely because CI is green; Stage ③ and explicit final approval still remain.
