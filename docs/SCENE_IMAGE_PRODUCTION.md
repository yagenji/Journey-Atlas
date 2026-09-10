# JOURNEY ATLAS — Scene Image Production Hard Rule

Updated: 2026-09-09
Policy revision: 6

## Scope

This is the canonical generation rule for Country Hero and S01–S08 scenic images.

It exists to prevent wasted generations from typography, poster layouts, collages, repeated previous assets, and target-scene drift.

## Core rule

- One Scene = one standalone image file.
- One generation target = the current `next.asset` from Production State.
- Never combine multiple Scenes into one collage, grid, contact sheet, poster, diptych, triptych, storyboard, or labelled panel.
- "Batch review" means one user review gate after the Scene round. It does not mean a collage.
- Do not regenerate an APPROVED asset unless the user explicitly requests it.

## Mandatory prompt tail

Every Hero / Scene generation instruction must end with the following hard constraints, regardless of whether the Content Plan already says similar things:

```text
PURE SCENIC IMAGE ONLY.

No added text anywhere in the image.
No title, place name, country name, caption, letters, typography, labels, badges, logo, flag, map, UI, infographic, poster layout, border, frame, collage, grid, split panel, contact sheet, or decorative wording.

Do not invent readable signage. If real-world signage is unavoidable in the location, keep it incidental, small, visually subordinate, and not legible as generated text.

Generate only the specified real place and viewpoint. Do not reuse, restage, crop, or vary the previously generated Hero or Scene. Do not substitute another landmark from the same country.

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
- independence from the previous asset;
- `noAddedText:true`.

If the packet is incomplete, do not spend a generation credit.

## Single-frame prompt envelope — mandatory

For every Hero / Scene generation, the effective instruction begins with the semantic equivalent of:

> ONE SINGLE FULL-BLEED 3:2 LANDSCAPE FRAME. ONE PLACE. ONE CONTINUOUS CAMERA VIEW. NO COLLAGE, NO GRID, NO PANELS, NO CONTACT SHEET, NO MONTAGE, NO INSET IMAGE, NO BORDER, NO LABELS, NO MULTI-SCENE COMPOSITION.

Only after this fixed envelope may the current target identity be described.

Do not mention S01–S08 as a set, the other Scenes, "8 images", "batch", "series", "collection", or review layout in the generation turn.

If a collage/multi-panel output occurs, mark generation context CONTAMINATED and stop image generation for that assistant turn. The next action is RESET_GENERATION_CONTEXT, not another Scene.

## Pre-generation reservation — mandatory

Before calling image generation for Hero or Scene:

1. Re-read authoritative Production State.
2. Confirm the exact NEXT target.
3. Write that target as `GENERATING` with a unique `generationReservation`.
4. Re-read and confirm NEXT becomes `RECONCILE_GENERATION / {same asset}`.
5. Only then generate the image.

Never generate first and plan to update State afterward. The image runtime may end the assistant turn before a State write can occur.

If a previous generation is still `GENERATING`, reconcile it first. Do not call image generation again.

The same Hero / Scene may be generated at most once in one assistant turn.

Every call must be a fresh independent text-to-image generation. Never use the previous generated image as an edit/reference source for the next target or regeneration.

## Preflight before every generation

Before calling image generation:

1. Resolve `stateRef` and read `ops/country-production/{slug}.json` from the authoritative reference (`country/{slug}` during active production, `main` from REVIEW onward).
2. Confirm `next.action` is a generation action.
3. Confirm the exact `next.asset`.
4. Read that asset's visual identity from the authoritative Content Plan on `contentRef`.
5. Compare target identity with the previous generated / approved asset:
   - location
   - main subject
   - terrain
   - architecture
   - season / light
   - composition
6. Append the mandatory prompt tail above.
7. Generate only the current target.

Do not generate from chat memory alone.

## Candidate visual novelty QA — mandatory

After every generated Hero / Scene, reconcile the existing `GENERATING` reservation before writing `REVIEW_CANDIDATE`:

1. Compare the output against the current Render Packet.
2. Compare it against the immediately previous generated or approved Hero / Scene.
3. Record `candidateVisualQa.targetIdentity = PASS`.
4. Record `candidateVisualQa.previousAssetRepeat = PASS`.
5. Record `candidateVisualQa.collageTypography = PASS`.

If the previous image is repeated, restaged, lightly cropped, or otherwise materially the same, reject it automatically, refresh the Render Packet / generation context, and do not ask the user to approve it. Do not retry that same asset again in the same assistant turn.

This check is required even when the generation ID is new. A new generation ID does not prove that the visual output is new.

## Immediate rejection

The output is automatic NG without waiting for user review if any of these occur:

- added title, place name, country name, caption, label or decorative typography;
- poster / brochure / postcard layout;
- collage, grid, split panel, contact sheet or multiple framed scenes;
- previous Hero / Scene is repeated or restaged instead of the current target;
- wrong location / landmark;
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
- second consecutive hard failure: reject, set / retain the asset for regeneration, reset that asset's prompt series;
- do not make a third near-identical attempt using the same prompt family;
- after reset, rebuild the prompt from the Content Plan + mandatory prompt tail, with no reference to the failed output.

The failure limit prevents spending long periods and image credits on one broken prompt series.

## Throughput and runtime constraint

Quality and asset identity remain more important than forcing eight different targets into one image-generation call.

- Never use a single multi-image prompt that risks collage or same-prompt variants as a substitute for eight distinct Scene targets.
- Do not insert a user approval gate between Scene generations.
- Where the runtime supports distinct sequential generation calls in one assistant turn, continue automatically through remaining NOT_STARTED Scenes.
- Where the runtime allows only one generated image per turn, that runtime boundary is not an approval gate: the next user `生成` / `進めて` must immediately execute the next Production State asset without re-planning, re-confirming, or discussing the previous valid candidate.
- Never claim that all eight were generated if the runtime produced only one.

## Machine duplicate gate

After approved Scene assets are materialized, run:

`python3 scripts/validate_images.py --duplicates-only --slug {slug}`

Hero + 8 Scenes are checked pairwise for same-path reuse, normalized identical pixels, and conservative near-duplicate similarity. A failure reopens only the affected Scene(s) for regeneration; the review package must not proceed.

## Batch review

After every Scene has one valid REVIEW_CANDIDATE or is marked REGENERATE:

- present the eight Scene results as one review gate;
- user approves the acceptable images together;
- regenerate only specified NG / REGENERATE assets;
- APPROVED assets are locked.

## Current production

Any Country already in HERO / SCENES / TASTE production must use the latest policy revision from its authoritative Production State resolved by `stateRef` starting with the next generation action. Existing APPROVED assets remain untouched.
