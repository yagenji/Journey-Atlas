# JOURNEY ATLAS — NEW COUNTRY START

新規Country制作の開始指示。**人間向け制作ルールは `docs/COUNTRY_PRODUCTION_RULES.md` を1本だけ読む。** 機械ポリシー・Validator・Publication文書は、現在のState/NEXTで必要になったとき、または検証エラーを診断するときだけ参照する。

## Copy / paste

```text
JOURNEY ATLASの新規Country Pageを制作します。対象国：【国名】。
GitHub：yagenji/Journey-Atlas。

最新main、PROJECT MASTER INSTRUCTIONS、AGENTS.md、docs/COUNTRY_PRODUCTION_RULES.mdを確認してください。
その後、対象CountryのJSON・Production State・既存branchだけを確認し、未着手なら現在のinitializerで開始、既存Stateがあれば現在のNEXTから再開してください。

通常制作では長いmachine policyや過去のProduction文書を最初から読み込まないでください。State transition・validation failure・publication automationなど、現在の工程で必要になった場合だけ該当する正本を参照してください。

ユーザーゲート以外で不要に停止せず、承認済み素材や確定内容を理由なく作り直さず、実ページQAと正式公開までdocs/COUNTRY_PRODUCTION_RULES.mdに従って進めてください。
```

## 原則

- 新規Countryの通常チャットコンテキストへ機械ポリシー全文・旧Protocol全文・公開Workflow全文を読み込まない。
- Country Production Stateを再開点とし、チャット履歴から進捗を再構築しない。
- 必要なルールだけを必要な工程で取得する。
- 旧方式で進行中のCountryは無断移行しない。
- 機械ポリシーとValidatorは廃止しない。人間向け指示と機械検証の責務を分離する。
