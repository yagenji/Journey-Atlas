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
