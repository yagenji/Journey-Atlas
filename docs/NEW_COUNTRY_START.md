# JOURNEY ATLAS — NEW COUNTRY START

Updated: 2026-09-15
Current new-Country protocol: 2.0 / policy patch 5
Current image policy: Revision 7 / Patch 2 / policyId 7.2
Current content policy: Content QA v6
Current publication path: Publication Pipeline v2

Hardcoded values in this document are descriptive only. Before starting or resuming a Country, read the current values from `main:ops/country-production-policy.json` and `main:ops/image-generation-policy.json`.

## Copy / paste start prompt

```text
JOURNEY ATLASの新規Country Page制作を開始します。

対象国：
【国名】

GitHub：
`yagenji/Journey-Atlas`

PROJECT MASTER INSTRUCTIONSとGitHub `main` の最新仕様を使用してください。
チャット内の古い説明より、現在の `main` を優先してください。

最初に以下を確認してください。
1. `main:ops/country-production-policy.json` の最新 protocolId / policyPatch / contentQuality.version / publicationAutomation.version
2. `main:ops/image-generation-policy.json` の最新 revision / patch / policyId
3. `main:docs/COUNTRY_PRODUCTION_PROTOCOL_2.md`
4. `main:docs/CONTENT_QUALITY_RULES_V6.md` と `main:docs/MAP_SYSTEM.md`
5. `ops/country-production/{slug}.json` と `stateRef` / `contentRef` / `publicationPipelineVersion`

新規CountryでStateが存在しない場合は、`country/{slug}` branchを作成し、現在のProtocol 2 initializerを使用してください。
`python3 scripts/country_production_protocol_v2.py init {slug}`

既存Stateがある場合はゼロから作り直さず、authoritative Stateから再開してください。
既存in-flight Countryは自動的にContent QA v6 / Publication Pipeline v2へ移行させないでください。明示的なmigrationがない限り既存contractを維持してください。

以後、進行判断にはProtocol 2のNEXTを使用してください。
`python3 scripts/country_production_protocol_v2.py next {slug}`

NEXTが返す `interaction.userGate` を承認要否の正本としてください。
- `userGate:false` の時にユーザーへ approve / 進めて / 生成 / next を要求してはいけません。
- Scene / Tasteの途中画像は承認ゲートではありません。
- runtime / tool / turn boundaryを承認ゲートへ変換してはいけません。
- 成功したtool actionの後に実行可能なnon-gate NEXT ACTIONが残っているなら、statusだけで停止せず次の本当のgateまで進めてください。

【Hero前に必ず完了すること】
`docs/COUNTRY_PRODUCTION_PROTOCOL_2.md` のPre-visual buildを完了してください。
Hero生成前に画像以外のCountry Pageをほぼ完成させます。
- Country JSON本文
- S01〜S08の選定・実座標・最終画像パス
- FOOD01〜04の選定・最終画像パス
- Map制作・QA
- taxonomy
- NEXT DESTINATIONS / Related Countries
- NEXT ROUTES
- Travel Scale
- Signature Facts
- ENCOUNTERS
- Beyond the Scenery / Travel Trivia
- Taste heading
- sources / sourceDates
- current Content QA

以下2つがPASSし、MapがAPPROVEDになるまでHeroへ進まないでください。
`python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json`
`python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json`

`validate_country_quality_v5.py` というfilenameは互換性のため残されています。`contentQaVersion` に応じてv5/v6をrouteします。

【Content QA v6】
新規Countryは `contentQaVersion: 6` を使用してください。
v6の詳細は `docs/CONTENT_QUALITY_RULES_V6.md` を正本とし、ここでは最低限のproduction gateだけ確認します。

- Signature Facts / Beyond the Scenery / Travel Triviaで同じcanonical subjectを使い回さない。
- Signature Factsは、その数字が国の見え方を変える3件だけを選び、`interestReason` を持たせる。
- 一般的な人口・面積・人口密度は例外的scaleで `exceptionalScale:true` の場合だけ候補にする。
- World Heritage件数・forest shareはcurrent policyのexception thresholdを満たす場合だけ候補にする。
- NEXT ROUTESは「代表的なtraveler routeか」と「現在のborder/service status」を分離する。temporary restrictionだけでrouteを削除しない。
- NEXT DESTINATIONSは近さではなくaffinityで選び、`affinityType` を持たせる。
- ENCOUNTERSは旅行者が広く直接観察できる体験とし、最低4categoryへ分散する。
- Taste headingはCountry名から固定生成し、Countryごとの創作見出しを作らない。
- Mapは首都ラベルとScene番号のcollisionだけでなくv6 safety marginも満たす。実緯度経度をlayout調整目的で変更しない。
- Pre-visual gate通過後はblocking defectまたはユーザーの明示修正がない限り、画像承認後に本文選定をやり直さない。

Travel Scale等の継承ルールを含む詳細条件は `docs/CONTENT_QUALITY_RULES_V6.md` とmachine policyを直接参照してください。

【画像生成】
画像生成は現在のmain image policyに従ってください。
- 1生成 = 1画像 = 1Target
- fresh independent text-to-image
- collage / grid / panel / montage / text禁止
- previous imageをreference/edit元にしない
- wrong-target / repeat / restageは自動Reject
- contamination時はRESET
- `PREVIOUS_ASSET_REPEAT` / `WRONG_TARGET_CARRYOVER` は1回目からRender Packet / prompt familyをrefreshし、同じpromptSeriesで再試行しない

Heroは1枚生成後に1回承認を求めます。
Hero承認後はS01〜S08を独立生成し、途中承認なしでScene Batch boundaryまで進めます。
Scene Batch承認後はFOOD01〜FOOD04を独立生成し、途中承認なしでTaste Batch boundaryまで進めます。

TASTE_INITIALで失敗Targetがあっても、その場で再生成せず `REGENERATE` にparkして未生成Targetを先に一巡してください。
全4Targetのfirst pass後に1回だけTaste Batch Reviewを行い、NG確定TargetだけをTASTE_REGENへ進めます。
REGENも対象画像を独立生成した後にBatch Reviewを行います。

【画像の格納方法】
画像格納は `USER_HANDOFF` に一本化します。
Assistant側で生成画像をGitHubへ復元・格納しようとしないでください。
Hero + 8 Scenes + 4 Tasteがすべて承認されたら、13枚を一度にユーザーへ渡し、generation ID / 内容 / 最終格納パスをまとめたmanifestを提示してください。
ユーザーが13枚を格納した後、Repository上の13画像を一度だけBatch verificationしてください。
画像handoffは承認ゲートではありません。

【Publication Pipeline v2】
新規Country scaffoldでは `publicationPipelineVersion: 2` を使用します。
13画像handoffがPASSした後は、通常のCountry-only pathを自動で進めてください。

Review path：
1. target Countryだけをstrict validation / image auditする
2. `publication-pipeline-v2-review.yml` がreusable PRを1本だけ確保する
3. `publication-pipeline-v2-checks.yml` がtargeted Desktop / Tablet / Mobile Browser QAを実行する
4. Review sourceは **latest main + target Country overlay** から構築する
5. `/reviews/{slug}/countries/{slug}/` へpersistent reviewをdeployする
6. review結果をauthoritative Stateへreconcileする
7. canonical review URLをユーザーへ提示し、最終ページ承認を求める

Review準備のためにlatest `main`を長期Country branchへmergeしないでください。
Country固有差分はCountry branch overlayを正本とし、shared runtimeはlatest `main`を使用します。
Country PRにshared UI/build/workflow変更を混ぜないでください。共通修正が必要なら別system PRにしてください。

Final approval後：
1. `finalApproval.state: APPROVED` を記録する
2. `publication-pipeline-v2-finalize.yml` に任せる
3. workflowがlatest `main`を取得し、target Country overlayを再構築する
4. terminal publication State / `atlasPublished:true` を準備する
5. exact terminal SHAでpublish checksを実行する
6. 同じreusable PRをsquash mergeする
7. Cloudflare上のmerge SHAを確認し、target Country route / JSONをinline smoke testする

以下は禁止です。
- final canonical review前のmain統合
- latest mainを長期Country branchへ直接mergeするv2運用
- Review用PRとは別のPublication PR
- Pipeline v2 publish後の別production-verification PR
- Country-only変更での全Country Browser QA / full build
- 実行可能なnon-gate NEXT ACTIONがある状態での進行確認待ち

通常のユーザー承認ゲートは以下のみです。
1. Hero
2. 8-Scene Batch
3. 4-Taste Batch
4. Final Country Page / Publish

私が「進めて」と指示した場合は、その時点のProtocol 2 NEXTを実行し、次の明示gateまで自動継続してください。
```

## Repository authority

For a Protocol 2 new Country, use this order:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production-policy.json`
3. `ops/image-generation-policy.json`
4. `docs/COUNTRY_PRODUCTION_PROTOCOL_2.md`
5. current image-policy revision docs
6. authoritative Country Production State
7. `docs/CONTENT_QUALITY_RULES_V6.md` for new `contentQaVersion: 6`; prior specs for legacy versions
8. `docs/PUBLICATION_PIPELINE_V2.md`
9. `docs/MAP_SYSTEM.md`
10. Scene / Taste / Map / Country template specifications
11. chat history

The start prompt intentionally avoids duplicating every detailed rule. Machine policy and current repository documents remain authoritative so the prompt does not drift when QA or publication automation changes.
