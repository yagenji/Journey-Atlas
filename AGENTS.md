# JOURNEY ATLAS — Development Rules

This file contains **repository-wide technical invariants only**. Do not duplicate Country production procedure here.

For a new Country, human production behavior is defined in `docs/COUNTRY_PRODUCTION_RULES.md`. Detailed machine contracts remain in the current validators/policies and should be read only when the active task requires them.

## 1. Product invariant

JOURNEY ATLAS is a quiet, adult travel atlas designed to make people want to know and visit a country through scenery and geography. Preserve the shared visual system and avoid advertising-style, sensational, childish or excessively decorative treatment.

## 2. Technical stack

Keep the existing simple architecture unless an explicit system change is approved:
- HTML;
- CSS;
- Vanilla JavaScript;
- Country JSON;
- Python only where build/QA automation needs it.

Do not introduce React/Next/Vue, unnecessary package systems, build frameworks or external libraries merely for one Country.

## 3. File responsibilities

- shared templates/UI belong in common HTML/CSS/JS;
- Country-specific editorial content, coordinates and image references belong in `data/countries/{slug}.json`;
- Theme assignment belongs in `data/theme-taxonomy.json`;
- canonical destination scope/publication discovery belongs in `data/atlas-destinations.json`;
- Country production progress belongs in `ops/country-production/{slug}.json` where applicable;
- approved Country assets belong under `assets/images/{slug}/` according to the current asset contract.

Do not copy common UI into Country-specific files or create Country-specific CSS/JS as a workaround for a shared problem.

## 4. Country data and geography

- Scene map markers and Scene cards derive from the same Country Scene data.
- Use real coordinates and reliable geographic data; never infer national borders, islands, roads, mountains, rivers or routes from memory or appearance.
- Visual label offsets may resolve collisions; real coordinates must not be falsified to make a Map look cleaner.
- Do not invent buildings, terrain, vegetation or landmarks in Country imagery.
- Unverified facts remain unfilled/TBD rather than guessed.

## 5. Factual data

Use reliable sources for population, area, language, religion, currency, geography, history, transport, seasonal operation and other factual claims.

For changing numerical data:
- `sourcesVerifiedAt` records when the source was checked;
- `sourceDates` records the period/date the displayed value describes;
- do not substitute `updatedAt` for either.

## 6. Shared design system

Do not create a new design language per Country. Use the existing tokens/components and `docs/DESIGN_SPEC.md` when exact typography or shared component detail is required.

Maintain the established font roles and readable text sizes. Do not solve layout problems by shrinking body text below the existing system.

Images contain no baked-in page text, map labels, buttons, cards or UI unless the asset contract explicitly requires it.

## 7. Responsive and accessibility

Country pages must remain usable on Desktop, Tablet and Mobile.

Maintain:
- semantic headings and link/button behavior;
- keyboard/focus behavior;
- touch interaction;
- `alt` / ARIA where required;
- non-color-only selected states;
- contrast;
- `prefers-reduced-motion` for added motion.

## 8. Change discipline

- Check current `main` and existing work before editing.
- Preserve unrelated user/branch changes.
- Change only files needed by the task.
- Prefer a shared fix for a proven shared defect; do not hide it in one Country.
- Do not change URL architecture, dependencies, common design, publication state or approved assets as an incidental workaround.
- Avoid destructive Git operations.
- Do not treat a CI pass as proof of visual correctness.

## 9. QA principle

Use the smallest QA scope that proves the actual change while preserving hard gates:
- Country-only change → target Country validation/Browser QA;
- shared rendering/build change → broader regression;
- asset change → identity/path/decode/dimension/duplicate checks;
- Map change → geometry/coordinate/label checks;
- production deployment → actual deployed route/SHA verification.

The actual rendered page is authoritative for visual QA.

## 10. Reading strategy

Do not preload the entire repository rule set into an assistant context.

At task start read only:
1. this file;
2. the task-specific human authority (`docs/COUNTRY_PRODUCTION_RULES.md` for a new Country);
3. the target Country JSON/State/branch information actually needed.

Open detailed Content, Map, Image, State or Publication machine documents only when entering that phase or diagnosing a concrete validator/workflow result. Do not repeatedly reread unchanged long files in the same work period.

## 11. Completion

A repository change is complete only when its relevant syntax/data checks pass and the affected real behavior is verified. Country-page completion additionally follows `docs/COUNTRY_PRODUCTION_RULES.md` and cannot be inferred from file existence, Build success or CI success alone.
