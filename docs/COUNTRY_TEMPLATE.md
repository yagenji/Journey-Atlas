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
- `capital`
  - `nameEn`
  - `nameJa`
  - `coordinates`
  - optional `labelPosition`
  - optional `mapOffset`
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
- `travelTrivia`
- `seasons`
- `transport`
- `personas`
- `facts`
- `signatureFacts`
- `tips`
- `relatedCountries`
- `updatedAt`
- `sources`

Reusable information items may include an optional `icon` key. The value must reference a symbol in `assets/icons/atlas-icons.svg`.

## Shared template copy

Explanatory text that describes how to use the layout belongs in `country.html`, not in each country JSON.

Current shared copy includes:

- scenery intro: `その国らしさが見えてくる、8つの景色。`
- map legend: numbered circles identify scenery and the diamond identifies the Hero image location; the legend sits below the map rather than in the editorial heading

Do not add a country name to the shared scenery intro. Country-specific meaning belongs in the eight scene descriptions themselves.
Keep the Travel Map heading concise; do not add explanatory guide copy beside it unless the shared layout changes globally.

## Shared site header

Top and country pages use the same JOURNEY ATLAS header scale and brand treatment.
Do not create a second country-only wordmark size, menu scale, or permanent menu enclosure.
The shared header remains visible while scrolling and is defined by the shared site stylesheet.

## Typography hierarchy

Japanese titles at the same section level use the same treatment:

- section title: 22px, Zen Kaku Gothic New, weight 600
- nested subsection title: 17px
- card title: 14–15px
- English kicker / metadata label: 9–11px

Do not create country-specific heading sizes.

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

#### Population display rule

Population is a visual-atlas comparison value, not a statistical dashboard.
Use a readable rounded figure in the visible page and keep the precise source figure in `sources`.

- Do not show thousand-level precision in the normal display.
- Prefer a rounded Japanese unit such as `約40万人` rather than `約39.7万人`.
- For larger populations, choose an equally readable `万人` or `億人` expression rather than unnecessary precision.
- Exceptions are allowed for very small countries/territories when rounding would materially distort scale.
- A country-specific exception must be intentional, not accidental source precision leaking into the UI.

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

The shared scenery intro frames the eight selections for every country. Do not create a country-specific replacement unless the page structure itself changes globally.

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

### Travel Trivia

`travelTrivia` contains small pieces of knowledge that make the actual trip more enjoyable.
Use 4–6 items per country; the shared renderer displays up to 6.

Each item should contain:

- `categoryEn`: short reusable category label
- `categoryJa`: Japanese category label
- `title`: one concise, memorable fact
- `text`: why it matters to a traveler or what they can notice/do locally
- `icon`: shared icon id
- `sourceKey`: key in the country-level `sources` object

Recommended reusable categories include:

- CUSTOMS / 習慣
- ETIQUETTE / マナー
- LANGUAGE / 言葉
- NAMES / 人名
- FOOD / 食
- EVERYDAY / 日常
- LOCAL TIP / 現地のコツ
- TRANSPORT / 移動

Selection rule: prefer facts that change what a visitor notices, tries, says, orders, or understands on location.
Avoid generic trivia, unsupported superlatives, myths, facts that are mainly clickbait, or claims likely to go stale quickly.
Every item must have a credible source recorded through `sourceKey`.

**No-overlap rule:** travel trivia must add a new layer of information. Before selecting an item, check it against `signatureFacts`, `atlasExtras`, `tips`, scene descriptions, and the hero copy. Do not repeat the same fact in a different card just because it is interesting.

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

### Capital marker

Every country page should show the capital on the travel map using the shared `capital` object.
The marker is deliberately quieter than numbered scenic markers and is not a scene.
Use geographic coordinates and, only when necessary for legibility, `labelPosition` or a small visual `mapOffset`.
Do not hand-position a capital independently of its coordinates.

## Related countries

Each related entry must include a `slug`.
The shared renderer checks `data/atlas-destinations.json`:

- published destination → clickable `EXPLORE`
- unpublished destination → non-clickable `COMING SOON`

Never create a broken link to an unpublished country page.

## Wishlist

Country pages store wishes locally using:

`journey-atlas:wish:{slug}`

The top page exposes a “行ってみたい国” control that filters the destination list to saved countries.
No login is required.

Operational limits are explicit:

- saved data belongs to the current browser/profile only
- it does not sync across devices
- clearing site data/private-browsing storage can remove it
- do not imply cloud/account persistence until an account backend exists

This local-first model is acceptable for the current static-site architecture and avoids collecting personal information.

## Icons

Use the shared SVG sprite at `assets/icons/atlas-icons.svg`.
Icons are a navigation and scanning aid, not decoration.

Rules:

- one-color line style
- shared 24×24 viewBox
- consistent stroke weight
- normal display size around 16–18px
- use `currentColor` so the template controls tone
- prefer semantic reuse across countries
- add a new symbol to the shared sprite only when the meaning will recur
- optional country JSON `icon` values may choose an existing shared symbol

Do not use ambiguous Unicode symbols such as △, ♢, ♧, ♜ or ▱ as substitutes for icons.
Emoji flags remain acceptable where a flag is specifically intended.

## Release gate for every country

Before publishing a new country:

1. JSON parses successfully and uses `schemaVersion: 2`.
2. Hero asset/manifest exists and fully reconstructs.
3. Map SVG exists, is structurally complete, and matches its bounds.
4. Capital coordinates project inside the intended map area.
5. Exactly 8 scene assets exist.
6. All scene coordinates project inside the intended map area.
7. Common facts are present and population follows the display-rounding rule.
8. Three useful signature facts are sourced.
9. Atlas extras are present where appropriate.
10. Travel trivia contains 4–6 traveler-relevant, sourced items.
11. Every trivia `sourceKey` resolves to an entry in `sources`.
12. Travel trivia does not duplicate `atlasExtras`, signature facts, tips, hero copy, or scene copy.
13. No country-specific runtime JS/CSS override is required.
14. Related countries never produce broken links.
15. Shared section-title hierarchy and icon styling remain intact.
16. Shared top/country header treatment remains intact.
17. Desktop and mobile layouts are visually checked.
18. GitHub `main` state is verified before public Pages review.
19. Public page is visually reviewed only after all earlier gates pass.

## Reference country

`data/countries/iceland.json` is the current benchmark for schema, page structure, and content depth.
New countries should follow the same data contract rather than copying Iceland-specific implementation details.
