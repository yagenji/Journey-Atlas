# JOURNEY ATLAS — NEW COUNTRY START

Updated: 2026-09-09

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

最初に ops/country-production/{slug}.json をmainから確認してください。

Production Stateが存在する場合：
- stateRef / contentRef が country/{slug} を指していれば、そのbranchのProduction Stateを再取得し、そちらを正本としてPHASE / NEXT ACTION / NEXT ASSETから再開してください。
- stateRef が main ならmainを正本としてください。

mainにProduction Stateが存在しない場合：
- country/{slug} branchを確認し、そこにStateがあればそのStateを正本としてください。
- 完全な新規Countryならcountry/{slug} branchを先に作成し、revision 4 Stateをそのbranchに初期化してください。
- active production中のState更新のためにmain PRを作成しないでください。
- 手作業で古いrevision 2 / 3 Stateを複製しないでください。

制作進行・承認ゲート・Batch処理・QA・Review Deployment・Publishは docs/COUNTRY_PRODUCTION_STATE.md に従ってください。
Scene / Hero画像は docs/SCENE_IMAGE_PRODUCTION.md に従ってください。
Taste画像は docs/TASTE_IMAGE_PRODUCTION.md に従ってください。

Content Planは何を作るかだけを保持し、PHASE / NEXT IMAGE / APPROVED状態 / generation cursor / failure logを持たせないでください。

通常のユーザー承認はHero、8景Batch、Taste Batch、Canonical URL最終確認のみとし、それ以外はBlocking Issueがない限り自動進行してください。

新規Stateは imageGenerationPolicy revision 4 を使用し、Hero / Scene / Tasteの全生成対象にcontentIdとrenderPacketをPHASE 1で確定してください。生成直後はcandidateVisualQaで前画像重複・対象一致・コラージュ/文字混入を確認し、SCENES_INITIAL / TASTE_INITIAL中の個別APPROVEDは禁止です。

ユーザー承認前に atlasPublished:true へ変更しないでください。

正式公開PRではrevision 4 Stateを直接 COMPLETE / CI_GATED にしてください。公開後のCloudflare Production検証結果を書き戻すためだけの追加PRは作成しないでください。
```

## Authority order

When instructions appear to conflict, use this order for Country production operations:

1. PROJECT MASTER INSTRUCTIONS
2. authoritative `ops/country-production/{slug}.json` resolved by `stateRef` (working branch during production, main from REVIEW onward)
3. `docs/COUNTRY_PRODUCTION_STATE.md` for sequencing / approval / throughput rules
4. `docs/SCENE_IMAGE_PRODUCTION.md` for Hero / Scene image generation
5. `docs/TASTE_IMAGE_PRODUCTION.md` for Taste image production
6. other global design / implementation specifications
7. Country Content Plan for editorial and visual-design intent only
8. chat history

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

No per-Scene or per-Food approval gate is created by the rule that each image is generated independently. Revision 4 additionally requires candidate visual novelty QA after each generation and a perceptual duplicate gate before the review package proceeds.

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
