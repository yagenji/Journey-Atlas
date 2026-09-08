# JOURNEY ATLAS — NEW COUNTRY START

Updated: 2026-09-08

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
- チャット履歴ではなくProduction Stateを正本として、PHASE / NEXT ACTION / NEXT ASSETから再開してください。

Production Stateが存在しない場合：
- Registry / Country JSON / assets / branchの実状態を確認し、新規CountryのProduction Stateをmainに初期化してください。

制作進行・承認ゲート・Batch処理・QA・Review Deployment・Publishは docs/COUNTRY_PRODUCTION_STATE.md に従ってください。
Taste画像は docs/TASTE_IMAGE_PRODUCTION.md に従ってください。

Content Planは何を作るかだけを保持し、PHASE / NEXT IMAGE / APPROVED状態 / generation cursor / failure logを持たせないでください。

通常のユーザー承認はHero、8景Batch、Taste Batch、Canonical URL最終確認のみとし、それ以外はBlocking Issueがない限り自動進行してください。

ユーザー承認前に atlasPublished:true へ変更しないでください。
```

## Authority order

When instructions appear to conflict, use this order for Country production operations:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production/{slug}.json` on `main` for current operational state
3. `docs/COUNTRY_PRODUCTION_STATE.md` for sequencing / approval / throughput rules
4. `docs/TASTE_IMAGE_PRODUCTION.md` for Taste image production
5. other global design / implementation specifications
6. Country Content Plan for editorial and visual-design intent only
7. chat history

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

No per-Scene or per-Food approval gate is created by the rule that each image is generated independently.

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

Do not create intermediate publish / QA / fix branches for normal Country production. Keep one Country working branch until review integration.
