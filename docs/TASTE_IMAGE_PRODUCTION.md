# JOURNEY ATLAS — Taste Image Production Hard Rule

Updated: 2026-09-10
Policy revision: 7.1

This file is the Single Source of Truth for Country-page Taste image generation beneath the current main image-generation policy.

## Purpose

Taste images are not food photography scenes, restaurant-table scenes, lifestyle still lifes, or multi-dish layouts.

They are **single-dish atlas cuts** whose job is to let the viewer recognize one representative food immediately.

## Non-negotiable generation unit

- **1 image = 1 dish only.**
- **1 generation request = 1 dish only.**
- Never ask the image generator to place FOOD01–FOOD04, multiple dishes, multiple plates, or multiple panels in one image.
- “Generate all four Taste images in one batch” means: generate four independent images consecutively without waiting for user approval between them.
- It never means one four-dish image, a 2×2 grid, split screen, montage, diptych, triptych, contact sheet, comparison plate, or collage.
- If a tool call can return multiple candidates, every candidate must still depict the same single dish. Do not use one call to request different dishes.
- One independent generation request per dish does **not** mean one user approval per dish.
- Different FOOD targets should continue in the same assistant turn after successful reconciliation when the image tool returns control.

## Composition lock

Every Taste image must use the Spain Taste visual language:

- final target: 1200×800
- exact 3:2
- one clearly recognizable dish
- one simple plate, bowl, cup, or serving vessel only when appropriate to that dish
- dish is the dominant subject and occupies the visual center
- restrained photo 6 : quiet watercolor 4 treatment
- natural, appetizing, realistic food structure
- clean pale beige / warm ivory / very light neutral background
- background should read as a quiet plain surface, not a location
- no text, labels, flags, logos, packaging, watermarks, frames, or UI

## Background hard rule

The background must remain visually empty.

Do **not** add decorative or contextual props unless they are literally part of the dish itself.

Explicitly prohibited in the background or around the dish:

- extra plates or bowls
- second dishes, side dishes, tasting portions
- cutlery
- chopsticks
- napkins or tablecloth styling
- cups, glasses, bottles, carafes
- condiments or sauce dishes
- loose herbs placed for styling
- raw ingredients
- fruit or vegetables used as props
- bread baskets
- flowers, candles, books, menus
- cookware, pans, pots, boards
- hands or people
- restaurant interiors
- kitchen interiors
- windows, streets, scenery, landscapes
- shelves, counters, decorative objects
- national motifs or souvenirs
- depth-of-field restaurant backgrounds
- shadows or reflections that imply unrelated objects outside the frame

A small garnish is allowed only when it is a normal, integral part of the dish and remains **on the same plate/bowl**. Do not invent garnish for visual interest.

## Dish identity rule

Before generation, define the dish identity in concrete visual terms:

- vessel
- main shape / silhouette
- key ingredients visible from the chosen angle
- texture
- surface color
- traditional arrangement
- any truly integral accompaniment

Do not compensate for weak dish identity by adding props or scenery.

If the dish cannot be recognized without explanatory background objects, improve the dish depiction itself.

## Render Packet input contract

Before any FOOD generation, Production State must contain a complete `renderPacket` for that exact dish.

Minimum packet:
- `kind: TASTE`;
- stable `contentId`;
- concrete dish identity;
- `independentGeneration:true`;
- `forbidPreviousAssetReuse:true`;
- `singleDishOnly:true`;
- `cleanNeutralBackground:true`.

The prompt must be rebuilt from the current Render Packet. Never carry any previously generated dish forward as an image-edit target or implicit reference.

If the Render Packet is missing or incomplete, do not generate.

At `TASTE_INITIAL` start, validate all FOOD01–FOOD04 Render Packets once. Within the same uninterrupted assistant turn, reuse the unchanged validated packet from authoritative State; do not re-read the Content Plan before every dish.

## Single-frame prompt envelope — mandatory

For every Taste generation, the effective instruction begins with the semantic equivalent of:

> ONE SINGLE FULL-BLEED 3:2 IMAGE. ONE DISH IN ONE SERVING ONLY. NO COLLAGE, NO GRID, NO PANELS, NO CONTACT SHEET, NO MONTAGE, NO INSET IMAGE, NO BORDER, NO LABELS, NO SECOND DISH.

Do not mention the four Taste images as a set, "4 images", "batch", "series", "collection", or review layout in the generation instruction sent to the image model.

If a collage/multi-panel output occurs, mark generation context CONTAMINATED and stop image generation for that assistant turn.

## Pre-generation reservation — mandatory

Before the first FOOD generation in a new assistant turn, or whenever State authority is uncertain:

1. Read authoritative Production State.
2. Confirm the exact FOOD target from NEXT.
3. Write that FOOD item as `GENERATING` with a unique `generationReservation` bound to exact asset id, contentId, promptSeries, and current generationContext epoch.
4. Persist using the expected blob SHA.
5. If GitHub accepts the write, treat the exact State content just written plus the returned new blob SHA as authoritative in that same assistant turn.
6. Confirm locally/deterministically that NEXT is `RECONCILE_GENERATION / {same FOOD}` and generate only that dish.

Do **not** immediately re-fetch the same State merely to confirm your own successful write. Re-fetch only on a new assistant turn, SHA conflict, possible external modification, or genuine uncertainty.

If any prior Hero / Scene / FOOD remains `GENERATING`, reconcile it first. Never generate the same FOOD more than once in one assistant turn. At most one unreconciled `GENERATING` target may exist.

Every FOOD call is a fresh independent text-to-image generation. Never use a previous dish image as an edit/reference source.

## Preflight and all-prior novelty check

At Taste round start:

1. validate all FOOD01–FOOD04 Render Packets and dish identities once;
2. confirm the four target identities are distinct before spending credits;
3. build the current all-prior Taste comparison set.

Before each subsequent FOOD generation in the same turn:

1. use the already-validated current Render Packet;
2. confirm its exact reservation asset/contentId/epoch;
3. compare the intended target with all previously generated or approved Taste targets in the Country;
4. do not reuse the previous image, composition seed, or implicit visual starting point.

Do not repeatedly re-fetch unchanged Render Packets, Content Plans, or prior images already available in the current generation context.

## Candidate visual novelty QA — mandatory

After every generated Taste image, reconcile the existing `GENERATING` reservation before the next image is generated:

- confirm the output matches the current dish Render Packet;
- compare it with **every** previously generated or approved Taste image in the same Country, using the in-turn incremental comparison set where available;
- record `candidateVisualQa.targetIdentity = PASS`;
- record `candidateVisualQa.previousAssetRepeat = PASS` only after the all-prior comparison passes;
- record `candidateVisualQa.collageTypography = PASS`;
- confirm single-dish and clean-background rules.

Checking only the immediately previous dish is insufficient.

A new generation ID is not sufficient. If any prior dish image is repeated, restaged, lightly altered, or carried into the wrong FOOD target, reject automatically and do not ask the user to approve it.

## Contamination handling

Set `generationContext.state = CONTAMINATED` when any of these occurs:

- collage / multi-panel / grid / contact-sheet / montage;
- the prior or another Taste image is repeated/restaged;
- a different FOOD target is carried into the current target;
- the model repeatedly preserves the prior dish structure while changing only superficial details.

On contamination:

1. reject and reconcile the generation;
2. set the affected FOOD to `REGENERATE`;
3. record the failure reason;
4. do **not** reserve the next FOOD in that transition;
5. stop further image generation for that assistant turn;
6. NEXT must become `RESET_GENERATION_CONTEXT`;
7. the RESET turn must perform no image generation and rebuild the next prompt from exactly one current Render Packet.

## Taste round execution — hard throughput rule

For the initial four Taste items or a Taste regeneration round:

1. reserve the first current FOOD target;
2. generate exactly that one dish;
3. reconcile and run target / all-prior duplicate / collage / single-dish / background QA;
4. if valid and another different FOOD target remains while generation context is CLEAN, use **one atomic State update** to:
   - persist the current FOOD as `REVIEW_CANDIDATE`;
   - clear its reservation;
   - reserve the next different FOOD as `GENERATING` with exact asset/contentId/promptSeries/epoch binding;
5. after that successful State write, do not re-fetch merely to confirm it; generate the already-reserved next FOOD immediately;
6. repeat until FOOD04 / regeneration round boundary or a real blocking/contamination condition;
7. for the final target, reconcile/persist without reserving another FOOD;
8. present one batch review after the round boundary;
9. regenerate only the user-specified or automatically rejected NG item(s).

Hard interaction rules:

- Do **not** ask for user approval after FOOD01, FOOD02, or FOOD03.
- Do **not** ask the user to type `approve`, `進めて`, `生成`, `next`, or equivalent between valid Taste generations.
- A valid FOOD result is an internal production checkpoint, not a user interaction checkpoint.
- While sequential image-generation calls are technically available in the current assistant turn, do **not voluntarily return control** before the round boundary.
- Each FOOD still uses its own independent image-generation request. Never combine several dishes into one prompt or output.
- Do not wait for country-branch CI completion between valid images; CI is an asynchronous transition guard.
- If the image runtime truly hard-stops the assistant turn after one generated image, that boundary is not approval. On the next user message, re-read/reconcile if needed and immediately continue from NEXT without asking for review of the previous valid candidate.

APPROVED Taste images are immutable unless the user explicitly asks for regeneration.

Do not edit the previous dish image into the next dish image. Each dish starts from an independent generation state.

## Machine duplicate gate

After the four approved Taste assets are materialized, run:

`python3 scripts/validate_images.py --duplicates-only --slug {slug}`

All four Taste images are compared pairwise for same-path reuse, normalized identical pixels, and conservative near-duplicate similarity. This remains a final machine safety gate; it does not replace the all-prior live comparison during generation.

A failure reopens only the affected Taste item(s); the Country review package must not proceed.

## Batch approval enforcement

During `TASTE_INITIAL` / `TASTE_REVIEW`, no FOOD item may become `APPROVED`.

FOOD01–FOOD04 first become `REVIEW_CANDIDATE` (or `REGENERATE` for a hard failure). The user is asked for approval only after all four have completed the round.

During `TASTE_REGEN`, previously batch-approved FOOD items may remain APPROVED and locked, but newly regenerated candidates must remain `REVIEW_CANDIDATE` until the regeneration batch boundary.

Individual user approval prompts or individual `userApprovedAt` events are invalid workflow behavior. Approval provenance belongs only to the Revision 7 append-only Taste batch ledger.

## Prompt-series credit guard

Track `promptSeries` and `promptSeriesRejectCount` per active dish.

After two hard failures in one prompt series, do not generate again until the Render Packet / prompt family is refreshed. This prevents repeated wrong-dish generations from consuming credits.

A repeat or wrong-target carryover should trigger context reset immediately rather than spending another credit on a near-identical prompt family.

## Hard reject conditions

Reject and regenerate the affected dish if any of the following appears:

- collage / multi-panel / grid
- more than one dish
- more than one meaningful serving vessel
- unrelated food or side dish
- decorative background props
- restaurant / kitchen / lifestyle background
- ingredients scattered around the plate
- cutlery / napkin / glass / bottle added for styling
- text / logo / flag / packaging
- dish is too small because background dominates
- wrong food structure or unrecognizable dish
- another FOOD target is repeated or carried forward
- photographic style is materially stronger than the JOURNEY ATLAS Taste reference
- watercolor is materially stronger than the Spain Taste reference
- low resolution, decode failure, wrong aspect ratio, or other technical failure

A rejected image must never be moved into the approved production folder.

## Prompt minimum

Every Taste generation prompt must explicitly state all of the following:

- ONE specific named dish only
- single independent image
- no collage / no multi-panel / no grid
- one plate/bowl/vessel only
- plain pale beige or warm ivory background
- no props, no cutlery, no napkin, no drink, no ingredients around the dish
- no restaurant or kitchen background
- no people or hands
- no text / logo / flag / packaging
- Spain Taste visual language
- photo 6 : quiet watercolor 4
- exact 3:2 composition
