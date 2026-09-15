# JOURNEY ATLAS — Country Production Protocol 2.0

Updated: 2026-09-15
Current policy patch: 5

Machine-readable authority: `ops/country-production-policy.json`.
Image-generation authority: `ops/image-generation-policy.json`.
Content-quality authority for new Countries: `docs/CONTENT_QUALITY_RULES_V6.md`.
Publication automation authority: `docs/PUBLICATION_PIPELINE_V2.md` plus the current Pipeline v2 workflows.

Protocol 2.0 is the default for **new Country production**. New Countries use Content QA v6 and Publication Pipeline v2. Existing in-flight Countries are not automatically migrated from their prior content/publication contracts.

## Production shape

```text
CONTENT + PRE-VISUAL BUILD
→ Hero generation/review
→ Scene round to batch boundary
→ Scene batch review
→ Taste first-pass round to batch boundary
→ Taste batch review
→ Taste REGEN round only when required
→ one 13-image USER_HANDOFF
→ one batch asset verification
→ Pipeline v2 review automation
→ latest-main + target-Country overlay validation
→ target-only Browser QA + persistent GitHub Pages review
→ final Country-page user approval
→ Pipeline v2 finalization on latest-main + target-Country overlay
→ checks on the exact terminal branch SHA
→ squash-merge the same reusable PR
→ inline Cloudflare SHA + target-route smoke verification
```

**Main is not the review environment. A second publication PR and a separate production-verification PR are forbidden for Pipeline v2 Countries.**

## 1. Pre-visual build is mandatory

Before Hero generation, finish everything that does not require the final raster bytes:

- Country JSON editorial content;
- final Hero / S01–S08 / FOOD01–04 paths;
- Scene coordinates;
- Map build and QA, including capital-name / Scene-number collision QA;
- taxonomy;
- Related Countries / NEXT DESTINATIONS;
- NEXT ROUTES or intentional omission;
- Travel Scale;
- Signature Facts;
- ENCOUNTERS;
- Beyond the Scenery / Travel Trivia;
- Taste heading and four dishes;
- sources/source dates;
- current Content QA.

New Countries use `contentQaVersion: 6` and must follow `docs/CONTENT_QUALITY_RULES_V6.md` plus `docs/MAP_SYSTEM.md`.
Existing v5/v4/v3/v2 Countries remain on their prior editorial contracts unless explicitly migrated.

Before leaving CONTENT, run both:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
```

The retained `validate_country_quality_v5.py` filename is intentional. It routes v5/v6 behavior from `contentQaVersion`.

`preVisualBuild.state` and every required check must be `PASS` before leaving CONTENT. Map must already be `APPROVED`, including the v6 capital-label safety gate and the self-contained / coordinate-on-land requirements defined by current policy.

## 2. One image is not one user gate

Scene round:

```text
S01 → S02 → S03 → S04 → S05 → S06 → S07 → S08 → one Batch Review
```

Taste first-pass round:

```text
FOOD01 → FOOD02 → FOOD03 → FOOD04 → one Batch Review
```

A runtime/card/turn boundary does not create an approval boundary. Resume the active round and continue toward its batch boundary.

Use:

```bash
python3 scripts/country_production_protocol_v2.py next {slug}
```

`interaction.userGate` is authoritative. Normal user gates are Hero, Scene Batch, Taste Batch, and final Country-page review only.

The assistant must not require `approve`, `進めて`, `next`, `生成` or equivalent between valid Scene/Taste targets. A platform-forced turn boundary is tracked separately from a user continuation nudge; only the latter is a workflow defect.

Protocol 2 metrics include:

- `productionMetrics.perImageApprovalPrompts` target `0`;
- `productionMetrics.userContinuationNudges` target `0`;
- runtime-forced image turn boundaries are measured but allowed.

## 3. Taste first-pass and REGEN are separate rounds

Taste follows Image Policy 7.2 and the current `ops/image-generation-policy.json`.

If a FOOD target fails during `TASTE_INITIAL`:

1. park that target as `REGENERATE`;
2. continue to the next `NOT_STARTED` FOOD target;
3. do not retry the failed FOOD while another first-pass target remains;
4. after all FOOD01–FOOD04 targets have been attempted, stop at one Taste Batch Review;
5. approve valid candidates and record failures in the batch ledger `regenerate` list;
6. only then enter `TASTE_REGEN`.

`TASTE_REGEN` before a first Taste batch-review ledger round is invalid.

During REGEN, regenerate all remaining NG targets as independent calls and request one regeneration Batch Review at the round boundary. Per-image approval remains forbidden.

Taste composition distinguishes integral dish components from decoration:

- integral sauce, dip, broth, wrapper or serving element may appear when genuinely required to constitute or recognize the dish;
- those elements must be named in the FOOD Render Packet;
- decorative props and contextual styling are forbidden;
- background remains plain pale beige / warm ivory.

Repeat/restage and wrong-target carryover require immediate Render Packet / prompt-family refresh before regeneration. Do not retry the same prompt series once those failures occur.

See `docs/TASTE_IMAGE_PRODUCTION.md` and `docs/IMAGE_POLICY_REVISION_7_2.md`.

## 4. Image handoff is one fixed path

After Hero + 8 Scenes + 4 Taste images are approved:

1. emit one 13-raster manifest;
2. user stores/uploads the 13 files to the exact repository paths;
3. user reports completion once;
4. verify all 13 assets once as a batch.

Use:

```bash
python3 scripts/country_production_protocol_v2.py handoff {slug}
```

This is operational handoff, not an approval gate. Assistant-side raster recovery/materialization is forbidden under this protocol.

## 5. Target-only post-visual fast path

For a normal Country-only change:

1. verify the 13 approved assets once;
2. validate only the target Country JSON/images;
3. let Publication Pipeline v2 run the target Desktop / Tablet / Mobile Browser QA once;
4. do not build or QA unrelated Countries;
5. do not run Cloudflare production before final page approval.

The targeted builder remains:

```bash
python3 scripts/build_country_preview_targeted.py --slugs {slug}
```

Full-Country build/QA is reserved for shared template/CSS/JS/build-system changes, explicit Full QA, and the real final production deployment.

If the user requests an editorial revision during final review, update only the requested content, keep approved image assets locked, reset the target QA/review state as required by current State logic, and rerun the target-only review path.

## 6. Pipeline v2 review uses latest-main overlay, not a branch merge

For new Countries, `publicationPipelineVersion: 2` is the default scaffold. Once the 13-raster handoff is verified and review-ready:

1. `.github/workflows/publication-pipeline-v2-review.yml` resolves the target Country;
2. it asserts Country-only scope against current `main`;
3. it ensures **one reusable review/publication PR** exists;
4. `.github/workflows/publication-pipeline-v2-checks.yml` runs targeted validation/image audit/Browser QA;
5. the review package is built from **latest `main` + the target Country overlay**;
6. the persistent GitHub Pages review is deployed at `/reviews/{slug}/countries/{slug}/`;
7. the successful result is reconciled into authoritative Production State;
8. the next user gate is the final canonical page approval.

Do **not** merge latest `main` directly into a long-running Country branch merely to prepare review. Shared runtime authority during review is latest `main`; Country-specific files remain authoritative from the Country branch overlay.

The PR remains open through final user review and is reused for publication after approval.

## 7. Persistent Country review URLs

GitHub Pages is one deployment surface, but each Country lives in its own persistent subtree:

```text
/reviews/{slug}/countries/{slug}/
```

Implementation rules:

- snapshot branch: `review-previews`;
- maximum retained review snapshots: 8;
- the current Country replaces only its own `/reviews/{slug}/` subtree;
- other active review subtrees are preserved;
- already-published previews are pruned when the next review snapshot is staged;
- oldest snapshots beyond the retained maximum are pruned;
- target raster URLs are rewritten to the immutable raw commit origin;
- the `review-previews` branch is a generated review cache, never production authority.

Protocol NEXT reaches `REVIEW_CANONICAL_URL` only after the target review result is reconciled successfully.

## 8. Final approval reuses the same PR

After explicit user approval, record `finalApproval.state: APPROVED`. For Pipeline v2 Countries, `.github/workflows/publication-pipeline-v2-finalize.yml` performs finalization.

The workflow:

1. enters the shared `country-publication-main` serialization lane;
2. captures the target Country overlay;
3. fetches current `main`;
4. resets the working branch to latest `main` and reapplies only the target Country overlay;
5. finalizes terminal publication State and `atlasPublished:true` metadata;
6. runs Pipeline v2 publish checks on that exact terminal SHA;
7. retries from a newer `main` when `main` advances during the cycle, up to the configured limit;
8. squash-merges the **same reusable PR**;
9. waits for Cloudflare to expose the merged SHA;
10. smoke-tests the target Country route and JSON.

Directly merging latest `main` into the long-running Country branch is forbidden for this v2 path. A second publication PR is forbidden. A separate production-verification PR is also forbidden because the inline Cloudflare SHA/route smoke is authoritative.

## 9. Publication serialization

Country production and review QA may run in parallel. Final integration into `main` is intentionally serialized through the `country-publication-main` concurrency group so Pipeline v2 and legacy publication paths cannot race each other.

A publish cycle stops only for a concrete blocker such as:

- validation or Browser QA failure;
- unexpected conflict outside the known shared Country metadata scope;
- latest-main churn that does not stabilize within the configured cycles;
- merge rejection;
- Cloudflare failing to expose the merged SHA within the smoke window.

A successful external step must be reconciled into State by automation. ChatGPT is not the callback mechanism.

## 10. Content QA v6

See `docs/CONTENT_QUALITY_RULES_V6.md`. v6 inherits the Travel Scale contract from v4 and the Signature Facts / map-label rules from v5, then adds one-pass editorial settlement before Hero production.

Important v6 gates include:

- Signature Facts / Beyond the Scenery / Travel Trivia use different canonical subjects;
- Signature Facts must be distinctive and immediately understandable;
- ordinary population / area / density require `exceptionalScale:true` to be eligible;
- World Heritage and forest-share exception thresholds remain enforced;
- capital labels have an additional safety margin beyond the v5 geometric collision test;
- NEXT ROUTES preserves genuine traveler routes while recording current restriction status separately;
- Taste heading is fixed from the Country name;
- NEXT DESTINATIONS is affinity-based, not proximity-based, and requires `affinityType`;
- ENCOUNTERS must be broad, observable, and span at least four categories;
- deterministic `userGate:false` actions continue automatically to the next real gate.

Validation commands remain:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
python3 scripts/test_country_editorial_v2.py
python3 scripts/test_country_quality_v5.py
```

## 11. State initialization

For a new Country:

```bash
python3 scripts/country_production_protocol_v2.py init {slug}
```

New scaffolds use Publication Pipeline v2. Existing completed/already-integrated States and in-flight legacy Countries are not retroactively migrated unless migration is explicitly planned.

Validate the production and image-policy machinery with:

```bash
python3 scripts/country_production_protocol_v2.py validate
python3 scripts/image_policy_v72.py validate
```

## 12. Productivity targets

Normal new-Country targets:

- per-image approval prompts: 0;
- user continuation nudges during Scene/Taste rounds: 0;
- runtime-forced image turn boundaries: measured separately;
- Scene Batch reviews: 1;
- Taste Batch reviews: 1 unless a genuine REGEN batch is required;
- image handoffs: 1;
- reusable Review/Publication PRs: 1;
- pre-canonical main integrations: 0;
- persistent review deployment: 1;
- targeted Browser QA cycle: 1 under normal Country-only conditions;
- second publication PRs: 0;
- separate production-verification PRs: 0;
- final production integrations: 1;
- Country-only full-Country builds before approval: 0;
- Country-only full-Country Browser QA before approval: 0.

## 13. Authority

When Protocol 2 applies:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production-policy.json`
3. `ops/image-generation-policy.json`
4. this document
5. current image-policy revision docs
6. authoritative Country Production State
7. `docs/CONTENT_QUALITY_RULES_V6.md` for new v6 Countries; prior specs for legacy content versions
8. `docs/PUBLICATION_PIPELINE_V2.md` for v2 publication behavior
9. `docs/MAP_SYSTEM.md`
10. image/content/map specifications
11. chat history
