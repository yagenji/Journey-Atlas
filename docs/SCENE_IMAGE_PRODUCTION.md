# JOURNEY ATLAS — Scene Image Production Hard Rule

Updated: 2026-09-10
Policy revision: 6.1

## Scope

This is the canonical generation rule for Country Hero and S01–S08 scenic images.

It exists to prevent wasted generations from typography, poster layouts, collages, repeated previous assets, target-scene drift, and unnecessary per-image user interaction.

## Core rule

- One Scene = one standalone image file.
- One generation request = one current Scene target only.
- Never combine multiple Scenes into one collage, grid, contact sheet, poster, diptych, triptych, storyboard, or labelled panel.
- "Batch review" means one user review gate after the Scene round. It does not mean a collage.
- One independent image-generation request per Scene does **not** mean one user approval per Scene.
- Do not regenerate an APPROVED asset unless the user explicitly requests it.

## Mandatory prompt tail

Every Hero / Scene generation instruction must end with the following hard constraints, regardless of whether the Content Plan already says similar things:

```text
PURE SCENIC IMAGE ONLY.

No added text anywhere in the image.
No title, place name, country name, caption, letters, typography, labels, badges, logo, flag, map, UI, infographic, poster layout, border, frame, collage, grid, split panel, contact sheet, or decorative wording.

Do not invent readable signage. If real-world signage is unavoidable in the location, keep it incidental, small, visually subordinate, and not legible as generated text.

Generate only the specified real place and viewpoint. Do not reuse, restage, crop, or vary any previously generated Hero or Scene. Do not substitute another landmark from the same country.

Single standalone landscape image only.
```

The negative block is mandatory. Do not shorten it because the Content Plan already contains "no text".

## Render Packet input contract

Before a Hero or Scene generation call, the exact target must already exist in Production State as a complete `renderPacket`.

The generation instruction must be constructed from that packet plus the mandatory prompt tail. Do not use the previous image, a conversational shorthand such as "next", or only the Scene number as the target definition.

A valid packet must identify:
- `kind: HERO` or `kind: SCENE`;
- stable `contentId`;
- real place / subject;
- viewpoint and composition;
- season / light where relevant;
- independence from previous assets;
- `noAddedText:true`.

If the packet is incomplete, do not spend a generation credit.

## Single-frame prompt envelope — mandatory

For every Hero / Scene generation, the effective instruction begins with the semantic equivalent of:

> ONE SINGLE FULL-BLEED 3:2 LANDSCAPE FRAME. ONE PLACE. ONE CONTINUOUS CAMERA VIEW. NO COLLAGE, NO GRID, NO PANELS, NO CONTACT SHEET, NO MONTAGE, NO INSET IMAGE, NO BORDER, NO LABELS, NO MULTI-SCENE COMPOSITION.

Only after this fixed envelope may the current target identity be described.

Do not mention S01–S08 as a set, the other Scenes, "8 images", "batch", "series", "collection", or review layout in the generation instruction sent to the image model.

If a collage/multi-panel output occurs, mark generation context CONTAMINATED and stop image generation for that assistant turn. The next action is RESET_GENERATION_CONTEXT, not another Scene.

## Pre-generation reservation — mandatory

Before calling image generation for Hero or Scene:

1. Re-read authoritative Production State.
2. Confirm the exact NEXT target.
3. Write that target as `GENERATING` with a unique `generationReservation`.
4. Re-read and confirm NEXT becomes `RECONCILE_GENERATION / {same asset}`.
5. Only then generate the image.

Never generate first and plan to update State afterward.

If a previous generation is still `GENERATING`, reconcile it first. Do not call image generation again until reconciliation is complete.

The same Hero / Scene may be generated at most once in one assistant turn.

Every call must be a fresh independent text-to-image generation. Never use a previously generated image as an edit/reference source for the next target or regeneration.

## Preflight before every generation

Before calling image generation:

1. Resolve `stateRef` and read `ops/country-production/{slug}.json` from the authoritative reference (`country/{slug}` during active production, `main` from REVIEW onward).
2. Confirm `next.action` is a generation action.
3. Confirm the exact `next.asset`.
4. Read that asset's visual identity from the authoritative Content Plan on `contentRef`.
5. Compare the target identity with **all** previously generated or approved Hero / Scene assets in the same Country, not only the immediately previous asset:
   - contentId / location
   - main subject
   - terrain
   - architecture
   - season / light
   - composition
6. Confirm the target is not a duplicate target and is not accidentally carrying forward another Scene identity.
7. Append the mandatory prompt tail above.
8. Generate only the current target.

Do not generate from chat memory alone.

## Candidate visual novelty QA — mandatory

After every generated Hero / Scene, reconcile the existing `GENERATING` reservation before writing `REVIEW_CANDIDATE`:

1. Compare the output against the current Render Packet.
2. Compare it against **every** previously generated or approved Hero / Scene in the same Country.
3. Record `candidateVisualQa.targetIdentity = PASS`.
4. Record `candidateVisualQa.previousAssetRepeat = PASS` only after the all-prior comparison passes.
5. Record `candidateVisualQa.collageTypography = PASS`.

Checking only the immediately previous asset is insufficient.

If any earlier image is repeated, restaged, lightly cropped, or materially reused, reject it automatically. If the output belongs to another current-Country target rather than the current target, treat it as wrong-target carryover and reject it automatically. Do not ask the user to approve an obvious repeat or wrong target.

A new generation ID does not prove that the visual output is new.

## Contamination handling

The generation context becomes `CONTAMINATED` when any of these occurs:

- collage / grid / multi-panel / contact-sheet / montage output;
- a previously generated Country image is repeated or restaged;
- the image model carries another Scene/Hero target into the current target;
- repeated labelled/collage visual family persists across different targets.

On contamination:

1. reject and reconcile the affected generation;
2. set the affected asset to `REGENERATE`;
3. record the failure reason;
4. set `generationContext.state = CONTAMINATED`;
5. stop image generation for that assistant turn;
6. next action must be `RESET_GENERATION_CONTEXT`;
7. RESET is a no-image turn and must rebuild the next prompt from exactly one Render Packet.

## Immediate rejection

The output is automatic NG without waiting for user review if any of these occur:

- added title, place name, country name, caption, label or decorative typography;
- poster / brochure / postcard layout;
- collage, grid, split panel, contact sheet or multiple framed scenes;
- any previous Hero / Scene is repeated or restaged instead of the current target;
- wrong location / landmark or another Scene target is carried forward;
- map, UI, badge, border or frame appears;
- scene identity is materially inconsistent with the Content Plan.

For an automatic NG:
- record the generation as rejected;
- do not ask the user to judge an obvious hard-rule failure;
- do not materialize or store it as an approved asset;
- advance according to the Production State rules.

## Failure handling

For the same target:

- first hard failure: reject immediately;
- collage / repeat / wrong-target carryover: contaminate context and reset before another generation;
- second consecutive hard failure in one prompt family: reject, retain the asset for regeneration, and refresh that asset's prompt series;
- do not make a third near-identical attempt using the same prompt family;
- after reset/refresh, rebuild the prompt from the Content Plan + current Render Packet + mandatory prompt tail, with no reference to the failed output.

The failure limit prevents spending long periods and image credits on one broken prompt series.

## Scene round execution — hard throughput rule

Quality and asset identity remain more important than forcing multiple targets into one image-generation request. At the same time, State transitions must not become unnecessary user interaction gates.

During `SCENES_INITIAL`:

1. reserve the current `next.asset`;
2. generate exactly that one standalone Scene;
3. reconcile it;
4. run target / all-prior duplicate / collage QA;
5. persist it as `REVIEW_CANDIDATE` or `REGENERATE`;
6. re-read authoritative State;
7. if NEXT points to another `NOT_STARTED` Scene and generation context is CLEAN, reserve and generate that next Scene immediately;
8. repeat until no `NOT_STARTED` Scene remains or a real blocking condition requires the round to stop.

Hard interaction rules:

- Do **not** insert a user approval gate between S01–S08.
- Do **not** ask the user to type `approve`, `進めて`, `生成`, `next`, or equivalent between valid Scene generations.
- A valid Scene result is an internal production checkpoint, not a user interaction checkpoint.
- While sequential image-generation calls are technically available in the current assistant turn, do **not voluntarily return control** after a valid Scene; continue to the next Scene.
- Each Scene still uses its own independent image-generation request. Never merge several Scene targets into one prompt or one collage-oriented request.
- If the image runtime truly hard-stops the assistant turn after one generated image, that runtime boundary is not approval. On the next user message, reconcile if needed and immediately continue from NEXT without asking the user to review the previous valid candidate.
- Never claim all eight were generated unless eight independent outputs actually exist.

## Machine duplicate gate

After approved Scene assets are materialized, run:

`python3 scripts/validate_images.py --duplicates-only --slug {slug}`

Hero + 8 Scenes are checked pairwise for same-path reuse, normalized identical pixels, and conservative near-duplicate similarity. This remains a final machine safety gate; it does not replace the all-prior live visual comparison during generation.

A failure reopens only the affected Scene(s) for regeneration; the review package must not proceed.

## Batch review

Only after every Scene has one valid `REVIEW_CANDIDATE` or is marked `REGENERATE`:

- present the eight Scene results as one review gate;
- user approves the acceptable images together;
- regenerate only specified NG / REGENERATE assets;
- APPROVED assets are locked.

No individual Scene may be user-approved during `SCENES_INITIAL` / `SCENES_REVIEW`.

## Current production

Any Country already in HERO / SCENES / TASTE production must use the latest main image-generation policy starting with the next generation action. Existing APPROVED assets remain untouched.
