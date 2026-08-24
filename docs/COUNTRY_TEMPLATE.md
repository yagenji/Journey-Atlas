# JOURNEY ATLAS Country Template v2

This document defines the reusable country-page contract for JOURNEY ATLAS.
Iceland is the reference implementation.

## Core rule

A country page must be rendered through one path only:

`country.html → assets/js/app.js → data/countries/{slug}.json`

Do not add country-specific JavaScript or country-specific CSS asset overrides to make a page work.
Country differences belong in the country JSON and country asset folder.

## Required data structure

Each country JSON uses `schemaVersion: 2` and should contain:

- `slug`
- `nameEn`
- `nameJa`
- `region`
- `hero`
  - `lead`
  - `image`
  - `location`
  - `coordinates`
  - optional `mapOffset`
- `map`
  - `bounds`
  - `svg`
  - `source`
- `scenes`: exactly 8 benchmark scenic entries
- `encounters`
- `atlasExtras`
- `seasons`
- `transport`
- `personas`
- `facts`
- `signatureFacts`
- `tips`
- `relatedCountries`
- `updatedAt`
- `sources`

## Information design

### Common basic facts

Keep a stable shared set so countries remain comparable:

1. Region
2. Capital
3. Population
4. Area
5. Language
6. Main religion / belief context where appropriate
7. Currency

The common facts are not replaced by country-specific information.

### Signature facts

Add 3 country-specific facts under `signatureFacts`.
They should reveal something distinctive that a generic country profile does not.
Prefer a clear number or concise measurable fact.

Examples for Iceland:

- Population density
- Share of land covered by glaciers
- Share of electricity generated from renewable sources

Avoid trivia that is difficult to verify, rapidly becomes stale, or does not help the visitor understand the country.

### Scenery descriptions

Write as an atlas, not a tourism advertisement.
Prefer concrete geography, geology, history, scale, material, or observable characteristics.
Avoid generic promotional phrases such as “breathtaking,” “magical,” or “must-see.”

### Beyond the Scenery

`atlasExtras` expands the country beyond landscapes.
Use the shared JOURNEY ATLAS theme vocabulary where relevant, such as:

- CITY
- HISTORY
- LIFE
- WILDLIFE
- FOOD
- ROAD

The purpose is breadth without turning the page into a conventional travel guide.

## Asset rules

### Hero

Preferred delivery is a direct high-resolution WebP/AVIF asset.
If repository/tooling limits require chunked base64 delivery, use a generic `.parts.json` manifest.
The shared renderer resolves the manifest; do not create a country-specific loader.

### Scenic images

Use direct image or SVG-wrapper paths from the country JSON.
Do not override image paths in shared CSS.

### Map

The country JSON is the single source of truth for map SVG and projection bounds.
Do not override map source or bounds at runtime.

Map geometry must come from geographic data, not AI generation or manually guessed country silhouettes.
For the map design rules, see `docs/MAP_SYSTEM.md`.

## Related countries

Each related entry must include a `slug`.
The shared renderer checks `data/atlas-destinations.json`:

- published destination → clickable `EXPLORE`
- unpublished destination → non-clickable `COMING SOON`

Never create a broken link to an unpublished country page.

## Wishlist

Country pages store wishes locally using:

`journey-atlas:wish:{slug}`

The top page exposes a “行ってみたい国” filter.
No login is required.

## Symbols and icons

Avoid ambiguous Unicode symbols as decoration.
Text labels, typography, spacing, and the established map-marker system should carry the hierarchy.
Only use an icon when it has a consistent system-wide meaning.

## Release gate for every country

Before publishing a new country:

1. JSON parses successfully and uses `schemaVersion: 2`.
2. Hero asset/manifest exists and fully reconstructs.
3. Map SVG exists, is structurally complete, and matches its bounds.
4. Exactly 8 scene assets exist.
5. All scene coordinates project inside the intended map area.
6. Common facts are present.
7. Three useful signature facts are sourced.
8. Atlas extras are present where appropriate.
9. No country-specific runtime JS/CSS override is required.
10. Related countries never produce broken links.
11. Desktop and mobile layouts are visually checked.
12. GitHub `main` state is verified before public Pages review.
13. Public page is visually reviewed only after all earlier gates pass.

## Reference country

`data/countries/iceland.json` is the current benchmark for schema, page structure, and content depth.
New countries should follow the same data contract rather than copying Iceland-specific implementation details.
