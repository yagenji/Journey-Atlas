# JOURNEY ATLAS — NEW COUNTRY START

Updated: 2026-09-10

## Purpose

This is the canonical reusable start instruction for a new JOURNEY ATLAS Country Page.

Do not maintain a separate long master prompt per Country. Project rules live in the repository; operational progress lives in Production State.

## Copy / paste start prompt

```text
JOURNEY ATLASの新規Country Page制作を開始します。

対象国：
【国名】

GitHub：
yagenji/Journey-Atlas

PROJECT MASTER INSTRUCTIONSとGitHub mainの最新仕様を使用してください。

最初に main の `ops/image-generation-policy.json` を確認し、画像生成ルールの最新revision / patchを確定してください。その後、ops/country-production/{slug}.json をmainから確認してください。

Production Stateが存在する場合：
- stateRef / contentRef が country/{slug} を指していれば、そのbranchのProduction Stateを再取得し、そちらを正本としてPHASE / NEXT ACTION / NEXT ASSETから再開してください。
- stateRef が main ならmainを正本としてください。

mainにProduction Stateが存在しない場合：
- country/{slug} branchを確認し、そこにStateがあればそのStateを正本としてください。
- 完全な新規Countryならcountry/{slug} branchを先に作成し、mainの最新Policyに準拠するStateをそのbranchに初期化してください。
- active production中のState更新のためにmain PRを作成しないでください。
- 手作業で古いrevision 2 / 3 Stateを複製しないでください。

制作進行・承認ゲート・Batch処理・QA・Review Deployment・Publishは docs/COUNTRY_PRODUCTION_STATE.md に従ってください。
Scene / Hero画像は docs/SCENE_IMAGE_PRODUCTION.md に従ってください。
Taste画像は docs/TASTE_IMAGE_PRODUCTION.md に従ってください。

Content Planは何を作るかだけを保持し、PHASE / NEXT IMAGE / APPROVED状態 / generation cursor / failure logを持たせないでください。

通常のユーザー承認はHero、8景Batch、Taste Batch、Canonical URL最終確認のみとし、それ以外はBlocking Issueがない限り自動進行してください。

【画像ラウンドの絶対実行ルール】
- 1画像 = 1独立生成リクエストを守ってください。複数Scene / 複数料理を1つの生成プロンプトにまとめてはいけません。
- ただし、1画像 = 1ユーザー操作ではありません。正常な画像1枚の生成完了をユーザー承認ゲートにしてはいけません。
- SCENES_INITIALでは、S01を生成・reconcileしたらStateを再取得し、Blocking IssueがなければS02へ進み、同じ手順でS08まで自動継続してください。S01〜S08の途中で「approve」「進めて」「生成」等のユーザー入力を要求してはいけません。
- TASTE_INITIALでも、FOOD01を生成・reconcileしたらStateを再取得し、Blocking IssueがなければFOOD02→FOOD03→FOOD04まで自動継続してください。FOOD01〜FOOD04の途中で個別承認を要求してはいけません。
- ユーザー承認を求めるのは、8景すべてのinitial roundが終了した時点のScene Batch Review、および料理4枚すべてのinitial roundが終了した時点のTaste Batch Reviewのみです。
- 画像生成ランタイムが実際にassistant turnを強制終了した場合だけ次ターンへ跨いで構いません。ただし、それは承認ゲートではありません。次にユーザー入力が来たら、前画像の承認確認をせず、reconcile後のNEXTへ直ちに自動継続してください。

新規Stateには `imageGenerationPolicyRef: "main:ops/image-generation-policy.json"` を設定し、mainの最新policy revision / patchを使用してください。Country branch側の古いpolicy snapshotでmainのpolicyを上書き・巻き戻ししないでください。Hero / Scene / Tasteの全生成対象にcontentIdとrenderPacketをPHASE 1で確定してください。各Render Packetにはsingle-frame contract（singleFrameOnly / forbidCollage / forbidPanels / forbidGrid / forbidContactSheet / forbidMontage / forbidInsetImages、Hero/SceneはsingleSceneOnly）を必須で設定してください。実際の画像生成ターンでは現在の1 target以外を言及せず、「8景」「4画像」「batch」「series」「collection」等の複数画像を想起させる文言を生成指示に含めないでください。

画像生成後のnovelty QAでは、直前画像だけではなく、そのCountryで既に生成済み・承認済みのHero / Scene / Tasteの該当グループ全体と比較してください。同一画像、実質的なrestage、wrong-target carryoverは自動NGとし、ユーザーに判定を求めないでください。コラージュ、同一画像の繰り返し、wrong-target carryoverのいずれかが1度でも出た場合はgenerationContextをCONTAMINATEDにし、そのターンの画像生成を停止してください。次のアクションはRESET_GENERATION_CONTEXTとし、resetのターンでは画像生成を行わないでください。

画像生成前に必ず対象assetをGENERATINGとして予約し、generationReservationをworking branchへ保存してから生成してください。画像生成後は次の生成前にRECONCILE_GENERATIONを実行し、candidateVisualQaで対象一致・既存全画像との非重複・コラージュ/文字混入を確認してください。同一assetを同じassistant turnで2回生成することは禁止です。前画像を参照・編集元に使わず、毎回fresh independent text-to-imageとして生成してください。SCENES_INITIAL / TASTE_INITIAL中の個別APPROVEDは禁止です。

ユーザー承認前に atlasPublished:true へ変更しないでください。

最終ページ確認でユーザーが公開を承認したら、承認記録だけのState PRを作らず、そのまま1本の正式公開PRでStateを COMPLETE / CI_GATED にしてください。公開後のCloudflare Production検証結果を書き戻すためだけの追加PRも作成しないでください。
```

## Authority order

When instructions appear to conflict, use this order for Country production operations:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/image-generation-policy.json` on `main` for all Hero / Scene / Taste generation rules
3. authoritative `ops/country-production/{slug}.json` resolved by `stateRef` for operational progress (working branch during production, main from REVIEW onward)
4. `docs/COUNTRY_PRODUCTION_STATE.md` for sequencing / approval / throughput rules
5. `docs/SCENE_IMAGE_PRODUCTION.md` for Hero / Scene image generation
6. `docs/TASTE_IMAGE_PRODUCTION.md` for Taste image production
7. other global design / implementation specifications
8. Country Content Plan for editorial and visual-design intent only
9. chat history

A Content Plan must never override current Production State.

## Normal user interaction

Normal flow:

```text
start
→ Hero review
→ 8-Scene batch review
→ 4-Taste batch review
→ canonical Country URL review
→ explicit publish approval
```

No per-Scene or per-Food approval gate is created by the rule that each image is generated independently. The current main policy additionally requires pre-generation reservation, mandatory reconciliation before any next generation, candidate visual novelty QA against all prior relevant Country assets, and a perceptual duplicate gate before the review package proceeds.

A successful Scene or Taste generation is an internal production checkpoint, not a user interaction checkpoint. While sequential image tool calls are available, the assistant must continue to the batch boundary without voluntarily returning control.

## Post-visual rule

After Hero + S01–S08 + FOOD01–FOOD04 are approved, continue automatically through:

```text
approved asset materialization
→ asset QA
→ Map build / QA
→ Country JSON / taxonomy implementation
→ validation
→ one Review Package integration
→ Review Deployment
→ targeted Desktop / Tablet / Mobile production QA
→ canonical URL presentation
```

Do not create intermediate State / publish / QA / fix branches for normal Country production. Keep one Country working branch until review integration. Per-image State updates are direct commits to that working branch, not PRs. After explicit publication approval, use one terminal publication PR and do not create a post-production State normalization PR.
