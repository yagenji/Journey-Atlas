# USER-APPROVED VISUAL POLICY WAIVER

Updated: 2026-09-16

Machine-readable authority: `ops/visual-policy-waiver-policy.json`.

## Purpose

This document defines a narrow **post-generation** exception path for an already-created visual that the user explicitly chooses to keep even though its generation provenance violated one specifically allowed non-visual generation rule.

This does **not** change normal image generation. `ops/image-generation-policy.json` remains authoritative for every new generation attempt.

## Allowed waiver

The only currently allowed violation code is:

- `PREVIOUS_IMAGE_REFERENCE_USED`

This means an image was generated with an earlier project image supplied as a reference even though the current Image Policy requires fresh text-to-image generation.

The waiver exists because the defect is in generation provenance rather than in the resulting visual target itself. It may be used only after the output already exists and the user explicitly approves keeping that exact output.

## Never waivable

A waiver must not be used for an output that fails any of the following:

- target identity;
- previous-asset repeat / restaging;
- wrong-target carryover;
- collage, multi-panel, grid, montage, or inset-image contamination;
- added typography;
- any other hard visual QA that makes the output unsuitable for the intended target.

The user may approve an aesthetic preference, but a waiver cannot relabel a hard visual failure as a compliant candidate.

## Required evidence

Every waiver must record:

- exact target scope;
- exact target → generation-ID mapping;
- `authorizedBy: USER_EXPLICIT`;
- user authorization timestamp;
- the user instruction that approved preserving the output;
- `preserveExistingImages: true`;
- `regenerationRequired: false`;
- hard visual QA with `targetIdentity`, `previousAssetRepeat`, and `collageTypography` all `PASS`;
- `status: STAGED | APPLIED`.

The record lives in `visualPolicyWaivers[]` in the Country Production State.

## State recovery

If the visual exists but reservation / reconciliation / batch state was not persisted correctly, use `docs/STATE_RECOVERY_MIGRATION.md` in addition to this waiver.

The waiver and the recovery solve different problems:

- waiver: acknowledges one allowed generation-provenance violation;
- recovery: reconstructs authoritative Production State around the already-existing generation IDs.

For Scene or Taste assets, approval must still be created from a real current batch-review boundary and recorded in the normal immutable batch ledger. A waiver never creates per-item Scene/Taste approval.

## Normal production remains unchanged

Do not proactively use image references because a waiver exists. The permitted path for all future generation remains:

`reserve → fresh text-to-image generate → reconcile/QA → batch boundary → approval`

A waiver is an exceptional preservation mechanism for an output the user has already chosen to keep, not an alternate generation workflow.
