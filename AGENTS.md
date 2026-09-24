# JOURNEY ATLAS — Development Rules

This file contains repository-wide technical invariants only. New-Country production procedure is defined in `docs/COUNTRY_PRODUCTION_RULES.md`.

## 1. Product invariant

JOURNEY ATLAS is a quiet, adult travel atlas designed to make people want to know and visit a country through scenery and geography. Preserve the shared visual system and avoid advertising-style, sensational, childish or excessively decorative treatment.

## 2. Technical stack

Keep the existing simple architecture unless an explicit system change is approved:
- HTML;
- CSS;
- Vanilla JavaScript;
- Country JSON;
- Python only for build/QA tooling.

Do not introduce React/Next/Vue, unnecessary package systems, build frameworks or external libraries merely for one Country.

## 3. File responsibilities

- shared templates/UI belong in common HTML/CSS/JS;
- Country-specific editorial content, coordinates and image references belong in `data/countries/{slug}.json`;
- Theme assignment belongs in `data/theme-taxonomy.json`;
- canonical destination scope/publication discovery belongs in `data/atlas-destinations.json`;
- approved Country assets belong under `assets/images/{slug}/`.

New-Country production progress is not a repository contract. Do not create Country Production State files, approval ledgers or generation-history files.

## 4. Country data and geography

- Scene map markers and Scene cards derive from the same Country Scene data.
- Use real coordinates and reliable geographic data.
- Never infer national borders, islands, roads, mountains, rivers or routes from memory or appearance.
- Visual label offsets may resolve collisions; real coordinates must not be falsified.
- Do not invent buildings, terrain, vegetation or landmarks.
- Unverified facts remain unfilled/TBD rather than guessed.

## 5. Factual data

Use reliable sources for population, area, language, religion, currency, geography, history, transport, seasonal operation and other factual claims.

For changing numerical data:
- `sourcesVerifiedAt` records when the source was checked;
- `sourceDates` records the period/date represented by the displayed value;
- do not substitute `updatedAt` for either.

## 6. Shared design system

Do not create a new design language per Country. Use existing tokens/components and `docs/DESIGN_SPEC.md` when exact shared component detail is required.

Maintain established font roles and readable text sizes. Do not solve layout problems by shrinking body text below the shared system.

Images contain no baked-in page text, map labels, buttons, cards or UI unless the asset contract explicitly requires it.

## 7. Responsive and accessibility

Country pages must work on Desktop, Tablet and Mobile.

Maintain:
- semantic headings and link/button behavior;
- keyboard/focus behavior;
- touch interaction;
- alt / ARIA where required;
- non-color-only selected states;
- contrast;
- reduced-motion support for added motion.

## 8. Change discipline

- Check current `main` and existing work before editing.
- Preserve unrelated user/branch changes.
- Change only files needed by the task.
- Prefer a shared fix for a proven shared defect.
- Do not change URL architecture, dependencies, common design, publication state or approved assets as an incidental workaround.
- Avoid destructive Git operations.
- Do not treat CI success as proof of visual correctness.

## 9. QA principle

QA inspects finished artifacts; it does not control production progress.

Use the smallest QA scope that proves the change:
- Country content → target schema/editorial QA;
- asset set → decode/dimension/duplicate QA;
- Map → geometry/coordinate/label QA;
- Country rendering → target Desktop/Tablet/Mobile Browser QA;
- shared rendering/build change → broader regression;
- production deployment → deployed route/SHA verification.

The actual rendered page is authoritative for visual QA.

## 10. Reading strategy

At a new-Country task start read only:
1. this file;
2. `docs/COUNTRY_PRODUCTION_RULES.md`;
3. the target Country JSON if it already exists.

Read `IMAGE_QUALITY.md`, `CONTENT_QUALITY.md` and `MAP_QUALITY.md` when entering those tasks. Do not preload retired production-state or publication-pipeline documents.

## 11. Completion

A repository change is complete only when relevant syntax/data checks pass and affected real behavior is verified. Country-page completion additionally requires final user approval and production verification as defined in `docs/COUNTRY_PRODUCTION_RULES.md`.
