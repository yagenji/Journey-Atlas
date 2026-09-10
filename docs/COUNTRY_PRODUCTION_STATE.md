# COUNTRY PRODUCTION STATE — OPERATING CONTRACT

Updated: 2026-09-10
Current image policy: Revision 7 / policyId 7.1

## Purpose

Country production must not depend on chat memory, repeated user prompts, or redundant repository round-trips.

Operational progress lives at:

`ops/country-production/{slug}.json`

Image-generation rules live only in:

`ops/image-generation-policy.json` on `main`

Revision 7 rules are explained in `docs/IMAGE_POLICY_REVISION_7.md`.
Revision 7.1 throughput rules are explained in `docs/IMAGE_POLICY_REVISION_7_1.md`.

When this document conflicts with the current main image policy or its revision guide, the current main policy/revision guide wins.

## Authority and reference

During active production:

- `contentRef: country/{slug}`
- `stateRef: country/{slug}`

From REVIEW onward:

- `contentRef: main`
- `stateRef: main`

One Country has one State file. Parallel Country chats must not edit a shared cursor record.

## Turn-start rule

At the start of a new assistant turn that will act on Country production:

1. read `ops/image-generation-policy.json` from `main`;
2. resolve the authoritative Country State from `stateRef`;
3. read `next.action / next.asset`;
4. execute the deterministic next action.

Do not infer NEXT from chat history when State exists.

If State is missing, initialize it from actual repository / asset / publication reality before generating anything.

## Same-turn State chaining — policyId 7.1

Within the same assistant turn, do **not** re-fetch unchanged State after every successful write.

Use optimistic locking:

1. write the complete new State using the expected current blob SHA;
2. if GitHub accepts the write, the exact content just written plus the returned new blob SHA becomes authoritative for that same assistant turn;
3. derive the next deterministic action from that State locally;
4. continue without a confirmation fetch.

Re-fetch State only when:

- the assistant turn changes;
- the write reports a SHA/conflict error;
- another actor may have modified the branch;
- State content is genuinely uncertain.

Never force-overwrite a SHA conflict.

## Phase model

Allowed phases:

- `CONTENT`
- `HERO`
- `SCENES_INITIAL`
- `SCENES_REVIEW`
- `SCENES_REGEN`
- `TASTE_INITIAL`
- `TASTE_REVIEW`
- `TASTE_REGEN`
- `MAP`
- `ASSET_QA`
- `IMPLEMENTATION`
- `QA`
- `REVIEW`
- `PUBLISH` — legacy-readable only for Revision 7 normal flow
- `COMPLETE`

The phase answers only: **what may happen next?**

## Asset states

Hero / Scene / Taste / Map use:

- `NOT_STARTED`
- `GENERATING`
- `REVIEW_CANDIDATE`
- `REGENERATE`
- `APPROVED`

`GENERATING` means an exact target has been reserved before spending an image credit and has not yet been reconciled.

At most one unreconciled `GENERATING` target may exist.

## Render Packet — mandatory

Every Hero / Scene / Taste target must have a complete `renderPacket` before generation.

Minimum common identity:

```json
{
  "kind": "HERO | SCENE | TASTE",
  "contentId": "stable-content-id",
  "identity": "exact target identity",
  "independentGeneration": true,
  "forbidPreviousAssetReuse": true
}
```

Hero / Scene additionally require the single-scene / no-added-text contract.
Taste additionally requires single-dish / clean-neutral-background contract.

The Render Packet is the exact generation target. `S03`, `FOOD02`, chat shorthand, or the previous generated image is not a target definition.

At the start of a Scene or Taste round, validate the complete Render Packet set once. Within the same uninterrupted turn, do not re-read the unchanged Content Plan before every target.

Re-read/rebuild the relevant packet only after contentId change, prompt-series refresh, generation-context reset, turn boundary when needed, or conflict.

## Generation identity integrity

Within one Country State, a generation ID belongs to one asset only.

The same generation ID must never appear under different Hero / Scene / Taste targets, including rejected history.

Cross-target generation-ID reuse is a hard failure.

## Pre-generation reservation

Before spending an image credit, the target must already be persisted as `GENERATING` with a unique `generationReservation` bound to:

- exact asset id;
- exact `contentId`;
- `promptSeries`;
- current `generationContext.epoch`;
- reservation id / timestamp.

The State after reservation must deterministically route NEXT to:

`RECONCILE_GENERATION / {same asset}`

A successful reservation write authorizes generation. Under policyId 7.1, do not re-fetch merely to confirm your own accepted write.

The same target may be generated at most once in one assistant turn.

Every image call is fresh independent text-to-image. Never use the previous generated image as edit/reference input for another target or regeneration.

## Atomic reconcile + reserve-next — policyId 7.1

Normal valid rounds use one durable State checkpoint per generated image rather than separate reconcile and next-reservation commits.

After a generated target returns:

1. reconcile it against its exact reservation;
2. run candidate visual QA;
3. if valid, persist it as `REVIEW_CANDIDATE`;
4. if another **different** target remains and `generationContext` is CLEAN, reserve that next target as `GENERATING` in the **same State update**;
5. clear the previous reservation and create the new exact reservation atomically;
6. write once using the expected blob SHA;
7. generate the already-reserved next target immediately.

The atomic handoff must leave at most one unreconciled `GENERATING` target.

For the final target in a round, reconcile/persist it without reserving another target.

If current output contaminates generation context, do **not** reserve the next target in the same transition.

## Candidate visual QA

A generated image does not become `REVIEW_CANDIDATE` merely because generation completed.

For every output, verify:

```json
"candidateVisualQa": {
  "targetIdentity": "PASS",
  "previousAssetRepeat": "PASS",
  "collageTypography": "PASS"
}
```

`previousAssetRepeat` means comparison against **all** prior relevant Country outputs, not only the immediately previous image.

Within one assistant turn, maintain an incremental comparison set instead of repeatedly fetching the same prior images.

A new generation ID alone does not prove visual novelty.

## Hard visual failures and contamination

These are automatic failures:

- collage / grid / multi-panel / contact sheet / montage;
- repeated or materially restaged previous image;
- wrong-target carryover;
- target identity mismatch;
- prohibited text / labels / poster structure;
- Taste multi-dish or prohibited background objects.

For collage, repeat/restage, or wrong-target carryover:

1. reject and reconcile the current generation;
2. set target to `REGENERATE`;
3. record rejected generation id and failure reason;
4. set `generationContext.state = CONTAMINATED`;
5. do not reserve another target;
6. NEXT becomes `RESET_GENERATION_CONTEXT`;
7. stop image generation for that assistant turn.

Allowed contamination reasons:

- `COLLAGE_OR_MULTIPANEL`
- `PREVIOUS_ASSET_REPEAT`
- `WRONG_TARGET_CARRYOVER`

`RESET_GENERATION_CONTEXT` is a no-image action. It increments the context epoch, clears failure latch fields, and rebuilds the next prompt from exactly one current Render Packet.

## Prompt-series credit guard

Track `promptSeries` and `promptSeriesRejectCount` per target.

After two hard failures in one prompt family:

- do not make a third near-identical attempt;
- route NEXT to `REFRESH_RENDER_PACKET`;
- rebuild from authoritative target identity;
- increment prompt series;
- reset reject count;
- only then generate again.

## Scene round

### Initial

`SCENES_INITIAL` means S01–S08 each receive one independent initial attempt.

Normal execution:

`S01 → reconcile/reserve S02 → S02 → ... → S08 → Scene Batch Review`

Rules:

- one generation call per Scene;
- different targets continue automatically in the same assistant turn when the image tool returns control;
- failed targets become `REGENERATE` and are not immediately retried while later `NOT_STARTED` targets remain;
- no user approval request between S01–S08;
- stop for user review only at the Scene round boundary.

### Review / regeneration

Revision 7 approval provenance lives only in append-only:

`sceneBatchReview.rounds[]`

At the initial batch review:

- accepted candidates → `APPROVED`;
- NG candidates → `REGENERATE`;
- if any NG remains → `SCENES_REGEN`.

Previously batch-approved Scenes remain locked during regeneration.
New regenerated candidates remain `REVIEW_CANDIDATE` until the regeneration batch boundary.

Individual Scene `userApprovedAt` is forbidden.

## Taste round

Taste uses the identical structure:

`FOOD01 → reconcile/reserve FOOD02 → FOOD02 → FOOD03 → FOOD04 → Taste Batch Review`

Rules:

- one image = one dish;
- one generation request = one dish;
- no collage / multiple dishes;
- no user approval between FOOD01–FOOD04;
- NG targets enter `TASTE_REGEN`;
- regenerated targets are reviewed together at the regeneration boundary.

Approval provenance lives only in append-only:

`tasteBatchReview.rounds[]`

Individual FOOD `userApprovedAt` is forbidden.

## Batch approval validator

Revision 7 validation requires:

- approval only at a true batch boundary;
- exact approved generation IDs in the corresponding batch ledger round;
- batch scope equals all and only unapproved targets at that boundary;
- rejected targets are routed to `REGENERATE`;
- historical ledger rounds are immutable / append-only;
- a later synthetic Batch record cannot legitimize an earlier individual approval;
- previously approved assets stay immutable in later regeneration rounds.

Transition validation runs across commit history so late Batch backfill is detectable.

## User-facing approval gates

Normal production has four user-facing gates:

1. Hero approval
2. 8-Scene batch review
3. 4-Taste batch review
4. Canonical Country page review / publication approval

If a Scene/Taste regeneration round is needed, its affected targets are regenerated consecutively and reviewed once at that round boundary.

Image cards or runtime turn boundaries do not create approval gates.

## State-only writes are non-blocking

Active-production State writes go directly to `country/{slug}`.

Do not create PRs for per-image candidate/rejection/reservation progress.

Do not wait for GitHub Actions after a successful per-image State write before continuing to the next different target.

Country-branch Revision 7 CI is a lightweight asynchronous transition guard. Full regression runs on PR/main.

Do not inspect workflow runs after every Scene/Food unless a validation conflict or batch/phase boundary requires investigation.

## CI split — policyId 7.1

On `country/**` pushes:

- validate pushed Revision 7 State transition range only;
- do not rerun initializer self-tests and approval-regression suites for every image checkpoint.

On PR / `main`:

- compile validators;
- run initializer self-test;
- run approval/throughput regression tests;
- validate current State set;
- validate commit transition history.

This reduces operational load without weakening final integration gates.

## Machine duplicate gate

After approved assets are materialized, run:

`python3 scripts/validate_images.py --duplicates-only --slug {slug}`

The machine gate checks path reuse, normalized identical pixels, and conservative near-duplicates across Hero/Scenes and across Taste items.

This final gate supplements, not replaces, live all-prior QA during generation.

## Batch materialization

Do not recover / convert / resize / rename / commit each generated image separately during the generation round.

After Scene batch approval:

- materialize approved Scene assets together;
- convert/resize together;
- place into final Country folder together;
- verify together.

Do the same after Taste batch approval.

## Post-visual auto pipeline

After Hero + Scenes + Taste are approved, normally no user input is needed until canonical-page review.

Auto-chain:

1. batch materialize approved visual assets;
2. decode / dimensions / path / hygiene QA;
3. build and QA Map;
4. implement Country JSON and taxonomy;
5. run source/data validation;
6. prepare one Review Package integration;
7. integrate to `main` once for review deployment;
8. run targeted Desktop / Tablet / Mobile QA for that Country;
9. write `phase: REVIEW`;
10. present the canonical URL.

Do not pause merely to report intermediate progress.

## Review / publication

`REVIEW` means:

- all required visual assets approved;
- implementation complete;
- QA passed;
- canonical review deployment exists;
- `atlasPublished:false`;
- `stateRef: main` / `contentRef: main`.

After explicit page-level publication approval, do not create a separate State-only PUBLISH PR.

Use one terminal publication PR that sets together:

- `finalApproval.state = APPROVED`;
- `phase = COMPLETE`;
- `publication.state = PUBLISHED`;
- `publication.atlasPublished = true`;
- `qa.productionState = CI_GATED` or supported PASS legacy value;
- `publication.productionVerification = CI_GATED` or supported PASS legacy value;
- renewal status production marker;
- `next.action = NONE`.

After merge, Cloudflare Production verification is the authoritative external production record. Do not create another PR only to write the workflow result back into State.

## Main integration rule

Normal main integration count:

- active per-image State cursor writes: **zero main integrations**;
- review package: **one main integration**;
- State-only publication approval: **zero integrations**;
- formal publication after user approval: **one final main integration**;
- post-publication State normalization: **zero integrations**.

Do not create derivative publish / QA / state-only branches for normal Country production.

## Content Plan / Production State separation

`docs/*_CONTENT_PLAN.md` answers **what to make**.

`ops/country-production/{slug}.json` answers **where production currently is**.

Content Plans must not contain live operational state such as:

- current phase;
- NEXT ACTION / NEXT ASSET;
- current approval states;
- generation cursors;
- regeneration attempt logs;
- temporary failure-state corrections;
- current review/publication state.

Reusable lessons from production incidents belong in global production specifications, not Country Content Plans.

## Commands

For Revision 7 active production:

Validate:

`python3 scripts/country_production_state_v7.py validate`

Show NEXT:

`python3 scripts/country_production_state_v7.py next {slug}`

Initialize a new Country:

`python3 scripts/country_production_state_v7.py init {slug}`

Validate a commit range:

`python3 scripts/country_production_state_v7.py validate-range {base} {head}`

The legacy `scripts/country_production_state.py` remains available for compatibility with older completed State records, but must not be used to initialize a new active Revision 7 Country.

## Canonical new-Country start

Use:

`docs/NEW_COUNTRY_START.md`

Do not ask the user to repeat a long master prompt when repository rules and Production State already exist.

The chat is not an operational source of truth.
