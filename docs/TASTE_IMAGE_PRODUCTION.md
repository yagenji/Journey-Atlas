# JOURNEY ATLAS — Taste Image Production Hard Rule

Updated: 2026-09-12
Policy revision: 7.2

This file is the Single Source of Truth for Country-page Taste image generation beneath the current main image-generation policy.

## Purpose

Taste images are **single-dish atlas cuts**. They are not restaurant-table scenes, lifestyle still lifes, feast spreads, food-editorial styling, multi-dish layouts or travel scenery.

The viewer should recognize the dish immediately from the food itself and the minimum elements genuinely required to constitute or serve that dish.

## Non-negotiable generation unit

- **1 image = 1 dish only.**
- **1 generation request = 1 FOOD target only.**
- FOOD01–FOOD04 are four independent image-generation calls.
- “Generate the four Taste images as one round” means four consecutive independent calls without user approval between valid targets.
- It never means one four-dish image, grid, split screen, montage, contact sheet, diptych, triptych or collage.
- One independent call per FOOD does **not** mean one user approval per FOOD.

## Visual language

Every Taste image uses the Spain Taste visual language:

- final target 1200×800;
- exact 3:2;
- one clearly recognizable dish;
- dish centered and visually dominant;
- restrained photo 6 : quiet watercolor 4;
- natural, appetizing, realistic food structure;
- plain pale beige / warm ivory / very light neutral background;
- no text, labels, flags, logos, packaging, watermark, border or UI.

## Integral components vs decorative props

The rule is **not** “only one vessel may exist.”

The correct rule is:

> Include what is genuinely required to constitute, serve or recognize the dish. Exclude what is added only to make the picture look richer.

### Allowed when integral to the dish

Examples include:

- a dipping sauce that is normally part of the dish;
- broth or soup that is part of the serving;
- a wrapper or leaf that is genuinely part of the food presentation;
- a small bowl or ramekin required to hold an integral sauce;
- another accompaniment without which the named dish would be materially incomplete or misleading.

These elements must be declared in the exact FOOD Render Packet before generation.

For example, Brunei ambuyat may include its integral cacah dipping sauce and the small vessel required to serve that sauce.

### Forbidden when decorative or contextual

Do not add elements merely for styling, atmosphere or “food photography” richness, including:

- decorative herbs outside the actual dish;
- raw ingredients scattered around the food;
- unrelated side dishes;
- extra plates or bowls with no integral role;
- cutlery or chopsticks added for styling;
- napkins, tablecloths or placemats;
- cups, glasses, bottles or drinks;
- condiment bottles or sauce dishes not integral to the named dish;
- fruit or vegetables used as props;
- flowers, candles, books or menus;
- cookware, pans, pots or decorative boards;
- hands or people;
- restaurant or kitchen interiors;
- windows, streets, scenery or landscapes;
- shelves, counters, national motifs or souvenirs;
- depth-of-field lifestyle backgrounds.

A normal garnish may remain when it is actually part of the dish itself. Do not invent garnish for visual interest.

## Revision 7.2 Render Packet contract

Before any FOOD generation, the exact target Render Packet must contain a complete composition contract.

Required fields include:

```json
{
  "kind": "TASTE",
  "independentGeneration": true,
  "forbidPreviousAssetReuse": true,
  "singleDishOnly": true,
  "cleanNeutralBackground": true,
  "integralAccompanimentsOnly": true,
  "integralAccompaniments": [],
  "integralServingElements": [],
  "decorativePropsForbidden": true,
  "decorativeProps": [],
  "plainBackgroundRequired": true,
  "backgroundStyle": "PLAIN_PALE_BEIGE_OR_WARM_IVORY"
}
```

`integralAccompaniments` and `integralServingElements` may contain named items when they are genuinely required by the dish.

`decorativeProps` must always be `[]`.

If this contract is incomplete, do not generate.

## Dish identity

Before generation, define the dish itself concretely:

- main shape and silhouette;
- key visible ingredients;
- texture and surface color;
- traditional arrangement;
- serving vessel where appropriate;
- any integral accompaniment;
- any integral wrapper or serving element.

Do not compensate for weak dish identity by adding scenery or props.

## Prompt envelope

Every Taste generation must semantically contain:

> ONE SINGLE FULL-BLEED 3:2 IMAGE. ONE NAMED DISH ONLY. INCLUDE ONLY THE DISH AND NAMED INTEGRAL COMPONENTS. PLAIN PALE BEIGE OR WARM IVORY BACKGROUND. NO DECORATIVE PROPS, NO LIFESTYLE STYLING, NO COLLAGE, NO GRID, NO PANELS, NO TEXT.

Do not mention FOOD01–FOOD04 as a set, batch, collection or series inside the image-generation instruction itself.

## Pre-generation reservation

Before generation:

1. read authoritative Production State when entering a new assistant turn or after uncertainty;
2. confirm the exact FOOD target from Protocol 2 NEXT;
3. reserve exactly that target as `GENERATING`;
4. bind reservation to asset, contentId, promptSeries and generation-context epoch;
5. generate only that FOOD target.

At most one unreconciled `GENERATING` target may exist.

Every FOOD call is a fresh independent text-to-image generation. Never edit or reference the previous dish image to create the next dish.

## Candidate QA — mandatory

After every generated Taste image, reconcile it before the next call.

A Taste candidate may become `REVIEW_CANDIDATE` only when all of these are `PASS`:

```json
"candidateVisualQa": {
  "targetIdentity": "PASS",
  "dishIdentity": "PASS",
  "singleDish": "PASS",
  "integralComponentsOnly": "PASS",
  "plainBackground": "PASS",
  "decorativePropsAbsent": "PASS",
  "previousAssetRepeat": "PASS",
  "collageTypography": "PASS"
}
```

`integralComponentsOnly` means every extra food component or serving element visible in the image is part of the dish as declared in the Render Packet.

`decorativePropsAbsent` means no unrelated styling elements are visible.

Checking only target identity, repeat and collage is insufficient.

## Initial Taste round — hard flow rule

`TASTE_INITIAL` is a **first-pass round**, not a per-dish retry loop.

For FOOD01–FOOD04:

1. attempt the current target once;
2. if valid, store it as `REVIEW_CANDIDATE`;
3. if it fails, park it as `REGENERATE` and record the failure;
4. if another FOOD target remains `NOT_STARTED`, continue to that target;
5. do **not** retry the failed FOOD while unattempted FOOD targets remain;
6. once all four targets have been attempted, stop at the Taste batch boundary;
7. present one Taste Batch Review;
8. approve valid candidates and record failed targets in the batch ledger `regenerate` list;
9. only then enter `TASTE_REGEN`.

Entering `TASTE_REGEN` before a real first Taste Batch Review is invalid.

## Taste regeneration round

During `TASTE_REGEN`:

- previously batch-approved FOOD items remain immutable;
- regenerate only the FOOD targets rejected by the batch review;
- run independent image-generation calls for all remaining REGENERATE targets;
- do not ask for individual approval after each regenerated image;
- stop at the regeneration round boundary;
- present one regeneration Batch Review.

## Repeat and wrong-target handling

If a generated Taste image repeats/restages a prior image or carries over the wrong FOOD target:

1. reject it automatically;
2. record `PREVIOUS_ASSET_REPEAT` or `WRONG_TARGET_CARRYOVER`;
3. contaminate/reset the generation context under Revision 7;
4. stop generation for that assistant turn when the policy requires reset;
5. **refresh the Render Packet / prompt family immediately**;
6. increment `promptSeries`;
7. only then regenerate.

Do not wait for the same prompt family to fail twice.

A new generation ID does not make a repeated visual acceptable.

## Other hard failures

Reject the affected FOOD candidate when any of the following occurs:

- collage / multi-panel / grid;
- more than one named dish;
- wrong dish identity;
- decorative props;
- restaurant, kitchen or lifestyle background;
- non-integral side dishes or sauces;
- text, logo, flag or packaging;
- dish too small because the background dominates;
- another FOOD target repeated or carried forward;
- wrong aspect ratio, decode failure or other technical defect.

For an ordinary composition failure that is not a repeat or wrong-target carryover, the existing prompt-series credit guard may still allow one retry before a prompt-family refresh. Repeat and wrong-target failures are stricter and refresh immediately.

## Interaction rules

- Do not ask for user approval after FOOD01, FOOD02 or FOOD03.
- Do not ask the user to type `approve`, `進めて`, `next`, `生成` or equivalent between valid Taste targets.
- A valid FOOD result is an internal production checkpoint, not a user interaction checkpoint.
- A runtime-imposed assistant turn boundary is not approval.
- On the next user message after a runtime boundary, reconcile State and continue from Protocol 2 NEXT without asking for review of the previous valid candidate.

Protocol 2 tracks user continuation nudges separately from runtime-forced turn boundaries. The former must remain zero.

## Batch approval

No FOOD item becomes `APPROVED` during `TASTE_INITIAL` or before a true Taste batch boundary.

Individual `userApprovedAt` events are forbidden. Approval provenance belongs in the append-only Taste batch ledger.

APPROVED Taste images are immutable unless the user explicitly asks for regeneration.

## Machine duplicate gate

After approved Taste assets are materialized, run:

```bash
python3 scripts/validate_images.py --duplicates-only --slug {slug}
```

This final machine gate complements, but does not replace, the live all-prior visual comparison during generation.
