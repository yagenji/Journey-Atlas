# JOURNEY ATLAS — Country制作の簡素化（作業案）

Status: DRAFT / NON-AUTHORITATIVE. Updated: 2026-09-17.
Baseline: `main` commit `d5a24fee70465ce9cafb3ceaedd3ec041fcae3b6` (US publication #914).
This is a single temporary working document; it does **not** supersede any current policy, change production behavior, or authorize publication. Delete or fold this document into the adopted authority at cutover; do not retain parallel rules.

## 目的

国の景色と地図を通じてその国を知り、行ってみたくなるCountry Pageを、品質を変えずに少ない作業・待機・チャット内情報量で制作する。ルールの数やCIの数ではなく、完成ページの品質と制作の実測値で判断する。

## 現行の事実と未検証の仮説

- **確認済み**: `ops/country-production-policy.json` は新規CountryのHero生成前に編集・地図・出典・複数QAの完了を要求している。Hero、8景バッチ、Tasteバッチ、正規URLの最終承認がユーザーゲート。
- **確認済み**: `ops/image-generation-policy.json` には生成予約、対象照合、履歴・コンテキストの管理がある。既に同一ターン内の再読込を減らし、Country CIをフェーズ遷移時に限定する最適化も含む。
- **確認済み**: `docs/PUBLICATION_PIPELINE_V2.md` と `docs/CANONICAL_UNPUBLISHED_REVIEW.md` は、ステージング確認後、未公開の正規URLに反映してユーザーが確認し、最終承認後に正式公開する。旧ProtocolのPR記述は後日のamendmentと併読する必要がある。
- **確認済み**: `docs/CLEANUP_STATUS.md` によると、destination正本は `data/atlas-destinations.json`、正式スコープは201、Asiaは49、Hong Kong/Macaoは独立、Theme正本は `data/theme-taxonomy.json`。既存データクリーニングとBranch Hygieneは別作業。
- **未検証の仮説**: 長い指示、各画像ごとの状態処理、二重検証、再デプロイが制作時間やコンテキスト負荷の大きな割合を占める。現時点では工程別の時間・メモリ値を取得しておらず、削減効果は断定しない。

## 短い制作契約（提案・未発効）

1. **CONTENT**: その国で見せたいHero・8景・料理・文章・出典・地点を確定。Country固有情報はJSON、Themeはtaxonomy、共通表示は共通Templateに置く。
2. **VISUAL**: 実在性・地形・建築を尊重した静かな水彩シリーズ。Heroは個別承認、各Scene/料理は1回の生成につき1対象・1画像、8景とTasteはそれぞれバッチ承認。承認素材を無断で変えない。
3. **IMPLEMENT**: 承認済み画像の完全decode・寸法・パスを一括検証し、地図とJSONを共通Templateへ接続。位置は緯度経度を基準とする。
4. **QA / REVIEW**: 編集・地図・画像・パッケージを対象国中心に検証。実ページをDesktop/Tablet/Mobileで確認。正式承認前は正規URLで `atlasPublished:false`、`noindex,follow`、通常導線なし、sitemap非掲載を維持。
5. **PUBLISH**: ユーザーが実ページを最終承認した後だけ `atlasPublished:true` にし、デプロイ済みSHA・公開URL・導線・sitemap・Browser QAを確認する。

この5段階は運用上の見出しであり、既存ValidatorやWorkflowを置き換える実装ではない。明確な安全条件を削除して短く見せることは禁止。

## 変更できない品質・安全境界

- Iceland/NorwayのVisual Language、Hero＋8景、必要なTaste、正確な地図、文章・出典、既存共通UI、Desktop/Tablet/MobileとAccessibility。
- `data/atlas-destinations.json` の201 destinationと `data/theme-taxonomy.json` の正本性。既存公開Countryを巻き戻さない。
- 画像の実在性・重複禁止・破損確認、必要なユーザー承認、正式公開前のnoindex/非リンク/非sitemap。
- 旧方式のin-flight Countryを黙って新方式へ移行しない。`main`・公開サイト・Branch Hygieneはこの作業では変更しない。

## 削減候補（依存調査・実測後に判定）

| 候補 | 調査すること | 安全に削減できる条件 |
| --- | --- | --- |
| プロンプト・仕様書の重複 | `AGENTS.md`、Project instructions、Protocol、image policy間の重複と実行時に参照する範囲 | 正本を1つにし、他は短い参照にできること |
| 画像状態の読み書き | 生成予約・照合・ledgerの呼び出し数と実際の誤生成防止効果 | 誤対象・重複・承認履歴を失わず処理回数を減らせること |
| Validatorの重なり | editorial v2、quality v5(v6 route)、map v6、state系の実行経路・同一入力の重複 | 検出能力を維持して統合でき、旧Country互換が残ること |
| CI / Browser QA | 各Workflowのtrigger、同じcommitでのBuild・Browser実行回数、実行時間、失敗理由 | 変更対象の検証を維持し、正規URLのライブQAを残せること |
| レビュー・公開 | Pages staging、Cloudflare未公開、正式公開の役割と重複 | 正規URLでの未公開ユーザーレビューと承認後の正式公開を維持できること |

## 実装前の測定・採否条件

- 比較対象は**同種の新規Country**。以前のスロベニア公開済みリニューアルと新規制作を直接比較しない。
- 画像生成時間・生成試行数、ツール呼出数、状態読み書き回数、CI回数と経過時間、Browser QA回数、PR/merge/Deploy回数、ユーザー操作回数、手戻り理由を工程別に集計する。
- ChatGPTコンテキスト使用量とブラウザ/Actionsの実メモリは別指標とする。取得できない指標は「未測定」とする。
- まずread-onlyで依存関係を特定し、独立した削減のみ作業ブランチで試す。旧・新双方のテスト、1か国の実ページ確認を通過するまで正本やWorkflowを置き換えない。
- 効果がなければその削減を撤回する。完了後は本作業案を新しい唯一の正本へ統合し、旧ルールの重複参照を除去する。

## 次の具体作業（未完）

1. 最新mainに再同期して `AGENTS.md`、ルール、State、scripts、Workflowの参照関係を一覧化する。
2. 代表的な新規CountryのActions実行履歴でボトルネックを計測する。
3. 高コストかつ安全に切り離せる1点から変更し、対象検証・既存国回帰テスト・実ページQAを通す。
4. 新方式の採用条件を満たした場合のみ正本を切り替える。ユーザー承認なく正式公開や既存国の品質変更を行わない。
