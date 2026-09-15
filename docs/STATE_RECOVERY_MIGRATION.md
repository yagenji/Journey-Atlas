# REVISION 7.2 — STATE RECOVERY MIGRATION

Updated: 2026-09-15

## Purpose

This procedure defines an exceptional **Production State reconciliation** path for a narrow orchestration failure: valid Scene or Taste outputs already exist, their exact generation IDs are known, and the user explicitly approved the existing batch, but the required reservation / reconciliation checkpoints were not persisted correctly.

It is not a raster-recovery workflow, not a generation shortcut, and not a validator bypass.

Normal Country production remains governed by:

- `ops/image-generation-policy.json` (`policyId: 7.2`);
- `ops/country-production-policy.json`;
- `docs/COUNTRY_PRODUCTION_PROTOCOL_2.md`;
- current Revision 7 transition validation.

Protocol 2 continues to forbid assistant-side raster recovery or materialization. This document only describes how authoritative State may be reconstructed around already-existing, independently identified outputs when the exceptional conditions below are satisfied.

## When recovery is allowed

All conditions are required:

- the image outputs already exist and their exact generation IDs are known;
- each recovered output maps unambiguously to exactly one expected target;
- the user explicitly approved the existing batch and explicitly authorizes State recovery instead of regeneration;
- the desynchronization was caused by orchestration / State persistence failure, not by a failed visual target;
- no recovered generation ID is already assigned to another target;
- target identity, all-prior novelty, single-frame / collage, typography, and other applicable candidate QA can still be established;
- already `APPROVED` production assets are not silently replaced;
- the recovery can pass the current Revision 7 static and transition validators without rewriting historical ledger entries.

If any condition is missing, do not use this procedure.

## Core rule

Recovery must not change untracked Scene/Taste assets directly to `APPROVED` and must not append a synthetic historical Batch ledger after approval already happened in State.

The recovery must reconstruct a **real current batch boundary first**, then apply approval in a separate normal batch-approval transition.

`recoveryMigrations[]` metadata records why the exceptional reconciliation occurred. It does not override validator rules.

## Transition 1 — RECOVERY STAGING

For the affected Scene or Taste batch:

1. Append a `recoveryMigrations[]` audit entry containing, at minimum:
   - a unique `id`;
   - `type: USER_APPROVED_EXISTING_BATCH_RECOVERY`;
   - `kind: SCENE | TASTE`;
   - a reason code describing the orchestration desynchronization;
   - the full recovery `scope`;
   - the exact recovered target → generation-ID mapping;
   - explicit user-authorization provenance and timestamp;
   - `preserveExistingImages: true`;
   - `status: STAGED`.
2. Restore every recovered target as `REVIEW_CANDIDATE` with its exact `candidateGenerationId`.
3. Record all candidate visual QA required by the current Image Policy, including target identity, all-prior novelty, and collage / typography checks. Taste recovery must also satisfy the current Taste composition checks.
4. Clear only stale reservation / contamination metadata that is proven to belong to the orchestration failure. Do not erase valid historical failure evidence.
5. Do not create or modify a batch approval ledger round in this transition.
6. The resulting State must deterministically reach the normal current Batch Review boundary (`BATCH_REVIEW_SCENES` / `WAIT_SCENE_BATCH_REVIEW` or `BATCH_REVIEW_TASTE` / `WAIT_TASTE_BATCH_REVIEW`).
7. Run the current State validator against this transition.

This staging transition reconstructs present candidate reality. It does not claim that approval was previously persisted correctly.

## Transition 2 — NORMAL BATCH APPROVAL

Only after Transition 1 has produced a true current Batch Review boundary:

1. Apply the user's explicit recovery authorization to that current batch boundary.
2. Convert the accepted recovered candidates to `APPROVED` using their exact recovered generation IDs.
3. Append exactly one normal immutable `sceneBatchReview.rounds[]` or `tasteBatchReview.rounds[]` entry in the same State transition.
4. Ensure the ledger `scope` equals all and only unapproved targets at that boundary.
5. Ensure `approvedGenerations` exactly matches the approvals created in this transition.
6. Put every rejected target, if any, in the ledger `regenerate` list and route it to `REGENERATE` under the current policy.
7. Set the corresponding Batch Review `approval` only when all targets satisfy the current ledger/state rules.
8. Update the matching recovery audit entry to `status: APPLIED` and record `appliedAt`.
9. Run the current State transition validator before advancing.

Because approval is created from a real current Batch Review boundary, this is not late historical backfilling.

## Hero recovery

Hero approval is individual under Image Policy 7.2 and is not a Scene/Taste batch ledger operation. This document does not create a new Hero approval mechanism.

If an existing Hero output needs exceptional State reconciliation, preserve the exact generation identity and explicit user-approval provenance and follow the current Hero State/approval rules. Do not reuse the Scene/Taste batch procedure as a synthetic Hero ledger.

## Prohibited uses

Do not use recovery to:

- rescue an image that failed target identity, novelty, composition, typography, or other hard visual QA;
- avoid regeneration merely because generation credits or time are scarce;
- invent, infer, or substitute a generation ID;
- map one generation ID to multiple targets;
- approve Scene/Taste items individually outside a Batch Review boundary;
- rewrite, delete, reorder, or late-backfill historical Batch ledger rounds;
- silently replace already approved assets;
- treat runtime/tool turn boundaries as user approval;
- materialize or reconstruct missing raster bytes in the repository;
- bypass current Image Policy 7.2, Protocol 2, Publication Pipeline v2, or transition validation.

## Normal production remains unchanged

For normal production, keep the current path:

`reserve → generate → reconcile/QA → reserve next target when valid → round boundary → Batch Review → Batch approval`

Recovery exists only for already-existing outputs after a proven orchestration / State-persistence desynchronization. It does not relax future generation, QA, handoff, review, or publication requirements.
