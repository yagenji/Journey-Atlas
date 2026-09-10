# JOURNEY ATLAS — Image Generation Policy Revision 7

Updated: 2026-09-10

This document explains the operational change from revision 6.1 to revision 7. The machine-readable authority remains `ops/image-generation-policy.json` on `main`.

## Why revision 7 exists

Revision 5/6 correctly added pre-generation reservation and reconciliation, but the safety lock was allowed to dominate throughput. In practice, different Scene / Taste targets could degrade into one-image-per-user-interaction even though batch approval was the intended workflow.

Revision 7 separates two concepts that must not be conflated:

- **generation unit**: one target, one independent image-generation call;
- **user approval unit**: one complete Scene/Taste round.

## Non-negotiable execution model

### Scenes

`S01 → S02 → S03 → S04 → S05 → S06 → S07 → S08`

Each target uses a separate image-generation request. After each valid result:

1. reconcile the exact reserved target;
2. run target identity / all-prior duplicate / collage QA;
3. persist `REVIEW_CANDIDATE` or `REGENERATE`;
4. re-read State;
5. if the next different target is available and context is CLEAN, continue immediately in the same assistant turn when the image tool returns control.

Do not request user approval between valid Scene targets.

The user review gate occurs only when the round reaches the batch boundary.

### Taste

The identical rule applies to `FOOD01 → FOOD02 → FOOD03 → FOOD04`.

One dish remains one independent image-generation call. Approval occurs only after the round boundary.

## Different-target same-turn continuation

`maxSameAssetGenerationsPerTurn = 1` protects one target from accidental repeated spending. It does **not** limit different targets to one generation per assistant turn.

An unreconciled `GENERATING` reservation blocks further image generation only until that exact target is reconciled. After successful reconciliation, a different target may be reserved and generated immediately.

If the image runtime truly terminates the assistant turn, that is a transport boundary, not an approval boundary. The next user message resumes the next State action without asking for approval of the previous valid candidate.

## Target synchronization

Before every generation, the reservation must bind:

- exact asset id;
- exact `contentId`;
- current Render Packet;
- current `generationContext.epoch`;
- deterministic `next.asset`.

A generation may be reconciled only to that reservation. A result that visually belongs to another current-Country target is `WRONG_TARGET_CARRYOVER`, not a valid candidate.

Wrong-target carryover, previous-image repeat/restage, and collage/multi-panel output all contaminate generation context and require `RESET_GENERATION_CONTEXT` before another image is generated.

Repository rules can guarantee State/target synchronization and stop propagation after a bad generation. They cannot guarantee that the image model will never visually drift on the first attempt; that is why target-identity reconciliation remains mandatory.

## Batch approval provenance

Revision 7 closes the approval loophole in both initial and regeneration phases.

For Scenes and Taste, approval provenance lives only in an append-only batch ledger:

- `sceneBatchReview.rounds[]`
- `tasteBatchReview.rounds[]`

Each round records:

- `round`;
- `reviewBoundary: true`;
- `scope` — all unapproved targets at that round boundary;
- `approvedGenerations` — asset id → exact generation id approved in that batch;
- `regenerate` — the remaining targets rejected in the same batch;
- `approvedAt`.

An individual Scene/Taste `userApprovedAt` field is invalid under revision 7.

Every currently `APPROVED` Scene/Taste generation must be covered by an immutable ledger entry matching its exact `approvedGenerationId`.

## REGEN rule

Previously batch-approved assets remain `APPROVED` and locked during `SCENES_REGEN` / `TASTE_REGEN`.

Regenerated targets must become `REVIEW_CANDIDATE` first. They may become `APPROVED` only in the next batch-review transition after all targets in that regeneration round reach the boundary.

Therefore revision 7 does **not** simply ban `APPROVED` assets in REGEN. It distinguishes:

- previously batch-approved assets — allowed and immutable;
- newly regenerated candidate approved individually — forbidden;
- newly regenerated candidate approved at a valid batch boundary with ledger provenance — allowed.

## Transition validator

`scripts/country_production_state_v7.py` validates both the current State and every commit transition.

The transition validator rejects:

- Scene/Taste approval without a new batch-ledger round in the same transition;
- a ledger round added when the previous State was not at a true batch boundary;
- late backfilling or editing of historical ledger rounds;
- ledger scope that does not equal all and only unapproved targets at the boundary;
- approved generation ids that do not match the exact State generation ids;
- rejected targets that are not routed to `REGENERATE`;
- changes to previously approved assets inside a later regeneration batch.

The dedicated workflow runs on `main`, pull requests, and `country/**` branch pushes and validates every commit in the pushed range. This prevents a sequence of individual approvals followed later by a synthetic batch record from passing unnoticed.

## New State initialization

New Country production should use:

```text
python3 scripts/country_production_state_v7.py init {slug}
```

The resulting State uses revision 7, batch ledgers, different-target continuation, target epoch binding, and regeneration batch enforcement.

## User interaction target

Normal Country production should require user approval only at these points:

1. Hero
2. 8-Scene batch review
3. Taste batch review
4. Canonical Country page review / publication approval

If a regeneration round is required, its affected targets are regenerated consecutively and reviewed together at the regeneration batch boundary; individual image approval is still prohibited.
