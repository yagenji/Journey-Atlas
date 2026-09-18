# JOURNEY ATLAS — COUNTRY PRODUCTION RULES

Status: **Human operational authority for NEW COUNTRY production**  
Machine enforcement remains in `ops/country-production-policy.json`, `ops/image-generation-policy.json`, validators and workflows. Those machine files are not startup reading material unless a State transition, validation failure or policy mismatch must be diagnosed.

## 1. Purpose

Create a Country Page that makes a first-time visitor want to know the country through scenery and geography, while preserving the common JOURNEY ATLAS system.

Quality is judged by the finished page, not by the number of rules, checks or CI runs.

## 2. Non-negotiable quality

- Use the common Country Template, typography, color system, spacing, icon language and Map visual language.
- Iceland / Norway remain the visual-series reference. Spain remains the Taste-series reference.
- Hero and scenes must represent real, recognizable places with plausible geography, architecture, season and light.
- Do not switch to photographs, SVG illustrations, reduced image counts, alternate page structures or Country-specific CSS/JS to escape a production problem.
- Facts, geography, population, area, transport, seasonality and other factual claims must be verified from reliable sources. Do not guess.
- Map locations derive from real coordinates; only label/visual offsets may be adjusted for collisions.
- Desktop, Tablet and Mobile must work. Accessibility, headings, alt/ARIA, semantics, keyboard operation and contrast are maintained.

## 3. What changes per Country

Country-specific content belongs in the Country JSON and approved Country assets. Theme assignment remains in `data/theme-taxonomy.json`.

Normally change only:
- Country content and sources;
- Hero, eight Scenes, four Taste images;
- Map shape/locations/labels;
- Theme assignment and related-destination data;
- the target Country Production State.

Shared Template/CSS/JS/workflows/validators are changed only for a proven shared-system defect, in separate system work where practical.

## 4. Production flow

```text
CONTENT + MAP
→ HERO
→ 8 SCENES
→ 4 TASTE
→ ASSET HANDOFF / VERIFY
→ IMPLEMENTATION + TARGET QA
→ UNPUBLISHED CANONICAL REVIEW
→ USER FINAL APPROVAL
→ FORMAL PUBLISH
→ PRODUCTION VERIFY
```

Do not create extra phases or approval gates.

**Keep the Country branch without a main-targeting PR during CONTENT + MAP, HERO, SCENES and TASTE.** Open or reuse one PR only after all 13 approved rasters are handed off and verified, when entering implementation/review QA. State-transition checks still run on Country pushes; PR-only checks must not be triggered by per-image progress. Do not open a PR for each image or State update.

## 5. CONTENT + MAP

Before Hero generation, finish the content that does not require final raster bytes:
- Hero place and eight Scene selections;
- Country Profile, Signature Facts, Encounters, Beyond the Scenery, Travel Trivia;
- four Taste dishes;
- Travel Scale, Seasons, Transport, FOR WHOM, Travel Notes;
- related destinations / next routes where applicable;
- sources and source dates;
- scene coordinates and Map;
- Theme assignment.

**Maps for Countries newly initialized after the shared geographic-context implementation is merged must show real surrounding land from the start.** Follow Azerbaijan's approved sea/surrounding-land palette on the common 1200×760 canvas. Preserve the target country's geographic identity and map-marker coordinates. Do not draw fictional neighboring terrain, borders or roads, or omit land to make an exclave appear to be an island.

For a new **single-region** Country, use the shared wrapper with verified target-specific administrative geometry; GSHHS coastlines alone cannot define a national border. The output must be a *new* preview path, not an existing approved asset. Example (replace placeholders with the actual Country, verified source and location):

```bash
python3 scripts/generate_country_map_with_context.py \
  --country-json data/countries/COUNTRY_SLUG.json \
  --source natural-earth --dataset /path/to/verified/admin0.geojson \
  --country-name 'VERIFIED COUNTRY NAME' \
  --output /tmp/COUNTRY_SLUG-map-context-review.svg
```

The wrapper also accepts `--source geoboundaries --iso VERIFIED_ISO3` when that verified source is appropriate. Record the actual boundary/coast source and license, assess coastline alignment, islands/exclaves, canvas edges and labels, and fully decode the rendered SVG at 1200×760 before handing it off. Do not use the old clean-background generator as a fallback for a new Country.

**Multi-region / inset Countries:** the single-region wrapper deliberately rejects `map.regions`. Use a verified region-aware map construction with the Country JSON's real region bounds, then apply the common `scripts/add_country_map_context.py` stage to a separate SVG preview. Check each region's clipping and inset projection individually. If the actual SVG layout is unsupported, resolve the common map-generation path before completing CONTENT + MAP; do not invent a Country-specific shortcut or silently produce a map without surrounding land. Do not retrofit a Country already in progress unless explicitly requested.

Use the current Country schema and current Content QA. Machine validators determine field-level contract details; do not copy their full rule set into chat context.

## 6. HERO

Hero is the page’s highest-quality image.

Requirements:
- one real place;
- identifiable Country/place character;
- horizontal composition with safe text/crop area;
- still legible on mobile;
- restrained, natural color;
- roughly photo 6 : quiet watercolor 4;
- no text, map, UI, collage or invented scenery.

Hero has one explicit user approval gate. Do not start Scene generation before Hero approval.

## 7. EIGHT SCENES

The eight Scenes explain the country’s visual/geographic breadth; they are not a tourism ranking.

For each Scene:
- define the current place, viewpoint, season/light and 3–6 identifying features;
- generate **one independent image for that Scene only**;
- do not include other Scene names in that generation request;
- check place identity, realism, 3:2 composition, visual style and repetition.

Once the user starts the Scene round, continue S01→S08 without asking for `next` or per-image approval. One image-generation call handles one Scene. After the round, present one batch review. Regenerate only rejected Scenes.

## 8. FOUR TASTE IMAGES

Taste uses Spain’s approved Taste images as the global visual-language reference, not as dish/composition copies.

For each dish:
- one dish only;
- authentic recognizable form;
- complete dish/vessel visible;
- centered, consistent visual weight;
- pale beige/ivory matte tabletop;
- soft diffused daylight;
- no decorative props unless integral to the dish;
- roughly photo 6 : quiet watercolor 4;
- no text/collage/multi-panel.

Once the user starts the Taste round, continue FOOD01→FOOD04 without per-image prompts. Review the four images as one batch. Regenerate only rejected dishes.

## 9. Image failures and State

Do not repeatedly retry the same failed target in one round. Preserve successful assets, park failed targets, finish the batch boundary, then regenerate only the failures after batch review.

The Country Production State is the restart point. On a new turn, read the target State and current NEXT; do not reconstruct the entire production history from chat.

Do not repeatedly reload unchanged long policy files within the same work period. Read machine policy only when the current State/action cannot be resolved or validation reports a policy error.

## 10. Asset handoff

Approved raster assets are handed off once as the approved set. Production folders contain final approved assets only: no draft/temp/test/placeholder/base64/parts/rejected/old duplicates.

Verify:
- path and filename;
- format and complete decode;
- dimensions/aspect ratio;
- Country JSON reference;
- duplicate/missing assets;
- actual page loading.

File existence or a WebP RIFF header alone is not sufficient validation.

## 11. QA

Run the narrowest QA that proves the change:
- Country-only changes → target Country validation and Browser QA;
- shared rendering changes → broader regression QA;
- image bytes → decode/dimension/path/duplicate checks;
- Map → map/coordinate/label checks.

Before the first canonical review, inspect the **rendered page built from the final delivered asset bytes**, not only approved image candidates or placeholder dimensions. At Desktop, Tablet and Mobile, check Hero crop, all eight Scenes, all four Taste cards (image-to-frame sizing, full dish visibility and backing), Map/labels, facts, related destinations and next routes together. Fix problems found in that pass before inviting the user to review; a load/decode PASS alone does not establish visual correctness.

For review feedback, reproduce each reported issue against the exact live build SHA and delivered assets. Consolidate related corrections into one minimal change, check the affected components locally at all three widths, then run only the relevant PR QA. After required checks pass, advance the PR through its guarded merge/deploy path and verify the exact canonical live SHA and affected rendering; do not restart full-country QA or create a separate PR merely to repeat checks already proved for unchanged bytes. Preserve any State update actually required by the publication pipeline and the final user-approval gate.

Do not equate CI success with visual completion. The actual rendered Country page must be checked at Desktop, Tablet and Mobile.

## 12. Review and publication

A finished new Country is first reviewed on its canonical URL:
`https://atlas.yagenji.com/countries/{slug}/`

During canonical review it remains:
- `atlasPublished:false`;
- `noindex,follow`;
- absent from sitemap;
- absent from normal discovery links.

A staging/Pages preview may support technical QA but is not the user’s final review URL.

Only explicit final page approval authorizes formal publication. Publication then changes discoverability/indexing and must verify the deployed production SHA and actual Country route. Automatic finalization runs only when `ATLAS_AUTO_PUBLISH=enabled` and an independently authorized `ATLAS_PUBLICATION_TOKEN` is configured in repository Actions settings; the GitHub Actions `GITHUB_TOKEN` is not a substitute for this credential. The token must have permission to update the Country branch, run Actions and merge its PR. Do not put an access token in chat or commit it to the repository.

Until that external identity is enabled and the end-to-end path is verified, use the connected GitHub account to finalize the **existing owner-authored Country PR** on latest main after final approval, preserve all publication gates, wait for the actual required `validate` and `browser-qa` checks on its current PR head, squash merge, and verify the deployed SHA and canonical page. Do not create another PR, use Actions-bot commits to force PR checks, or add empty commits to trigger checks. A skipped automatic finalizer is not a publication success.

Never treat review deployment as formal publication.

## 13. User gates

There are only four normal editorial user gates:
1. Hero approval;
2. eight-Scene batch approval;
3. four-Taste batch approval;
4. final canonical Country-page approval.

User asset handoff is an operational dependency, not an extra content approval gate.

If the next action is deterministic, execute it. Do not stop for progress confirmation or ask the user to say `進めて` between targets.

## 14. Compatibility

This document governs **new Countries**. Do not silently migrate an in-flight legacy Country to the new contract. Existing published Country pages and old State formats continue under their established compatibility rules until explicitly migrated or retired.

## 15. Definition of Done

A Country is complete only when:
- content, sources, Map and Themes are final;
- Hero, eight Scenes and four Taste images are approved and verified;
- JSON and assets pass current validators;
- actual Desktop/Tablet/Mobile page QA passes;
- the user approves the canonical unpublished page;
- formal publication completes after that approval;
- production route/deployment verification passes.

## 16. When a problem occurs

Use this order:
1. identify the concrete failure;
2. decide whether it is Country-specific or shared-system;
3. solve it without changing the approved product specification;
4. rerun only the relevant QA;
5. change the specification only if technically unavoidable and explicitly approved.

Do not add a permanent rule, workflow or state field for every one-off failure. Prefer removing the root cause or using an existing invariant.
