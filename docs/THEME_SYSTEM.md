# JOURNEY ATLAS Theme System

`data/theme-taxonomy.json` is the single source of truth for top-level travel themes.
The same assignments are used by both the top-page theme filter and each country page.

## Assignment rule

Each destination should normally have 1–3 primary themes. Use 4 only when the travel motivation is genuinely broad and distinctive.

A theme is not assigned because an element merely exists in a country. It is assigned when that element is a strong reason a traveler would choose the destination.

Examples:

- Iceland: `earth`, `road`
- Norway: `earth`, `sea`, `road`

## Top-level themes

- `earth` — 地球の風景
- `city` — 街を歩く
- `history` — 時をたどる
- `life` — 暮らしに出会う
- `wildlife` — 野生に会う
- `sea` — 海の世界へ
- `food` — 食をめぐる
- `road` — 道の先へ

World Heritage, aurora, hot springs, wine, deserts and similar attributes are secondary characteristics, not separate top-level themes.

## Country-page behavior

Country pages read the same taxonomy and show the assigned primary themes in the Hero area under `TRAVEL THEMES`.
Do not duplicate theme labels inside each country JSON.

## Production workflow

Before publishing a new country:

1. Choose 1–3 primary themes.
2. Add the country slug to the corresponding `examples` arrays in `data/theme-taxonomy.json`.
3. Check that the top-page theme filter returns the country.
4. Check that the same themes appear on the country page.
5. If the country feels weak under a theme, remove the assignment rather than expanding the taxonomy.
