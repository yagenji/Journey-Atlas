# JOURNEY ATLAS — NEW COUNTRY START

新規Country制作の**短い開始指示**。ここには詳細な品質条件や公開手順を複製しない。最新の機械ポリシーと現在の運用文書が正本であり、旧チャットやこのファイルの固定文言より優先する。

## Copy / paste

```text
JOURNEY ATLASの新規Country Pageを制作します。対象国：【国名】。
GitHub：yagenji/Journey-Atlas。まず最新main、PROJECT MASTER INSTRUCTIONS、AGENTS.mdを確認してください。

新規制作の正本はmainのops/country-production-policy.jsonとops/image-generation-policy.jsonです。必要なフェーズに応じてdocs/COUNTRY_PRODUCTION_PROTOCOL_2.md、docs/CONTENT_QUALITY_RULES_V6.md、docs/MAP_SYSTEM.md、docs/PUBLICATION_PIPELINE_V2.md、docs/CANONICAL_UNPUBLISHED_REVIEW.mdを参照してください。詳細ルールをチャットへ丸ごと転記せず、現在の作業に必要な条件だけを使ってください。

最初に既存のCountry JSON・Production State・ブランチを確認してください。未着手ならcountry/{slug}で現在のProtocol 2 initializerを使用し、既存Stateがあるならそこから再開してください。進行中の旧方式Countryを無断移行しないでください。

制作はContentと地図・出典・現行QAの完了後にHeroへ進み、Hero個別承認→8景を各1枚ずつ独立生成して一括承認→Tasteを各1品ずつ独立生成して一括承認→承認済み13画像の一括格納・完全検証→実ページQAの順で進めてください。Iceland / NorwayのVisual Language、実在地の正確さ、共通Template・UIは変えないでください。

各工程はscripts/country_production_protocol_v2.py next {slug}の現在のinteraction.userGateに従ってください。ユーザーが必要な承認・画像格納・真正な障害以外で止まらず、画像ごとの「進めて」は求めないでください。途中で本文や承認済み素材を理由なく作り直さず、GitHubのStateを再開点として使ってください。

レビューはGitHub Pagesのステージングだけで完了扱いにしません。未公開のまま正規URL https://atlas.yagenji.com/countries/{slug}/ に反映してDesktop / Tablet / Mobileを確認します。この時点ではatlasPublished:false・noindex,follow・通常導線なし・sitemap非掲載を維持し、ユーザーの最終ページ承認後だけ正式公開してください。公開手順・PR数・最新mainとの統合は現行Publication Pipeline v2と正規URLレビューamendmentに従い、ここで固定しません。

最後に、実行済み検証・実ページURL・未解決事項だけを簡潔に報告してください。CI成功だけでページ完成と判断しないでください。
```

## 読み方と互換性

- 初回に最新mainと当該CountryのStateを確認し、各フェーズでは関連する正本と現行NEXTだけ参照する。同一ターンで未変更の長文仕様・Stateを繰り返し取得しない。SHA不一致やターンをまたぐ再開時には鮮度を確認する。
- PROJECT MASTER INSTRUCTIONSの品質・ユーザー承認・正式公開条件は省略してよい条件ではない。短い開始文はそれらを置き換えない。
- 旧Content QAおよび旧Publication方式の進行中Countryは、既存の契約を維持する。新規国用の短い開始文を旧国の移行許可として解釈しない。
- Review用Pagesは技術QA用であり、ユーザーの最終確認URLは未公開の正規URL。現行の未公開main統合と正式公開は別の操作である。
