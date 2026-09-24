# JOURNEY ATLAS — NEW COUNTRY PRODUCTION

Status: **single human production authority for new Countries**

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

Generate one Hero candidate at a time.

The Hero must:
- show one real identifiable place;
- preserve plausible geography, architecture, season and light;
- be a quiet landscape composition with mobile-safe crop space;
- use restrained natural color;
- contain no text, UI, collage or invented landmark.

The Hero has one explicit approval gate. After approval, continue to Scenes.

## 6. EIGHT SCENES

Generate S01→S08 as eight independent image calls.

Each Scene brief contains only:
- place;
- viewpoint;
- season/light;
- 3–6 identifying visual features;
- composition;
- forbidden elements.

Do not ask for per-image approval. After all eight candidates are ready, present one batch review. Regenerate only rejected Scenes.

## 7. FOUR TASTE IMAGES

Generate FOOD01→FOOD04 as four independent image calls.

Each image must show:
- one authentic recognizable dish;
- the complete dish/vessel;
- centered and consistent visual weight;
- pale beige/ivory matte background;
- soft diffused daylight;
- no decorative props unless integral to the dish;
- no text, collage or multi-panel.

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
- final map is geographically valid;
- target Content / Image / Map QA passes;
- actual Desktop / Tablet / Mobile rendering passes;
- the canonical unpublished page is explicitly approved;
- publication is merged;
- production route/SHA smoke verification passes.
