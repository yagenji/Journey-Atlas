# Documentation index

JOURNEY ATLASの現行仕様を参照するための索引です。公開済みCountryの過去制作計画は、現行State・仕様・実装から参照されていないことを確認して削除し、Git履歴を過去記録とします。未公開Countryの作業資料と承認記録の参照先は維持します。

## Current source-of-truth documents

- `../ops/country-production-policy.json` — Country制作の機械可読な正本
- `../ops/image-generation-policy.json` — 画像制作の機械可読な正本
- `COUNTRY_PRODUCTION_PROTOCOL_2.md` — 新規Countryの制作手順
- `PUBLICATION_PIPELINE_V2.md` — Review / publication automation
- `CONTENT_QUALITY_RULES_V6.md` — 新規CountryのContent QA。既存Countryは宣言済みversionに従う
- `IMAGE_POLICY_REVISION_7_2.md` — 現行画像制作ルール
- `COUNTRY_PRODUCTION_STATE.md` — Country Production Stateの契約
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

Reference v3の役割分担は `PUBLISHED_COUNTRY_RENEWAL.md` に従います。Iceland / Norwayはビジュアル言語、Spainは現行構造・情報密度・UIの実装基準です。国ごとの新しいデザイン言語は追加しません。

## Active draft country documents

- `ANTARCTICA_CONTENT_PLAN.md`
- `ANTARCTICA_QA.md`
- `ROMANIA_CONTENT_PLAN.md`

これらは未完成Countryの作業資料であり、共通仕様より優先しません。

## Retained production references

- `RUSSIA_CONTENT_PLAN.md` — 公開済みですが、`../ops/country-production/russia.json` のRender Packetから参照されるため維持
- `renewal-audits/` / `renewal-content/` — Renewalの判断根拠。過去制作計画の削除対象とは別に依存確認する

## Cleanup continuity

- `CLEANUP_STATUS.md` — データ・旧資料・互換処理の整理状況と、保留中の依存関係

## Data source of truth

- `../data/atlas-destinations.json` — canonical 201 destinationsの範囲・Destination registry・publication state。台湾・香港・マカオ・南極を含む単一正本
- `../data/countries/{slug}.json` — Country固有情報
- `../data/theme-taxonomy.json` — TRAVEL THEMES
- `../data/region-taxonomy.json` — Region taxonomy。Asiaは49 destinations
- `../data/illustration-briefs.json` — 201 destination illustration planning reference

台湾・香港・マカオ・南極を独立destinationとして扱うのは旅行先としての探索性を目的とした編集上の区分であり、国家承認に関する立場を示すものではありません。

## Do not use as source of truth

- GitHub branch names
- generated `countries/{slug}/index.html`
- old commits or archive tags
- published Countryの過去制作計画
- CI successだけを完成判定に使うこと

Production / review stateはRegistryとCountry JSON、実ページのQAで判断します。Destination scopeは `scripts/validate_destination_scope.py` でcanonical registryの201件・Asia 49件・台湾/香港/マカオ/南極包含を機械検証します。
