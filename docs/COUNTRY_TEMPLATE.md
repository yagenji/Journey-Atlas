# JOURNEY ATLAS Country Template v2

This document defines the reusable country-page contract for JOURNEY ATLAS.
Iceland is the reference implementation.

## Core rule

A country page must be rendered through one path only:

`country.html → assets/js/app.js → data/countries/{slug}.json`

Do not add country-specific JavaScript or country-specific CSS asset overrides to make a page work.
Country differences belong in the country JSON and country asset folder.

Production deployment adds one deterministic build step:

`source → validate published country data → build production assets → validate build → deploy`

The production build is `scripts/build_site.py` and is executed automatically by GitHub Actions.

## Required data structure

Each published country JSON uses `schemaVersion: 2` and contains:

- `slug`
- `nameEn`
- `nameJa`
- `region`
- `seo`
  - `description`
  - optional `ogImage`
- `capital`: capital object when the destination has a separate capital; `null` for a territory/SAR with no separate capital
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
- `travelScale`
- `seasons`
- `transport`
- `personas`
- `facts`
- `signatureFacts`
- `tips`
- optional `nextRoutes`: 0–3 representative cross-border journey routes
- `relatedCountries`
- `updatedAt`
- `sourcesVerifiedAt`
- `sourceDates`
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
Country-page navigation stays intentionally minimal: the top page and JOURNEY LENS are the primary exits.

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

#### Source date / provenance rule

`updatedAt` is the country JSON content-update date. It is **not** a substitute for the statistical reference period.

For published countries:

- `sourcesVerifiedAt` records the last source audit date as `YYYY-MM-DD`.
- `sourceDates` maps a source key to the period represented by that value.
- Population is always treated as time-sensitive and must have `sourceDates.population`.
- Other values that can change over time — for example religion share, annual energy mix, annual land-use share, membership counts, or other current statistics — must also record their reference period when known.
- Accepted period forms are `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, and `YYYY-Qn`.
- Use the **data reference period**, not merely the date on which the webpage was accessed.
- If the data period cannot be established from the source, do not invent one; keep the source citation and resolve the period before relying on the value as a current statistic.

Example:

```json
"sourcesVerifiedAt": "2026-08-28",
"sourceDates": {
  "population": "2026-Q2",
  "hydropower": "2025"
}
```

### Signature facts

Add exactly 3 country-specific facts under `signatureFacts`.
They should reveal something distinctive that a generic country profile does not.
Prefer a clear number or concise measurable fact.

Examples for Iceland:

- Population density
- Share of land covered by glaciers
- Share of electricity generated from renewable sources

Avoid trivia that is difficult to verify, rapidly becomes stale, or does not help the visitor understand the country.

### Encounters

`encounters` is an independent eight-item overview of what a visitor can expect to encounter while travelling through the country.

The eight Scenes are only eight real landscapes selected by JOURNEY ATLAS to show geographic and visual range. They are not an exhaustive inventory of the country. Encounters must therefore be selected by looking across the whole country, not by converting the Scene list into shorter labels.

- Use exactly 8 short, immediately understandable nouns or noun phrases.
- The eight items together must give a broad, multi-angle impression of the country rather than eight examples from one category.
- Consider multiple lenses such as geography/nature, streets and architecture, everyday life/work, mobility/public space, food, animals/season, belief/culture, and language/signage. These are lenses, not a fixed quota.
- A Scene element may also appear in Encounters when it is independently representative of the country. Never include it merely because it already appears in a Scene.
- Do not create Encounters by replacing the eight Scene titles with generic nouns. This is a content failure even when every individual term is understandable.
- Nature-led countries may legitimately contain more natural elements, but include other strong travel encounters when they materially help explain the country.
- Prefer common-language terms that can be pictured without explanation.
- A short locally rooted phrase may be used when its visual meaning is immediately clear, such as `白いゲル`, `韓屋の屋根`, or `寺廟の屋根飾り`.
- Avoid specialist vocabulary, obscure local names, named tools, niche traditions, product/brand names, and specific fictional/commercial characters when the term needs prior knowledge to make sense.
- A globally understood figure such as Santa Claus may be used when it works as a direct visual cue.
- Do not use Encounters to teach cultural trivia. Move explanatory cultural material to Beyond the Scenery or Travel Trivia.

Country QA must confirm all five points below:

1. The eight items are not paraphrases of the eight Scenes.
2. The set shows meaningful breadth across the country.
3. Every item is something a traveller can directly see, hear, taste, use, or experience on location.
4. The set does not depend on unexplained specialist/local terminology.
5. Representative value for the country outranks the convenience of reusing content already present elsewhere on the page.

### Scenery descriptions

Write as an atlas, not a tourism advertisement.
Prefer concrete geography, geology, history, scale, material, or observable characteristics.
Avoid generic promotional phrases such as “breathtaking,” “magical,” or “must-see.”

The shared scenery intro frames the eight selections for every country. Do not create a country-specific replacement unless the page structure itself changes globally.

### Travel Scale

`travelScale` uses a shared three-step UI, but the day ranges are country-specific.

Fixed across countries:
- exactly 3 items;
- kicker `DURATION`;
- title `旅の目安日程`;
- icons `city` / `map` / `compass` in that order;
- each item explains a realistic way to use that amount of time;
- **all three duration labels use days, and the third/final duration is always open-ended** (for example `8日以上`, `12日以上`, `14日以上`).

Not fixed:
- `3〜4日 / 5〜7日 / 8日以上` is **not** a global duration template;
- small countries may use shorter thresholds such as `半日〜1日 / 2日 / 3日以上`;
- geographically broad or travel-intensive countries may use thresholds such as `3〜4日 / 7〜10日 / 12日以上`.
- The final step represents the point from which a traveler can keep expanding regions or themes; do not impose an arbitrary upper limit.

Choose the ranges from the actual travel scale of the country: distribution of places, regional diversity, surface/air/sea transfer burden, islands or mountain access, and whether the proposed itinerary can be travelled without rushing. Country area alone is not sufficient.

Do not inflate a small country to fill the template, and do not compress a large country merely to preserve cross-country numerical uniformity. The three-step **information structure** is shared; the number of days is editorial content.

### Next Routes

`nextRoutes` is optional and contains 0–3 representative cross-border journeys.

- Show it only where a real, mainstream travel continuation exists.
- Prefer rail, road/coach, bridge or regular ferry travel that feels like one continuous trip.
- Do not create a route merely because two countries share a border.
- Do not create a route when flying is effectively the only mainstream continuation.
- Island countries may still qualify when a regular ferry route is itself a major travel pattern.
- Each item uses `flag / countryEn / countryJa / path / description`.
- Keep descriptions editorial: explain what landscapes, cities or cultural settings change along the route.
- Do not store fares, frequencies, exact journey times or service numbers.
- Route connectivity is time-sensitive: record `sources.nextRoutes` and `sourceDates.nextRoutes`.

### Next Destinations

`relatedCountries` is a preference recommendation layer: “if you liked this country, what else may you like?”

- Adjacency is not required.
- Select by landscape, geography, urban character, culture or travel style.
- Overlap with `nextRoutes` is allowed because the two sections answer different questions.
- The reason must explain the affinity, not merely describe crossing a border or continuing in a direction.

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

### Taste image production

Taste images follow `docs/TASTE_IMAGE_PRODUCTION.md`, which is the Single Source of Truth.

Key rules:

- one image / one generation request / one dish;
- a four-image batch is four independent sequential generations, not a collage;
- exact 3:2, final 1200×800;
- Spain Taste visual language, photo 6 : quiet watercolor 4;
- simple single vessel;
- plain pale beige / warm ivory background;
- no unrelated props, cutlery, napkins, drinks, ingredients around the dish, extra plates, people, hands, restaurant/kitchen/scenery backgrounds, text, logos, flags, or packaging;
- an integral garnish is allowed only on the same plate/bowl and only when normal for the dish;
- hard reject any collage, multi-dish image, prop-heavy background, or lifestyle food scene;
- regenerate only NG items; APPROVED Taste images are immutable unless the user explicitly requests regeneration.

## Asset rules

### Hero

Preferred source delivery is a direct high-resolution WebP/AVIF asset.
If repository/tooling limits require chunked base64 delivery, use a generic `.parts.json` manifest.
The source renderer can resolve the manifest as a fallback, but **production deployment must reconstruct it into a normal image file** through `scripts/build_site.py`.
Do not create a country-specific image loader.

### Scenic images

Use direct image or SVG-wrapper paths from the country JSON.
Do not override image paths in shared CSS.
Scene media is lazy-loaded by the shared renderer using `IntersectionObserver`; Hero remains eager.
Do not add country-specific eager-loading logic.

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

## CSS architecture

Country-page source styles remain separated by responsibility, but the browser should not load the legacy files one by one.

- source entrypoint: `assets/css/country.css`
- top-page entrypoint: `assets/css/top.css`
- production build concatenates the declared source files into one country bundle and one top bundle
- source order is defined only in `scripts/build_site.py`
- `country.html` loads only `country.css`
- generated production `index.html` loads only `top.css`

Do not add a new stylesheet link directly to `country.html`.
If a reusable style component is added, register it in the build source list and keep its responsibility clear.

## Static published URLs and SEO

Published countries are generated as static entry pages:

`/countries/{slug}/`

The query-string page remains as a compatibility/fallback route, but it is not the canonical search-index URL.

For every published country, the build generates or sets:

- static HTML entry page
- country-specific `<title>`
- `meta description`
- canonical URL
- Open Graph title / description / URL / image
- `twitter:card`
- `sitemap.xml`
- `robots.txt`

`data/atlas-destinations.json` is rewritten in the deployment artifact so published country links point to the static URL.
The source JSON should include a concise `seo.description`; `seo.ogImage` is optional and Hero is the default.

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

The country-page button explicitly says that the value is saved in the current browser.
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

## Automated validation

Published country pages are checked by:

`python scripts/validate_country.py --published`

The strict validator checks at least:

- `schemaVersion: 2`
- required template keys
- Hero / map / scene assets exist
- encoded Hero manifests fully reconstruct
- Hero, capital, and all scene coordinates sit inside map bounds
- exactly 8 scenes
- exact common-fact set and order
- `sourcesVerifiedAt` and source-period metadata for time-sensitive statistics
- rounded population display (no accidental decimal precision)
- exactly 3 signature facts
- exactly 3 `personas` entries for FOR WHOM
- non-empty atlas extras
- 4–6 travel trivia entries
- every trivia `sourceKey` exists in `sources`
- duplicate trivia / related-country identifiers

Both source validation and production-build validation must pass before Pages deploys.

## Release gate for every country

Before publishing a new country:

1. JSON parses successfully and uses `schemaVersion: 2`.
2. `seo.description` is written.
3. Hero asset/manifest exists and fully reconstructs.
4. Map SVG exists, is structurally complete, and matches its bounds.
5. Capital coordinates project inside the intended map area.
6. Exactly 8 scene assets exist.
7. All scene coordinates project inside the intended map area.
8. Common facts are present and population follows the display-rounding rule.
9. Three useful signature facts are sourced.
10. FOR WHOM contains exactly 3 `personas` entries.
11. Atlas extras are present where appropriate.
12. Travel trivia contains 4–6 traveler-relevant, sourced items.
13. Every trivia `sourceKey` resolves to an entry in `sources`.
14. Travel trivia does not duplicate `atlasExtras`, signature facts, tips, hero copy, or scene copy.
15. No country-specific runtime JS/CSS override is required.
16. Related countries never produce broken links.
17. Shared section-title hierarchy and icon styling remain intact.
18. Shared top/country header treatment remains intact.
19. `python scripts/validate_country.py --published` passes.
20. Production build creates the direct Hero asset, CSS bundles, static country page, sitemap, and robots file.
21. Desktop and mobile layouts are visually checked.
22. GitHub Pages deployment workflow succeeds.
23. Public page is visually reviewed after deployment.

## Reference country

`data/countries/iceland.json` is the current benchmark for schema, page structure, content depth, and production metadata.
New countries should follow the same data contract rather than copying Iceland-specific implementation details.
