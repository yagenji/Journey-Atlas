# USER-APPROVED VISUAL POLICY WAIVER

Updated: 2026-09-16

Machine-readable authority: `ops/visual-policy-waiver-policy.json`.

## Normal rule remains in force

For every *future* request: one image-generation request = one FOOD target = one independent image. Fresh text-to-image, advance reservation, target reconciliation, Taste composition, no text/collage and batch approval all remain required. This document authorizes no future grouped generation. It is a narrow **post-generation** preservation mechanism only.

## Permitted generation-provenance waivers

- `PREVIOUS_IMAGE_REFERENCE_USED`: an already-existing output was generated with a previous image supplied as a reference. Explicit post-generation user authorization is required.
- `MULTIPLE_OUTPUTS_ONE_REQUEST`: **one closed historical case only**, identified by `closedHistoricalCaseId: elsalvador-taste-four-20260916` in the policy. On 2026-09-16 one image-tool request returned four separate, distinct single-dish outputs for El Salvador FOOD01–FOOD04. Each output has its own exact generation ID, and the user approved their appearance and explicitly said `採用` after the generation-unit violation was explained. This is **not** permission to request four outputs together in future. Only the slug, four targets and four generation IDs fixed in the machine-readable historical case are eligible.

The second code refers to the **generation request grouping**, not to a collage or multi-panel image. A collage, a wrong dish, added typography, a duplicate, or any other hard visual QA failure is never waivable.

## Required evidence and safeguards

Every waiver must include its exact target scope and unique generation IDs, user authorization and timestamp, user instruction, `preserveExistingImages: true`, `regenerationRequired: false`, applicable hard visual QA PASS fields, and `status: STAGED | APPLIED`. The closed historical case also requires `closedHistoricalCaseId` and must exactly match the policy's slug, kind, scope and generation IDs; a different target, generation, country or reused case ID is rejected by the validator.

If reservation/reconciliation history is missing, use `docs/STATE_RECOVERY_MIGRATION.md` separately. First reconstruct a real current batch boundary as REVIEW_CANDIDATE with a STAGED waiver and recovery audit; only afterward may a second normal Batch Review transition create approvals and the immutable ledger. No retrospective fabricated reservation or late ledger backfill is allowed. The exception does not permit assistant-side raster materialization, skip image decode/dimension audits, or authorize publication before final page approval.
