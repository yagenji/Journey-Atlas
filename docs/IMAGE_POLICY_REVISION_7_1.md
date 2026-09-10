# JOURNEY ATLAS — Image Generation Policy Revision 7.1

Updated: 2026-09-10

Revision 7.1 is a throughput patch for Revision 7. It does not weaken any image-safety, target-synchronization, duplicate-prevention, or batch-approval rule.

The machine-readable authority remains `ops/image-generation-policy.json` on `main`.

## Goal

Normal production should behave like this:

- one generation request = one image;
- one image = one Scene or one Taste dish;
- different targets continue in the same assistant turn after successful reconciliation;
- S01–S08 reach one Scene batch review with no user interaction between valid targets;
- FOOD01–FOOD04 reach one Taste batch review with no user interaction between valid targets;
- GitHub state traffic must not become the throughput bottleneck.

Revision 7 fixed approval provenance and target synchronization. Revision 7.1 removes redundant repository round-trips that are not required for those guarantees.

## 1. Same-turn authoritative State chaining

At the start of a new assistant turn, read the current main image policy and authoritative Country Production State.

After a successful State write using the expected blob SHA, the exact State content just written and the returned content/blob SHA are authoritative for the remainder of that same assistant turn.

Do **not** immediately re-fetch the same State merely to confirm a write that GitHub already accepted.

Re-fetch is required only when:

- the assistant turn changes;
- the user or another actor may have modified the branch;
- a SHA/conflict error occurs;
- the State content is otherwise uncertain.

This preserves optimistic locking without paying an unnecessary read after every successful write.

## 2. Atomic reconcile + reserve-next transition

The pre-generation reservation remains mandatory. There must still be at most one unreconciled `GENERATING` target.

However, after a generated target passes reconciliation/QA, do not use two separate State writes for:

1. current target `GENERATING → REVIEW_CANDIDATE`;
2. next target `NOT_STARTED → GENERATING`.

When generation context is CLEAN and the next different target is known, perform both changes in **one State transition**:

- reconcile the current target;
- clear its reservation;
- persist its candidate/rejected generation information and `candidateVisualQa`;
- reserve the next different target with its own `generationReservation`;
- bind that reservation to exact asset id, contentId, promptSeries, and current generationContext epoch;
- persist once;
- generate the already-reserved next target immediately.

After that write, deterministic NEXT is `RECONCILE_GENERATION / {next target}`. The next image is therefore protected before its generation begins.

If the current output is a collage, repeat/restage, wrong-target carryover, or any failure that contaminates context, **do not reserve the next target** in the same transition. Route to `RESET_GENERATION_CONTEXT` instead.

## 3. Round-start Render Packet preflight

All Hero / Scene / Taste Render Packets are prepared before image generation and are validated by Production State rules.

At the start of `SCENES_INITIAL`, validate the complete S01–S08 Render Packet set once. At the start of `TASTE_INITIAL`, validate FOOD01–FOOD04 once.

Within the same uninterrupted assistant turn:

- use the frozen Render Packet in authoritative State as the target definition;
- do not re-read the Content Plan before every image;
- do not re-fetch unchanged Render Packets;
- rebuild/re-read only if contentId, promptSeries, target identity, or generationContext requires a reset/refresh.

The Content Plan remains the editorial source, but repeated per-target Content Plan reads are not a safety requirement once the round Render Packets have been validated.

## 4. Incremental all-prior visual comparison

The rule to compare each new output against all prior relevant Country images remains mandatory.

During one assistant turn, maintain the already-reviewed outputs as an incremental comparison set. Do not repeatedly re-fetch the same prior images from the repository when they are already present in the current generation context.

At a turn boundary or after context reset, reconstruct the comparison set from authoritative State/assets as needed.

This changes retrieval cost, not the duplicate-detection standard.

## 5. CI must not block image continuation

Per-image State commits on `country/**` branches are operational checkpoints. They must not require waiting for full repository regression CI before the next image generation.

Country-branch pushes run only the lightweight Revision 7 transition validation needed to verify the pushed State transition history.

Full initializer tests, approval-regression tests, complete State validation, and broader QA remain required on pull requests and `main`.

A successful GitHub State write is sufficient to continue to the next already-determined generation action. CI remains an asynchronous guard and may stop later integration if it fails.

## Expected normal-round repository traffic

Without atomic handoff, an eight-Scene round can require roughly one reservation write plus one reconciliation write per target, along with repeated reads.

With Revision 7.1:

- read policy + State once at turn/round start;
- reserve the first target once;
- after each image, one atomic reconcile/reserve-next State write;
- no confirmation re-read after an accepted write;
- one final reconcile write for the last target;
- one user review at the round boundary.

The same pattern applies to Taste.

The target is not zero State writes. The target is **one durable checkpoint per generated image, not two writes plus multiple reads per generated image**.

## Safety invariants that remain unchanged

Revision 7.1 must never be interpreted as permission to:

- generate more than one target in a single image request;
- have more than one unreconciled `GENERATING` target;
- generate the same asset twice in one assistant turn;
- continue after contaminated context;
- skip target identity QA;
- skip all-prior duplicate/restage QA;
- reuse a previous image as the next target's reference/edit source;
- approve Scene/Taste items individually;
- backfill batch approval provenance later.

Throughput optimization applies only to redundant repository orchestration around valid, different-target continuation.
