# REVISION 7 — STATE RECOVERY MIGRATION

Updated: 2026-09-11

## Purpose

This procedure is an exceptional recovery path for a specific orchestration failure: valid Scene or Taste images already exist and the user explicitly approved the batch, but Production State did not persist the required per-target reservation/reconciliation checkpoints.

It is **not** a bypass for normal Revision 7 generation, candidate QA, Batch Review, or approval provenance.

## When recovery is allowed

All conditions are required:

- the image outputs already exist and their exact generation IDs are known;
- each recovered output can be mapped unambiguously to exactly one expected target;
- the user explicitly approved the existing batch and explicitly authorizes recovery instead of regeneration;
- the desynchronization was caused by orchestration / State persistence failure, not by a failed visual target;
- no recovered generation ID is already assigned to another target;
- obvious collage, wrong-target, repeated/restaged, typography, or other hard-failure outputs are excluded;
- APPROVED production assets are not silently replaced.

## Core rule

Recovery must **not** directly change untracked assets to `APPROVED`, and must **not** append a synthetic historical Batch ledger to an already-approved State.

Instead, recovery reconstructs the missing batch boundary in two explicit State transitions.

### Transition 1 — RECOVERY STAGING

For the recovered batch:

1. Record an append-only `recoveryMigrations[]` entry with:
   - unique `id`;
   - `type: USER_APPROVED_EXISTING_BATCH_RECOVERY`;
   - `kind: SCENE | TASTE`;
   - `reasonCode: ORCHESTRATION_STATE_DESYNC`;
   - full recovery `scope`;
   - exact `recoveredGenerations` mapping;
   - `authorizedBy: USER_EXPLICIT`;
   - `authorizedAt`;
   - `preserveExistingImages: true`;
   - `regenerationForbidden: true`;
   - `status: STAGED`.
2. Restore each recovered target as `REVIEW_CANDIDATE` with its exact `candidateGenerationId`.
3. Record `candidateVisualQa` for target identity, all-prior novelty, and collage/typography checks.
4. Clear stale generation reservations and contamination latches.
5. Do not create an approval ledger yet.
6. State must deterministically reach the normal Batch Review boundary (`BATCH_REVIEW_SCENES` or `BATCH_REVIEW_TASTE`).

This staging transition reconstructs current candidate reality; it does not claim that approval was already recorded correctly.

### Transition 2 — NORMAL BATCH APPROVAL

Only after Transition 1 has created a true current Batch boundary:

1. apply the user's explicit recovery authorization / existing Batch approval;
2. convert the recovered candidates to `APPROVED`;
3. append exactly one normal immutable `sceneBatchReview.rounds[]` or `tasteBatchReview.rounds[]` entry;
4. ensure `scope` equals the full unapproved batch at that boundary;
5. ensure `approvedGenerations` exactly match the recovered candidate generation IDs;
6. set `regenerate: []` when the whole recovered batch is accepted;
7. set the corresponding Batch review `approval: APPROVED`;
8. update the recovery entry to `status: APPLIED` and record `appliedAt`;
9. advance to the normal next phase.

Because the approval ledger is created from a real current Batch boundary, this is not late backfilling of an already-approved State.

## Prohibited uses

Do not use recovery to:

- rescue an image that failed target identity or hard visual QA;
- avoid regeneration merely because credits are scarce when the image itself is invalid;
- invent a generation ID;
- map one generation ID to multiple targets;
- approve individual Scene/Taste items outside a Batch boundary;
- rewrite or delete historical Batch ledger rounds;
- modify already approved assets without explicit user instruction;
- treat runtime image-tool turn boundaries as approval.

## Normal production remains unchanged

Revision 7 / policyId 7.1 remains the normal path:

`reserve → generate → reconcile/QA → atomic reserve-next → Batch boundary → Batch approval`

Recovery is only a State reconstruction procedure for already-existing, explicitly user-approved output after an orchestration desynchronization. It does not relax future image-generation requirements.
