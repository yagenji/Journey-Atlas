# JOURNEY ATLAS — Taste image production

Updated: 2026-09-17. This is the **dish identity and composition guide**; it does not duplicate the generation State machine. The current main `ops/image-generation-policy.json` and `ops/country-production-policy.json` govern Render Packet fields, reservations, candidateVisualQa, contamination/reset, batch ledger and retry timing. For the current next action use `scripts/country_production_protocol_v2.py next {slug}`.

## Visual contract

- **One image = one named dish = one independent generation call.** FOOD01–FOOD04 are separate calls, followed by **one batch user review**, not four approvals or one multi-dish image.
- Final target 1200×800 (3:2), photo 6 : quiet watercolor 4, Spain approved Taste visual language, soft daylight, plain pale beige/warm ivory table, restrained color, recognizable food. Center the complete dish and necessary vessel; consistent visual scale (normally approximately 62% of image width), no crop.
- No added text, logos, labels, packaging, flags, watermarks, border, restaurant/lifestyle scenery, collage, panels, grid or contact sheet. Never use the previous FOOD image as edit or reference input for a different dish.
- The **only** non-dish elements allowed are the authentic serving vessel and components genuinely required to constitute, serve or recognize the specified dish. Name each integral accompaniment and serving element in the current FOOD Render Packet before generation. A sauce integral to the dish and its necessary ramekin are allowed; stray garnish, raw ingredients, extra tableware, cutlery, drinks, napkins or decorative props are not. `decorativeProps` must be `[]`.

## Current FOOD identity and image prompt

From the validated current Render Packet, specify the named dish, key visible ingredients, shape/silhouette, texture/color, authentic arrangement/vessel, and any integral accompaniment. Do **not** list the other FOOD targets or Spain dish names in the generation prompt.

```text
ONE SINGLE FULL-BLEED 3:2 IMAGE. ONE NAMED DISH ONLY.
Include only this dish, its necessary vessel and specifically named integral components.
The entire surrounding pale beige/warm ivory tabletop stays plain and empty.
Center the complete dish and vessel with consistent subject scale; do not crop.
Soft diffused daylight. Refined restrained photo 6 : quiet watercolor 4.
NO DECORATIVE PROPS. NO LIFESTYLE STYLING. NO TEXT.
NO COLLAGE, GRID, PANELS, OR MULTI-DISH IMAGE.
Create this dish independently; do not edit, vary or reuse a previous image.
```

## Review and technical gates

Before generating, validate the current exact FOOD target, Render Packet and reservation under the machine policy; do not spend credits on incomplete composition fields. For each result verify the named dish and integral components, plain empty background, centered complete subject, no props, no previous-asset repeat, no collage/typography and consistent style. Record all current mandatory `candidateVisualQa` fields; a merely recognizable dish is not sufficient.

During `TASTE_INITIAL` attempt each of FOOD01–FOOD04 once. Park a failed target and finish other unattempted targets; do not retry it before the first batch review. Approve valid candidates as a batch, then regenerate only the rejected FOOD targets under the current policy. Duplicated/wrong-target outputs require the prescribed prompt refresh and generation-context reset. Preserve approved dishes and ledger provenance. After assets are stored, run complete decode/dimensions and the machine duplicate gate (`scripts/validate_images.py --duplicates-only --slug {slug}`); check the actual Country page before reporting visual QA PASS.
