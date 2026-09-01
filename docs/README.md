# Documentation index

JOURNEY ATLASの現行仕様を参照するための索引です。古い制作台帳や公開済みCountryの作業計画はmainに残さず、Git履歴を過去記録とします。

## Current source-of-truth documents

- `../AGENTS.md` — Repository共通の制作・実装ルール
- `../WORKFLOW.md` — Design lock、実装、Branch lifecycle
- `COUNTRY_TEMPLATE.md` — Country JSON / Template / release contract
- `COUNTRY_PAGE_TEMPLATE.md` — Country Pageの情報構成と表示要件
- `MAP_SYSTEM.md` — Country Mapの共通仕様とQA
- `THEME_SYSTEM.md` — TRAVEL THEMESの運用
- `ILLUSTRATION_STYLE_GUIDE.md` — 共通イラスト制作基準
- `DESIGN_SPEC.md` — 共通デザイン仕様
- `CLOUDFLARE_PAGES.md` — Production / review deployment
- `HERO_ART_BRIEF.md` — Top Hero visual brief

## Reference-country documents

- `ICELAND_ART_BRIEF.md`
- `ICELAND_QA.md`

Iceland / NorwayをCountry Pageの基準とし、国ごとの新しいデザイン言語は追加しません。

## Active draft country documents

- `ANTARCTICA_CONTENT_PLAN.md`
- `ANTARCTICA_QA.md`
- `TAJIKISTAN_CONTENT_PLAN.md`

これらは未完成Countryの作業資料であり、共通仕様より優先しません。

## Data source of truth

- `../data/atlas-scope.json` — 201 destinationsの範囲
- `../data/atlas-destinations.json`
- `../data/atlas-destinations-editorial.json` — Destination registry / publication state
- `../data/countries/{slug}.json` — Country固有情報
- `../data/theme-taxonomy.json` — TRAVEL THEMES
- `../data/region-taxonomy.json` — Region taxonomy
- `../data/illustration-briefs.json` — 201 destination illustration planning reference

## Do not use as source of truth

- GitHub branch names
- generated `countries/{slug}/index.html`
- old commits or archive tags
- published Countryの過去制作計画
- CI successだけを完成判定に使うこと

Production / review stateはRegistryとCountry JSON、実ページのQAで判断します。
