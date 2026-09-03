# JOURNEY ATLAS — Published Country Renewal Protocol

## Purpose

This workflow is for Country Pages that are already published. It is separate from new-country production.

The goal is to renew all published countries to one current standard without rebuilding acceptable work unnecessarily.

## Source of truth

Renewal status is stored in:

`data/country-renewal-status.json`

Do not maintain a second manual status list in Country JSON.

## Core rule

**Audit all → fix shared system issues → renew countries by wave → regress → global final QA.**

Do not redesign the common Country Page while renewing individual countries unless the audit proves a shared defect.

## Work types

Every finding must be classified before implementation.

- **SYSTEM** — shared template / CSS / JS / QA / accessibility. Fix once in the common layer.
- **CONTENT** — country-specific data and copy. Fix in Country JSON / taxonomy / sources.
- **VISUAL** — Hero, scenes, map visual quality. Requires visual QA and normal approval flow.

## Audit classification

Each country is classified after audit:

- **A — light renewal**: current Hero / scenes / map can largely remain; mainly content and current-section alignment.
- **B — medium renewal**: some visual replacement, map work, or substantial content changes.
- **C — rebuild-level renewal**: scene selection / asset quality / map / content materially below the current standard.

Do not classify a country from reputation or age alone. Classify from the actual current page and source assets.

## Reference v3

Reference responsibilities are deliberately split.

### Iceland / Norway — visual language reference
Use them for the JOURNEY ATLAS series character: recognizable real places, calm 60:40 photo-to-illustration balance, refined travel-atlas tone, map importance, and restrained composition.

**Important:** Norway's legacy 320–360px scene files are not the current production-resolution standard. Norway must itself be renewed.

### Spain — current structure / information-density / UI reference
Use Spain for the current shared Country Page structure, six-item Country Profile, responsive behavior, compact travel area, NEXT DESTINATIONS, and JOURNEY LENS handoff.

### Current image production rule
For renewed countries:
- approved Hero + 8 approved scenes;
- scenes normally 1200×800 / 3:2;
- complete raster decode;
- no broken assets;
- no unused files in an approved production folder;
- visual approval still takes precedence over automation.

## Renewal sequence

### Phase 0 — standard lock
Freeze the common structure and current shared UI before country work.

### Phase 1 — all-country audit
Audit all published Country Pages before broad implementation. Record KEEP / FIX / REWRITE / REGENERATE decisions for:
- Hero
- 8-scene selection
- scene assets
- map
- Country Profile
- Signature Facts
- Encounters
- Beyond the Scenery
- Travel Trivia
- Taste
- Travel Scale
- Seasons
- Transport
- For Whom
- Travel Notes
- Themes
- sources
- Desktop / Tablet / Mobile

### Phase 2 — shared fixes
If the same issue affects multiple countries, fix the common layer once. Do not add country-specific CSS as a workaround.

### Phase 3 — country delta sheet
For each country, renew only the items that the audit marked for change. KEEP is a valid result.

### Phase 4 — wave production
Work in the wave order recorded in `data/country-renewal-status.json`.
The first wave is Iceland / Norway / Spain so the new standard is represented by actual production pages.

### Phase 5 — visual production
Only regenerate images marked for replacement. Keep one active image target at a time and use the normal APPROVED workflow.

### Phase 6 — visual-complete gate
Do not connect replacement visuals to production until all required replacement images for that country are approved.

### Phase 7 — implementation
Country-specific changes belong in Country JSON / taxonomy / approved assets. Shared UI remains shared.

### Phase 8 — QA
Run automation first, then human visual QA.

Automation covers JSON, themes, source/assets, image decode, dimensions, map rules, route/build/package and approved-folder hygiene.

Human QA covers visual hierarchy, crop, recognizability, watercolor balance, map readability, long copy, Desktop / Tablet / Mobile and series consistency.

### Phase 9 — production review
Review on `https://atlas.yagenji.com/countries/{slug}/`.

### Phase 10 — wave regression
At the end of each wave, regress Iceland / Norway / Spain plus the wave countries.

### Phase 11 — global final QA
After all published countries are renewed, run the full published-country hard gate and final visual review.

## Image QA policy: audit vs hard gate

Image QA has two modes during the renewal program.

### AUDIT
All published countries are scanned. Legacy failures are reported but do not block unrelated work.

This is not an exception to the quality standard. It is a migration-state report.

### HARD
Only countries with `hardImageGate: true` in the renewal status are blocking.

Set `hardImageGate: true` only after that country has completed the renewal image gate. From then on, regressions block CI.

When all published countries are renewed, every published country must have `hardImageGate: true`.

## Branch lifecycle

Use one branch for the currently active country or one shared common-fix branch. After merge, remove obsolete branches. Do not create separate review / QA / publish branches for the same country.
