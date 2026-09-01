# JOURNEY ATLAS

景色と地図からその国を知り、まだ知らなかった場所へ行ってみたいと思う体験をつくるビジュアル・トラベルアトラスです。

## Source of truth

- Destination scope: `data/atlas-scope.json`
- Destination registries: `data/atlas-destinations.json` / `data/atlas-destinations-editorial.json`
- Country content: `data/countries/{slug}.json`
- Travel themes: `data/theme-taxonomy.json`
- Region taxonomy: `data/region-taxonomy.json`
- Shared Country template: `country.html`
- Country map generator: `scripts/generate_country_map.py`

Country固有情報はCountry JSONへ置き、共通UIはCountry Templateで共有します。Iceland / NorwayをCountry Pageの基準とします。

## Publication state

`atlasPublished` が公開状態の正本です。

- `false`: レビュー可能。直接URL表示可、`noindex,follow`、通常導線・sitemapには載せない。
- `true`: ユーザー承認済みの正式公開。通常導線、`index,follow`、sitemapを有効化する。

標準Country URL:

`https://atlas.yagenji.com/countries/{slug}/`

`schemaVersion: 2` のCountry JSONは、正式公開前でもビルド時にレビュー用Country Pageを生成します。

## Generated files

`countries/{slug}/index.html` は `scripts/build_site.py` がビルド時に生成する成果物です。Gitでは管理しません。

Production packageにはブラウザ実行に必要なruntime dataとreviewable Country JSONのみを含め、制作管理用JSON・scripts・CI設定は含めません。

## Validation

Country JSON、公開Registry、Map、Theme、production packageを検証します。

```bash
python3 scripts/validate_country.py --reviewable
python3 scripts/validate_country.py --published
python3 scripts/build_cloudflare.py
```

GitHub Actions:

- `.github/workflows/validate-country-data.yml`
- `.github/workflows/deploy-pages.yml`

## Branch policy

ブランチ運用の詳細は `WORKFLOW.md` の **Branch lifecycle** を参照してください。

基本は `main` + 現在作業中のCountry / 共通修正ブランチのみとし、review・publish・QAのためだけの派生ブランチは作りません。
