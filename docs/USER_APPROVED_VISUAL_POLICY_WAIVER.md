# USER-APPROVED VISUAL POLICY WAIVER

Updated: 2026-09-16

Machine-readable authority: `ops/visual-policy-waiver-policy.json`.

## Normal rule remains in force

For every *future* request: one image-generation request = one image target = one independent image. Fresh text-to-image, advance reservation, target reconciliation, image composition, no text/collage and the relevant approval gate all remain required. This document authorizes no future grouped generation. It is a narrow **post-generation** preservation mechanism only.

## Permitted generation-provenance waivers

- `PREVIOUS_IMAGE_REFERENCE_USED`: an already-existing output was generated with a previous image supplied as a reference. Explicit post-generation user authorization is required.
- `MULTIPLE_OUTPUTS_ONE_REQUEST`: only the **closed historical cases** enumerated by exact slug, kind, target IDs and generation IDs in `ops/visual-policy-waiver-policy.json` qualify. Each existing output must be a separate, independently identified single-target image. This code concerns the grouping of the original image-tool request, *not* collage/multi-panel pixels. The user must explicitly authorize preserving the exact images after the generation-unit defect is explained.

Current closed cases are El Salvador's four Taste outputs (`elsalvador-taste-four-20260916`), Antigua & Barbuda's eight Scene outputs (`antiguabarbuda-scenes-eight-20260916`), and Antigua & Barbuda's four Taste outputs (`antiguabarbuda-taste-four-20260916`). Antigua's Scene and Taste images had their own generation IDs but were returned as two multi-output requests. The user approved the existing batches and explicitly authorized a case-specific exception on 2026-09-16 after being informed of the grouped-generation violation. None of these cases permits new grouped generation, a different image, or reuse of a generation ID for another target.

## Required evidence and safeguards

Every waiver must include its exact target scope and unique generation IDs, user authorization and timestamp, user instruction, `preserveExistingImages: true`, `regenerationRequired: false`, applicable hard visual QA PASS fields, and `status: STAGED | APPLIED`. A grouped-generation waiver also requires the exact `closedHistoricalCaseId` and must match the policy's slug, kind, scope and generations. The validator rejects a different country, target, generation or reused case ID.

Wrong target, duplicate/restaged imagery, collage, typography, or any other hard visual QA failure remains **unwaivable**. A visual-policy waiver is not visual approval. If reservation/reconciliation history is missing, use `docs/STATE_RECOVERY_MIGRATION.md` separately: first reconstruct an actual current batch boundary with `REVIEW_CANDIDATE`, a STAGED recovery record and STAGED waiver; only then make a second normal batch-approval transition with an immutable ledger. Do not fabricate historical reservations or backfill a ledger after approval.

The exception does not authorize assistant-side raster materialization, skipping image decode/dimension and browser QA, bypassing the user-owned raster handoff, or publication before final page approval.
