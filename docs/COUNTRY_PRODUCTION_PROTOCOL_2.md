# JOURNEY ATLAS — Country Production Protocol 2.0

Updated: 2026-09-12
Current policy patch: 3

Machine-readable authority: `ops/country-production-policy.json`.
Image-generation authority remains `ops/image-generation-policy.json`.

Protocol 2.0 is the default for **new Country production**. Patch 3 preserves the post-image fast path and adds stricter image-round interaction and Taste controls based on the Philippines / Singapore / Thailand / Vietnam / Brunei production review.

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
→ target Country QA
→ sync latest main once
→ open ONE pre-main review PR
→ PR automatically triggers target-only Browser QA + persistent GitHub Pages review
→ final Country-page user approval
→ finalize THE SAME PR to terminal publication State
→ serialized publication queue syncs latest main, waits required checks and squash-merges
→ one Cloudflare production deployment + targeted production verification
```

**Main is not the review environment. A second publication PR is forbidden.**

## 1. Pre-visual build is mandatory

Before Hero generation, finish everything that does not require the final raster bytes:

- Country JSON editorial content;
- final Hero / S01–S08 / FOOD01–04 paths;
- Scene coordinates;
- Map build and QA;
- taxonomy;
- Related Countries;
- Next Routes or intentional omission;
- Travel Scale;
- Signature Facts;
- sources/source dates;
- Content QA v2.

`preVisualBuild.state` and every required check must be `PASS` before leaving CONTENT. Map must already be `APPROVED`.

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

Protocol 2 Patch 3 metrics:

- `productionMetrics.perImageApprovalPrompts` target `0`;
- `productionMetrics.userContinuationNudges` target `0`;
- `productionMetrics.runtimeForcedImageTurnBoundaries` is measured but allowed.

## 3. Taste first-pass and REGEN are separate rounds

Taste follows Image Policy 7.2.

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
3. run target Desktop / Tablet / Mobile Browser QA once;
4. do not build or QA unrelated Countries;
5. do not run Cloudflare production before final page approval.

The targeted builder remains:

```bash
python3 scripts/build_country_preview_targeted.py --slugs {slug}
```

Full-Country build/QA is reserved for shared template/CSS/JS/build-system changes, explicit Full QA, and the real final production deployment.

The `Validate country data` workflow does **not** rebuild the targeted preview package when `browser-country-qa` already owns that build. This removes the previous duplicate targeted package build.

## 6. One pre-main Review PR triggers Preview automatically

After `phase: QA` and target QA `PASS`, Protocol 2 NEXT returns:

```text
OPEN_REVIEW_PR_FOR_TARGETED_PREVIEW
```

Before opening the PR, sync the Country branch with current `main` once. Then open **one** PR from `country/{slug}` to `main` while:

- `atlasPublished:false`;
- `phase: QA`;
- `stateRef/contentRef: country/{slug}`;
- `finalApproval.state: PENDING`.

Opening or synchronizing that PR automatically triggers `.github/workflows/deploy-country-preview.yml`. No `.github/preview-trigger/**` commit and no manual dispatch is needed in the normal path.

The PR remains open through final user review. It is reused for publication after approval.

## 7. Persistent Country review URLs

GitHub Pages is one deployment surface, but each Country now lives in its own persistent subtree:

```text
/reviews/{slug}/countries/{slug}/
```

A later Country review therefore does not overwrite the earlier Country URL.

Implementation rules:

- snapshot branch: `review-previews`;
- maximum retained review snapshots: 8;
- the current Country replaces only its own `/reviews/{slug}/` subtree;
- other active review subtrees are preserved;
- already-published previews are pruned when the next review snapshot is staged;
- oldest snapshots beyond the retained maximum are pruned;
- target raster URLs are rewritten to the immutable `raw.githubusercontent.com/.../{commit}/assets/images/...` origin so the persistent Pages snapshot does not duplicate all Country image bytes;
- the `review-previews` branch is a generated review cache, never production authority.

After the Pages deployment and Browser QA pass, record:

```json
"reviewPreview": {
  "mode": "TARGETED_COUNTRY_BRANCH_PREVIEW",
  "state": "DONE",
  "url": "https://.../reviews/{slug}/countries/{slug}/",
  "browserQa": "PASS"
}
```

Protocol NEXT then returns `REVIEW_CANONICAL_URL` as the final user gate.

## 8. Final approval reuses the same PR

After explicit user approval, Protocol NEXT returns:

```text
FINALIZE_REVIEW_PR_FOR_PUBLICATION
```

Do **not** create another PR.

Finalize the existing Country branch/PR to the normal terminal publication representation, including:

- `finalApproval.state: APPROVED`;
- `publication.state: PUBLISHED`;
- `publication.atlasPublished: true`;
- matching destination-registry `atlasPublished:true`;
- terminal `phase: COMPLETE`;
- `stateRef: main` and `contentRef: main`;
- supported CI-gated production verification fields required by the legacy State validator.

Because this final commit is publication metadata/state only, local PR Browser QA may skip redundant rendering work; the already-passed persistent review remains the visual approval source.

## 9. Serialized publication queue

`.github/workflows/publish-country-queue.yml` is the final integration queue.

It acts only when all of the following are true:

- Protocol 2 State;
- final approval is explicit;
- persistent review is `DONE` with Browser QA `PASS`;
- terminal publication State is complete;
- registry and State both say `atlasPublished:true`.

The queue has one global concurrency lane. For each ready Country it:

1. fetches latest `main`;
2. merges latest `main` into the Country branch when needed;
3. pushes the synchronized branch;
4. waits for repository-required `validate` and `browser-qa` checks on that exact head;
5. confirms `main` has not advanced again;
6. squash-merges the existing PR;
7. retries synchronization if `main` advanced while checks were running.

This matches the repository Ruleset's strict up-to-date requirement while preventing multiple Countries from repeatedly invalidating each other's final checks.

Country production can remain parallel; **main publication is intentionally serial**.

## 10. Content QA v2

See `docs/CONTENT_QUALITY_RULES_V2.md`.

Hard rules include:

- every Travel Scale item contains a concrete `例：`;
- forest/woodland percentage is not a routine Signature Fact; it requires `exceptionalShare:true` and must be <=10% or >=70%.

For Country-only work, Content QA targets the Country. Full Content QA is reserved for shared/full-scope changes.

## 11. State initialization

For a new Country:

```bash
python3 scripts/country_production_protocol_v2.py init {slug}
```

Protocol 2 intentionally stays in legacy `phase: QA` during pre-main review because legacy `REVIEW` requires `main` authority.

Validate with:

```bash
python3 scripts/country_production_protocol_v2.py validate
python3 scripts/image_policy_v72.py validate
```

Existing completed/already-integrated States are not retroactively migrated. Active image production must follow the current main policy before another image generation occurs.

## 12. Productivity targets

Normal new-Country targets:

- per-image approval prompts: 0;
- user continuation nudges during Scene/Taste rounds: 0;
- runtime-forced image turn boundaries: measured separately, not treated as approvals;
- Scene Batch reviews: 1;
- Taste Batch reviews: 1 unless a genuine REGEN batch is required;
- image handoffs: 1;
- Review PRs: 1;
- pre-canonical main integrations: 0;
- persistent review deployment: 1;
- targeted Browser QA cycle: 1;
- publication PRs created after approval: 0 — reuse the Review PR;
- final production integrations: 1;
- Country-only full-Country builds before approval: 0;
- Country-only full-Country Browser QA before approval: 0.

Measure Taste Batch approval → review URL ready, publication queue synchronization cycles, and final main integration count.

## 13. Authority

When Protocol 2 applies:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production-policy.json`
3. `ops/image-generation-policy.json`
4. this document
5. current image-policy revision docs
6. authoritative Country Production State
7. image/content/map specifications
8. chat history
