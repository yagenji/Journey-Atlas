# JOURNEY ATLAS Theme System

`data/theme-taxonomy.json` is the single source of truth for top-level travel themes.
The same assignments are used by both the top-page theme filter and each country page.

## Assignment rule

Aim for 3 primary themes per destination when all three work as useful travel tags.
Use only 1 or 2 when a third theme would be weak, repetitive, or artificial.

A theme is not assigned because an element merely exists in a country. It is assigned when it meaningfully describes why or how someone would travel there.

Examples:

- Iceland: `earth`, `road`, `wildlife`
- Norway: `earth`, `sea`, `road`
- Antarctica: `earth`, `wildlife` — no third theme is forced

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

1. Start by looking for 3 useful primary themes.
2. Keep 1 or 2 if a third theme is not genuinely useful.
3. Add the country slug to the corresponding `examples` arrays in `data/theme-taxonomy.json`.
4. Check that the top-page theme filter returns the country.
5. Check that the same themes appear on the country page.
6. If a theme feels weak or merely technically present, remove it rather than forcing the count to three.
