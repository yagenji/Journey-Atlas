# COUNTRY PRODUCTION STATE — OPERATING CONTRACT

Updated: 2026-09-08

## Purpose

Parallel Country production must not depend on chat memory.

The authoritative operational state for each active or recently completed Country lives at:

`ops/country-production/{slug}.json`

One country = one state file. Separate files prevent parallel Country chats from editing the same record.

## Absolute execution rule

Before acting on `生成`, `進めて`, `次`, `続けて`, approval, regeneration, QA, review, or publish instructions:

1. Read the Country state file from **main**.
2. Read `next.action` and `next.asset`.
3. Execute only that action.
4. Update the state immediately after the transition.
5. Re-read before the next action.

Do not derive NEXT from conversation memory when a state file exists.

If a state file is missing, initialize it from the actual repository/asset/publication state before generating anything.

## Optimistic locking

When updating a state file, use the current blob SHA returned by GitHub.

If the write fails because the SHA changed:
- re-fetch the state;
- do not overwrite blindly;
- continue from the newer state.

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
- `PUBLISH`
- `COMPLETE`

The phase is operational, not editorial. It answers: **what can happen next?**

## Asset states

Hero / Scene / Taste / Map:

- `NOT_STARTED`
- `REVIEW_CANDIDATE`
- `REGENERATE`
- `APPROVED`

Do not use `APPROVED` unless the user has actually approved that asset, except when initializing from an already published/review-deployed page whose approved production assets are already authoritative.

## Scene initial round

During `SCENES_INITIAL`:
- generate the first `NOT_STARTED` Scene;
- a failed Scene becomes `REGENERATE`;
- continue to later `NOT_STARTED` Scenes;
- do **not** immediately retry the failed Scene;
- when no `NOT_STARTED` Scene remains, move to batch review.

This preserves the rule: one initial attempt per Scene per round.

After batch review:
- approved candidates → `APPROVED`;
- only requested/failed items → `REGENERATE`;
- if any regeneration remains → `SCENES_REGEN`;
- otherwise proceed to Taste.

## Taste initial round

The same rule applies to Taste:
- FOOD01–04 are independent generations;
- failed items become `REGENERATE`;
- finish all `NOT_STARTED` items before batch review;
- only NG items enter `TASTE_REGEN`.

## next object

Every state file stores:

```json
"next": {
  "action": "GENERATE_SCENE",
  "asset": "S04"
}
```

The stored value must match the deterministic result from:

`python3 scripts/country_production_state.py next {slug}`

CI validates this.

## Review / publish

`REVIEW` means:
- all visual assets approved;
- implementation complete;
- QA passed;
- canonical review deployment exists;
- `atlasPublished:false`;
- next action is review of the canonical URL.

`PUBLISH` is entered only after explicit page-level user approval.

`COMPLETE` requires:
- formal publication;
- `atlasPublished:true`;
- final approval recorded;
- production QA passed;
- `next.action = NONE`.

## State update examples

### After S04 generation succeeds

Before:
- phase: `SCENES_INITIAL`
- S04: `NOT_STARTED`
- next: `GENERATE_SCENE / S04`

After:
- S04: `REVIEW_CANDIDATE`
- next becomes first remaining `NOT_STARTED` Scene.

### After S04 generation fails

After:
- S04: `REGENERATE`
- while later `NOT_STARTED` Scenes exist, NEXT must point to the next unstarted Scene.
- do not retry S04 immediately.

### After user approves Scene batch except S04

- all accepted Scenes → `APPROVED`
- S04 → `REGENERATE`
- phase → `SCENES_REGEN`
- next → `GENERATE_SCENE / S04`

### After final page approval

- `finalApproval.state = APPROVED`
- phase → `PUBLISH`
- next → `PUBLISH_COUNTRY`

## Central state and content branches

State files are operational metadata and live on `main`.

`contentRef` records where the current Country implementation is authoritative:
- early production may point to `country/{slug}`;
- after review deployment it is normally `main`.

The state file does not replace Country JSON, approved assets, taxonomy, or registry. It only controls production sequencing.

## Commands

Validate all states:

`python3 scripts/country_production_state.py validate`

Show deterministic next action:

`python3 scripts/country_production_state.py next ukraine`

Show all tracked countries:

`python3 scripts/country_production_state.py summary`


## Canonical new-Country start

The reusable start instruction lives at:

`docs/NEW_COUNTRY_START.md`

For a new Country:

1. read `ops/country-production/{slug}.json` from `main`;
2. if it exists, resume exactly from its deterministic NEXT;
3. if it does not exist, inspect the actual registry / Country JSON / assets / branch state and initialize the State once;
4. create or update the Content Plan only for editorial and visual-design intent;
5. do not copy operational cursor information into the Content Plan;
6. proceed through the State machine without asking the user to repeat a master prompt.

The chat is not an operational source of truth.

## Content Plan / Production State separation — mandatory

`docs/*_CONTENT_PLAN.md` answers **what to make**.

`ops/country-production/{slug}.json` answers **where production currently is**.

Content Plans must not contain:
- current PHASE;
- current NEXT ACTION / NEXT ASSET / NEXT IMAGE;
- current approval states such as `Image state: APPROVED`;
- generation cursors;
- regeneration attempt logs;
- temporary failure-state corrections;
- current review / publication state;
- a duplicate production-gate sequence.

Historical production incidents that reveal a reusable rule belong in the relevant global production specification, not in a Country Content Plan.

Operational sequencing, asset state and publication state must be read only from the Production State on `main`.

## Throughput mode — mandatory

The production state machine exists to prevent duplicate work. It must **not** create a user approval gate after every image.

### User approval gates

There are only four normal user-facing gates:

1. Hero approval
2. 8-Scene batch review
3. 4-Taste batch review
4. Final canonical-page review / publication approval

Scene-by-Scene and Food-by-Food user approval is prohibited during the initial production round.

### Auto-continue inside image rounds

During `SCENES_INITIAL`:

- after S01 generation, write S01 as `REVIEW_CANDIDATE` or `REGENERATE`;
- immediately re-read NEXT;
- if another Scene is `NOT_STARTED`, generate it in the **same assistant turn**;
- repeat until S01–S08 have all received one initial attempt;
- do not emit an approval request between images;
- stop only when NEXT reaches the Scene batch-review boundary.

During `TASTE_INITIAL`, use exactly the same behavior for FOOD01–FOOD04.

The image generation UI may produce separate image cards. That does not create separate user approval gates.

### State-only writes are non-blocking

State must still be written after each generation so another chat cannot regenerate the same asset.

However:

- do not wait for GitHub Actions after a state-only write;
- do not inspect workflow runs after every Scene/Food;
- re-fetch the state file and continue immediately;
- run/inspect state validation only at a batch or phase boundary, or when a write/validation conflict occurs.

### Batch materialization

Do not recover, convert, optimize, rename, or commit each generated image separately.

During image production, store the generation identity/state only.

After the user approves the Scene batch:
- recover/materialize the approved Scene assets together;
- convert/resize them together;
- place them into the approved Country folder together;
- verify the batch together.

Do the same after Taste batch approval.

This preserves one-image-one-generation while removing repeated post-processing overhead.

### Post-visual auto pipeline

After Hero + 8 Scenes + 4 Taste images are approved, no further user input is normally required until the canonical Country page is ready for review.

Auto-chain:

1. batch materialize approved visual assets;
2. full decode / dimensions / path / hygiene QA;
3. build and QA the Map;
4. implement Country JSON and taxonomy;
5. run source validation;
6. prepare one review-deployment integration;
7. merge/integrate to main **once** for review deployment;
8. wait for the production commit once;
9. run targeted Desktop / Tablet / Mobile QA for that Country;
10. write `phase: REVIEW` and present the canonical URL.

Do not pause between these steps merely to report progress.

### Main integration rule

Country visual production stays on the Country working branch.

Do not merge/push individual approved images, Map work, asset QA work, and JSON implementation to main as separate production changes.

Normal pre-review integration count:

- state-only metadata writes to main: allowed and non-deploying;
- Country content/assets: **one main integration when the review package is complete**.

Formal publication after user approval is a second small main change that switches publication state.

This rule prevents repeated deployment / Cloudflare propagation / production QA cycles.
