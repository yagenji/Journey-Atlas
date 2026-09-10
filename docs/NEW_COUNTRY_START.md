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

最初に main の `ops/image-generation-policy.json` を確認し、画像生成ルールの最新revision / patch / policyIdを確定してください。
- Revision 7では `docs/IMAGE_POLICY_REVISION_7.md` と `scripts/country_production_state_v7.py` を使用してください。
- policyId 7.1以降では、さらに `docs/IMAGE_POLICY_REVISION_7_1.md` のthroughput rulesを使用してください。
その後、`ops/country-production/{slug}.json` を確認してください。

Production Stateが存在する場合：
- stateRef / contentRef が country/{slug} を指していれば、そのbranchのProduction Stateを正本としてPHASE / NEXT ACTION / NEXT ASSETから再開してください。
- stateRef が main ならmainを正本としてください。
- active image phaseのStateがmain中央Policyより古い場合は、次の画像生成前に最新revisionへ移行してください。古いStateを理由に中央Policyを巻き戻してはいけません。

mainにProduction Stateが存在しない場合：
- country/{slug} branchを確認し、そこにStateがあればそのStateを正本としてください。
- 完全な新規Countryならcountry/{slug} branchを先に作成し、Revision 7 Stateを初期化してください。CLIを使う場合は `python3 scripts/country_production_state_v7.py init {slug}` を使用してください。
- active production中のState更新のためにmain PRを作成しないでください。
- 手作業で古いrevision Stateを複製しないでください。

制作進行・承認ゲート・Batch処理・QA・Review Deployment・Publishは docs/COUNTRY_PRODUCTION_STATE.md に従ってください。
Revision 7の画像実行・承認由来・REGENルールは docs/IMAGE_POLICY_REVISION_7.md に従ってください。
Revision 7.1のState read/write最適化・atomic handoff・軽量CIルールは docs/IMAGE_POLICY_REVISION_7_1.md に従ってください。
Scene / Hero画像は docs/SCENE_IMAGE_PRODUCTION.md に従ってください。
Taste画像は docs/TASTE_IMAGE_PRODUCTION.md に従ってください。

【Country region 表記の絶対ルール】
- Country JSON の `region` は `data/region-taxonomy.json` をSingle Source of Truthとし、destination registryの `iso2` が所属するsubregionの `labelEn` をそのまま使用してください。subregionがない地域はtop-level `labelEn` を使用してください。
- 表記形式は必ず `{TAXONOMY LABEL} / {整数緯度}°N|S` とします。例：`EAST ASIA / 35°N`、`SOUTHERN EUROPE / 42°N`。
- `CENTRAL EUROPE`、`SOUTHEASTERN EUROPE`、`BALTIC SEA`、`NORTH ATLANTIC` のようなCountry独自分類や、`ATLANTIC`、`BLACK SEA`、`NORTHERN ASIA` 等の緯度以外のsuffixを追加してはいけません。
- `scripts/new_country.py` で新規scaffoldを作る場合、taxonomy labelは自動で固定されます。Map bounds確定後に `python3 scripts/normalize_country_region_labels.py` を実行して代表緯度を付与し、`python3 scripts/audit_country_region_labels.py` を通してください。
- 代表緯度は既存の妥当な整数緯度を維持し、未設定の場合はCountry map boundsの南北中央を整数丸めして決定します。推測で別の緯度を足さないでください。
- Region auditがPASSするまでReview Package / Review Deploymentへ進んではいけません。

Content Planは何を作るかだけを保持し、PHASE / NEXT IMAGE / APPROVED状態 / generation cursor / failure logを持たせないでください。

通常のユーザー承認はHero、8景Batch、Taste Batch、Canonical URL最終確認のみとし、それ以外はBlocking Issueがない限り自動進行してください。REGENが必要な場合も、対象画像を連続生成した後のREGEN Batch Reviewだけを承認ゲートとし、1枚ごとの承認は禁止です。

【画像ラウンドの絶対実行ルール】
- 1画像 = 1独立生成リクエストを守ってください。複数Scene / 複数料理を1つの生成プロンプトにまとめてはいけません。
- ただし、1画像 = 1ユーザー操作ではありません。正常な画像1枚の生成完了をユーザー承認ゲートにしてはいけません。
- `maxSameAssetGenerationsPerTurn = 1` は同一Targetの重複生成防止です。異なるTargetを同一assistant turnで連続生成することを禁止するルールではありません。
- SCENES_INITIALでは、S01を生成・reconcileしたらBlocking Issueがない限りS02へ進み、同じ手順でS08まで自動継続してください。S01〜S08の途中で「approve」「進めて」「生成」等のユーザー入力を要求してはいけません。
- TASTE_INITIALでも、FOOD01を生成・reconcileしたらBlocking Issueがない限りFOOD02→FOOD03→FOOD04まで自動継続してください。FOOD01〜FOOD04の途中で個別承認を要求してはいけません。
- SCENES_REGEN / TASTE_REGENでも同じです。今回のREGEN対象をそれぞれ独立生成で連続処理し、round boundary到達後に一括承認してください。
- ユーザー承認を求めるのは、initial / regenを問わず、そのroundがbatch boundaryへ到達した時だけです。
- 画像生成ランタイムが実際にassistant turnを強制終了した場合だけ次ターンへ跨いで構いません。ただし、それは承認ゲートではありません。次にユーザー入力が来たら、前画像の承認確認をせず、reconcile後のNEXTへ直ちに自動継続してください。

【Revision 7 承認ルール】
- Scene / Tasteのユーザー承認由来は、個別assetではなく `sceneBatchReview.rounds[]` / `tasteBatchReview.rounds[]` にのみ記録してください。
- Scene / Taste assetに個別 `userApprovedAt` を記録してはいけません。
- 各Batch roundは `scope`、`approvedGenerations`、`regenerate`、`reviewBoundary:true`、`approvedAt` を記録してください。
- SCENES_REGEN / TASTE_REGEN中に既にAPPROVEDのassetが存在してよいのは、過去のBatch ledgerでそのexact `approvedGenerationId` が承認済みの場合だけです。
- 新しく再生成したcandidateは、次のBatch boundaryまでは `REVIEW_CANDIDATE` のままにしてください。個別にAPPROVEDへ変更してはいけません。
- Batch ledgerはappend-onlyです。後から個別承認をBatch承認だったことに見せかける追記・改変は禁止です。CIがcommit transition単位で検査します。

【Revision 7.1 Throughputルール】
- 新しいassistant turnの開始時はmain Policyとauthoritative Stateを読み直してください。
- 同一assistant turn内では、期待blob SHAを使ったState writeが成功した時点で「自分が書いた完全なState内容 + 返却された新しいblob SHA」を新しいauthoritative Stateとして扱ってください。同じ内容を確認するためだけの再fetchは禁止です。
- 再fetchするのは、assistant turnが変わった時、SHA conflictが起きた時、外部変更の可能性がある時、またはState内容が不確かな時だけです。
- 正常な画像をreconcileする時、次の異なるTargetがありgenerationContextがCLEANなら、`current: GENERATING → REVIEW_CANDIDATE` と `next: NOT_STARTED → GENERATING` を1回のState updateで原子的に行ってください。
- このatomic handoff後も未reconcileの`GENERATING`は常に1つだけでなければなりません。
- 現在画像がコラージュ・重複/restage・wrong-target carryover等でgenerationContextを汚染した場合は次Targetを同時予約せず、RESETへ進んでください。
- SCENES_INITIAL開始時にS01〜S08のRender Packetを一度まとめてpreflightし、同一turn内でContent Planを画像ごとに再読込しないでください。TasteもFOOD01〜04をround開始時に同様にpreflightしてください。
- 同一turn内のall-prior novelty QAでは、既に現在の生成contextにある過去画像をincremental comparison setとして再利用し、同じ画像をGitHubから毎回取り直さないでください。
- country/{slug}へのper-image State commit後、次の画像へ進むためにCI完了を待ってはいけません。State write成功を継続条件とし、country branch CIは非同期のtransition guardとして扱ってください。
- lower-priority文書に「自分の成功したState write直後にも必ず再fetch」とある場合、policyId 7.1ではこのsectionが優先します。

新規Stateには `imageGenerationPolicyRef: "main:ops/image-generation-policy.json"` を設定し、mainのRevision 7を使用してください。Country branch側の古いpolicy snapshotでmainのpolicyを上書き・巻き戻ししないでください。Hero / Scene / Tasteの全生成対象にcontentIdとrenderPacketをPHASE 1で確定してください。各Render Packetにはsingle-frame contract（singleFrameOnly / forbidCollage / forbidPanels / forbidGrid / forbidContactSheet / forbidMontage / forbidInsetImages、Hero/SceneはsingleSceneOnly）を必須で設定してください。実際の画像生成ターンでは現在の1 target以外を言及せず、「8景」「4画像」「batch」「series」「collection」等の複数画像を想起させる文言を生成指示に含めないでください。

画像生成前のreservationは、exact asset id / exact contentId / current generationContext.epoch / current NEXTと一致させてください。生成結果はその予約Targetに対してのみreconcileしてください。

画像生成後のnovelty QAでは、直前画像だけではなく、そのCountryで既に生成済み・承認済みのHero / Scene / Tasteの該当グループ全体と比較してください。同一画像、実質的なrestage、wrong-target carryoverは自動NGとし、ユーザーに判定を求めないでください。コラージュ、同一画像の繰り返し、wrong-target carryoverのいずれかが1度でも出た場合はgenerationContextをCONTAMINATEDにし、そのターンの画像生成を停止してください。次のアクションはRESET_GENERATION_CONTEXTとし、resetのターンでは画像生成を行わないでください。

画像生成前に必ず対象assetをGENERATINGとして予約し、generationReservationをworking branchへ保存してから生成してください。画像生成後は次の生成前にRECONCILE_GENERATIONを実行し、candidateVisualQaで対象一致・既存全画像との非重複・コラージュ/文字混入を確認してください。同一assetを同じassistant turnで2回生成することは禁止です。前画像を参照・編集元に使わず、毎回fresh independent text-to-imageとして生成してください。

ユーザー承認前に atlasPublished:true へ変更しないでください。

最終ページ確認でユーザーが公開を承認したら、承認記録だけのState PRを作らず、そのまま1本の正式公開PRでStateを COMPLETE / CI_GATED にしてください。公開後のCloudflare Production検証結果を書き戻すためだけの追加PRも作成しないでください。
```

## Authority order

When instructions appear to conflict, use this order for Country production operations:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/image-generation-policy.json` on `main` for all Hero / Scene / Taste generation rules
3. `docs/IMAGE_POLICY_REVISION_7_1.md` when main policyId is 7.1 or later, for State I/O / atomic handoff / CI throughput rules
4. `docs/IMAGE_POLICY_REVISION_7.md` for revision-7 execution / batch provenance / REGEN rules
5. authoritative `ops/country-production/{slug}.json` resolved by `stateRef` for operational progress (working branch during production, main from REVIEW onward)
6. `docs/COUNTRY_PRODUCTION_STATE.md` for sequencing / approval rules not superseded by Revision 7/7.1
7. `docs/SCENE_IMAGE_PRODUCTION.md` for Hero / Scene image generation
8. `docs/TASTE_IMAGE_PRODUCTION.md` for Taste image production
9. other global design / implementation specifications
10. Country Content Plan for editorial and visual-design intent only
11. chat history

A Content Plan must never override current Production State or the central image-generation policy.

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

No per-Scene or per-Food approval gate is created by the rule that each image is generated independently. Revision 7 requires different-target continuation after each successful reconcile, batch-only approval provenance in initial and regeneration rounds, target reservation synchronization, all-prior novelty QA, and commit-transition validation against late Batch backfill.

Revision 7.1 additionally requires same-turn authoritative State chaining, atomic reconcile/reserve-next handoff, round-start Render Packet preflight, incremental visual comparison reuse, and non-blocking country-branch CI.

A successful Scene or Taste generation is an internal production checkpoint, not a user interaction checkpoint. While sequential image tool calls return control, the assistant must continue to the batch boundary without voluntarily returning control.

## Post-visual rule

After Hero + S01–S08 + FOOD01–FOOD04 are approved, continue automatically through:

```text
approved asset materialization
→ asset QA
→ Map build / QA
→ Country JSON / taxonomy implementation
→ region normalization / audit
→ validation
→ one Review Package integration
→ Review Deployment
→ targeted Desktop / Tablet / Mobile production QA
→ canonical URL presentation
```

Do not create intermediate State / publish / QA / fix branches for normal Country production. Keep one Country working branch until review integration. Per-image State updates are direct commits to that working branch, not PRs. After explicit publication approval, use one terminal publication PR and do not create a post-production State normalization PR.
