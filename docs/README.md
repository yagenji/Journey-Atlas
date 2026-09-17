# Documentation index

JOURNEY ATLASの現行仕様への索引です。公開済みCountryの過去制作計画は、現行State・仕様・実装から参照されていないことを確認して削除し、Git履歴を過去記録とします。未公開Countryの作業資料と承認記録の参照先は維持します。

## New Country: read only what is needed

制作開始時の人間向け正本は **`COUNTRY_PRODUCTION_RULES.md` 1本**です。共通の技術的不変条件は `../AGENTS.md`、再開点は対象CountryのJSONとProduction Stateです。初回から以下の全資料を読まないでください。State transition・画像生成・Content QA・Map QA・review/publishなど、現在の工程で必要になったものだけ対応する機械正本・仕様を参照します。

`COUNTRY_PRODUCTION_PROTOCOL_2.md` は旧文書からの互換参照であり、新規国の制作指示書ではありません。旧方式で進行中のCountryは無断移行しません。

## Source-of-truth and phase-specific references

- `COUNTRY_PRODUCTION_RULES.md` — **新規Countryの人間向け制作ルールの唯一の正本**
- `../AGENTS.md` — Repository全体の技術的不変条件
- `../ops/country-production-policy.json` — Country制作の機械可読な正本（必要時のみ）
- `../ops/image-generation-policy.json` — 画像制作の機械可読な正本（必要時のみ）
- `COUNTRY_PRODUCTION_PROTOCOL_2.md` — Protocol 2の技術的互換参照。新規国の起動時には読まない
- `PUBLICATION_PIPELINE_V2.md` — Review / publication automation
- `CONTENT_QUALITY_RULES_V6.md` — 新規CountryのContent QA。既存Countryは宣言済みversionに従う
- `IMAGE_POLICY_REVISION_7_2.md` — 現行画像制作の詳細
- `COUNTRY_PRODUCTION_STATE.md` — Country Production Stateの契約
- `../WORKFLOW.md` — 固有のDesign lock、トップページ、Branch lifecycle。Country制作手順は保持しない
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
