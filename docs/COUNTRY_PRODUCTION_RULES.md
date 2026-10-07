# JOURNEY ATLAS — NEW COUNTRY PRODUCTION

Status: **single human production authority for new Countries**

The normal flow below applies to new Countries. For the user-authorized
remediation of existing Country imagery, use section 15 instead of the new-Country
approval and publication flow. Its scope does not include new Country production.

The production system is deliberately lightweight. GitHub stores final Country assets and runs finish-line QA; it does not track image-generation history or editorial micro-state.

## 1. Core principle

Create the Country first. Inspect the finished Country second.

Do not use GitHub as a production-state machine. New Country production has:
- no Production State file;
- no generation reservation;
- no approval ledger;
- no generation/provenance ID requirement;
- no state-transition CI;
- no State-only, provenance-only or verification-only PR.

Quality is enforced by the finished data, assets, map and rendered page.

## 2. Startup reading

At the start of a new Country read only:
1. `AGENTS.md`;
2. this file;
3. the target `data/countries/{slug}.json` if it already exists.

Open the quality references only when entering that work:
- `docs/IMAGE_QUALITY.md`;
- `docs/CONTENT_QUALITY.md`;
- `docs/MAP_QUALITY.md`.

Do not preload retired production-policy documents.

## 3. Production flow

```text
PREP + MAP
→ HERO
→ 8 SCENES
→ 4 TASTE
→ ONE ASSET HANDOFF
→ IMPLEMENT
→ TARGET QA
→ UNPUBLISHED CANONICAL REVIEW
→ USER FINAL APPROVAL
→ PUBLISH
→ PRODUCTION SMOKE
```

There are exactly four normal user approval gates:
1. Hero;
2. eight-Scene batch;
3. four-Taste batch;
4. final canonical Country page.

Internal quality checks do not create additional user approval gates.

Image generation uses a fast four-point gate only:
1. correct target;
2. one standalone image — no collage / grid / split panel;
3. not the same or near-same visual as an earlier current-Country image;
4. Hero / Scene style is visibly photo 6 : watercolor 4, or Taste follows its separate food language.

PASS → continue immediately to the next deterministic target. During S01→S08 and FOOD01→FOOD04, do not stop to report or request confirmation between passing images.
FAIL → regenerate only that target with a fresh standalone prompt.

Do not add State, ledger, reservation, provenance, reset workflow, extra PR or extra user approval to perform this check.

If the next action is deterministic, continue without asking the user to say "進めて".

## 4. PREP + MAP

Before image production, prepare the finished editorial plan and map:
- Hero place;
- eight Scene places and real coordinates;
- four Taste dishes;
- Country Profile;
- Signature Facts;
- Encounters;
- Beyond the Scenery;
- Travel Trivia;
- Travel Scale;
- Seasons;
- Transport;
- FOR WHOM;
- Travel Notes;
- next routes / related destinations where applicable;
- reliable sources and source dates;
- Theme assignment;
- map geometry, bounds, labels and source/license.

Drafting may happen outside GitHub. Do not create commits merely to record intermediate editorial progress.

## 5. HERO

Generate one Hero candidate at a time: **one target, one image call, one output**.

The Hero must:
- show one real identifiable place;
- preserve plausible geography, architecture, season and light;
- be a quiet landscape composition with mobile-safe crop space;
- use restrained natural color;
- follow the Hero / Scene visual style and photorealism ceiling in `docs/IMAGE_QUALITY.md`;
- contain no text, UI, collage or invented landmark.

Before presenting the Hero for user approval, perform the internal style-band check in `docs/IMAGE_QUALITY.md`.

- PASS → present the Hero for approval;
- BORDERLINE or FAIL → regenerate that Hero before presenting it.

This check does not create a new approval gate.

The Hero has one explicit approval gate. After approval, continue to Scenes.

## 6. EIGHT SCENES

Generate S01→S08 as eight independent image calls.

For every Scene call, apply the fixed generation contract in `docs/IMAGE_QUALITY.md`: **one generation = one target = one image**. Do not put multiple Scene names/IDs into the same generation instruction and do not reference a previous generated image.

Each Scene brief contains only:
- place;
- viewpoint;
- season/light;
- 3–6 identifying visual features;
- composition;
- forbidden elements.

The shared Hero / Scene generation instruction and style band in `docs/IMAGE_QUALITY.md` apply to every Scene.

Perform internal style QA on each generated Scene before the batch review:
- PASS → keep the candidate;
- BORDERLINE or FAIL → regenerate only that Scene.

Do not ask for per-image approval. After all eight PASS candidates are ready, present one batch review. Regenerate only user-rejected Scenes.

## 7. FOUR TASTE IMAGES

Generate FOOD01→FOOD04 as four independent image calls.

For every Taste call, apply the fixed generation contract in `docs/IMAGE_QUALITY.md`: **one generation = one named dish = one image**. Do not put multiple dishes into the same generation instruction and do not reference a previous generated image.

Each image must show:
- one authentic recognizable dish;
- the complete dish/vessel;
- centered and consistent visual weight;
- pale beige/ivory matte background;
- soft diffused daylight;
- no decorative props unless integral to the dish;
- no text, collage or multi-panel.

Taste uses the separate Spain food-image language defined in `docs/IMAGE_QUALITY.md`; do not mechanically apply the Hero / Scene photorealism ceiling to food images.

Review the four as one batch. Regenerate only rejected dishes.

## 8. ONE ASSET HANDOFF

After Hero, Scenes and Taste are approved, hand off exactly 13 final rasters once:
- 1 Hero;
- 8 Scenes;
- 4 Taste images.

Production folders contain final assets only. Rejected candidates and temporary files do not belong in the repository.

## 9. IMPLEMENT

Create or update one Country branch with the finished Country package:
- 13 approved rasters;
- one final map SVG;
- Country JSON;
- Theme assignment;
- publication registry only when required by the existing destination row.

Do not open image-by-image PRs or intermediate production PRs.

## 10. TARGET QA

Run finish-line QA only against the affected Country:
- Content QA;
- Country schema/data QA;
- Image decode/dimensions/duplicate QA;
- visual Image QA against the Hero / Scene style band and Taste language;
- Map geometry/coordinate/label QA;
- Desktop / Tablet / Mobile Browser QA.

QA returns PASS or FAIL. It does not advance or mutate production state.

When a check fails, fix only the affected artifact and rerun the relevant check.

## 11. REVIEW

Open one Country review PR.

After its required QA passes, merge the Country implementation while it remains unpublished:
- `atlasPublished:false`;
- `noindex,follow`;
- absent from sitemap;
- absent from normal discovery links.

Review the canonical Country page:
`https://atlas.yagenji.com/countries/{slug}/`

Only explicit user approval of that page authorizes publication.

## 12. PUBLISH

After final approval, create one small publication PR from latest `main`.

That PR changes only what is necessary to make the already-reviewed Country discoverable/indexable. Do not rebuild the Country or repeat unchanged editorial/image work.

After merge, verify the deployed SHA and target Country route.

## 13. Error discipline

A one-off failure does not create a new permanent production rule.

Use this order:
1. identify the concrete defect;
2. decide whether it is Country-specific or shared;
3. fix the defect;
4. rerun the smallest relevant QA;
5. change shared rules only for a repeated, proven shared defect.

Shared-system defects are fixed separately from Country content whenever practical.

## 14. Definition of Done

A new Country is complete only when:
- content and sources are final;
- Hero + 8 Scenes + 4 Taste images are approved;
- Hero + 8 Scenes pass the shared visual style band;
- final map is geographically valid;
- target Content / Image / Map QA passes;
- actual Desktop / Tablet / Mobile rendering passes;
- the canonical unpublished page is explicitly approved;
- publication is merged;
- production route/SHA smoke verification passes.

## 15. Existing Hero / Scene image remediation

This workflow implements the user's approved 2026-10-07 remediation direction:
retain existing BORDERLINE imagery and minimize human operations through one
finished-page batch review, normally covering about five Countries.

### Scope and quality

- Use the completed image-quality audit to select existing FAIL Hero / Scene
  targets. Confirm latest `main`, current image references and existing work first.
- Retain existing PASS and BORDERLINE images. Retained BORDERLINE images remain
  BORDERLINE; this is an explicit retention exception, not a PASS reclassification.
- Every newly generated replacement must PASS `IMAGE_QUALITY.md`. Regenerate a
  new BORDERLINE or FAIL candidate internally before presenting the batch.
- Generate each replacement independently: one target, one image call, one
  output. Keep the real place accurate and simplify its rendering.
- Preserve Taste images, maps, editorial content, URLs and publication state.
  Do not regenerate retained images to complete a nominal eight-Scene batch or
  thirteen-image handoff.

### Autonomous preparation

Proceed through target preparation, independent generation, internal visual QA,
replacement-page preparation and relevant target QA without per-Hero, per-Scene
or per-Country approval. Do not stop to request "continue" between deterministic
steps. A pilot Country is included in the first finished-page batch review;
there is no separate pilot approval gate.

Inspect the complete nine-image Hero / Scene set, including retained images,
for consistency. Do not silently expand the remediation scope to retained
BORDERLINE images. Raise a concrete inconsistency in the finished batch review
if it materially affects the page.

Prepare replacements in an isolated working copy or review preview. Before
review, verify raster decoding, dimensions/aspect ratios, references and
duplicates, and actual Desktop / Tablet / Mobile rendering of affected pages.
Keep candidates and previews out of live published assets.

### One approval gate per finished batch

Present the completed replacement pages and a concise changed-target list as
one review, normally for about five Countries. Clearly identify the retained
images and newly generated replacements. This single batch approval replaces
the separate Hero, Scene and final-page gates for this remediation only.

After explicit user approval of the finished batch, commit/PR and apply its
approved replacements together, run relevant checks and verify production
routes and deployed SHA. Do not unpublish an existing Country or create a
second publication approval gate. Fix only specifically rejected targets;
do not ask to reapprove unchanged, already approved targets.

Continue autonomously into preparing the next batch after approved replacements
are verified. Each subsequent completed batch still requires explicit approval
before its live replacements are applied. Report a concrete blocker when tools
or unresolved factual inputs prevent completion; do not invent geography or
claim background work will continue after a turn ends.

Use final assets only in the repository. Do not add Production State, approval
ledgers, generation histories, reservations or image-by-image PRs. Shared policy
changes are separate from the final image-replacement batch.
