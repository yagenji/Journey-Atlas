# JOURNEY ATLAS — NEW COUNTRY START

Updated: 2026-09-11
Current new-Country protocol: 2.0

## Copy / paste start prompt

```text
JOURNEY ATLASの新規Country Page制作を開始します。

対象国：
【国名】

GitHub：
`yagenji/Journey-Atlas`

PROJECT MASTER INSTRUCTIONSとGitHub `main` の最新仕様を使用してください。

最初に以下を確認してください。
1. `main:ops/country-production-policy.json` の最新 protocolId
2. `main:ops/image-generation-policy.json` の最新 revision / patch / policyId
3. `ops/country-production/{slug}.json` と `stateRef` / `contentRef`

新規CountryでStateが存在しない場合は、`country/{slug}` branchを作成し、現在のProtocol 2 initializerを使用してください。
`python3 scripts/country_production_protocol_v2.py init {slug}`

既存Stateがある場合はゼロから作り直さず、authoritative Stateから再開してください。

以後、進行判断にはProtocol 2のNEXTを使用してください。
`python3 scripts/country_production_protocol_v2.py next {slug}`

NEXTが返す `interaction.userGate` を承認要否の正本としてください。
- `userGate:false` の時にユーザーへ approve / 進めて / 生成 / next を要求してはいけません。
- Scene / Tasteの途中画像は承認ゲートではありません。
- 画像ランタイムやカード表示によってturnが区切られても、それを承認ゲートへ変換してはいけません。次のユーザーメッセージでは前画像の承認を求めず、reconcileして同じroundをBatch boundaryまで継続してください。

【Hero前に必ず完了すること】
`docs/COUNTRY_PRODUCTION_PROTOCOL_2.md` のPre-visual buildを完了してください。
Hero生成前に、画像以外のCountry Pageをほぼ完成させます。
- Country JSON本文
- S01〜S08の選定・座標・最終画像パス
- FOOD01〜04の選定・最終画像パス
- Map制作・QA
- taxonomy
- Related Countries
- Next Routes
- Travel Scale
- Signature Facts
- sources / sourceDates
- Content QA v2

`python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json` がPASSし、MapがAPPROVEDになるまでHeroへ進まないでください。

【Content QA v2】
- Travel Scaleは3段階すべてに具体的な `例：` を必須とします。
- 森林・樹林地の割合は通常のSignature Factに使用しません。
- 森林率を使えるのは国の極端な特徴である場合だけです。機械基準は10%以下または70%以上かつ `exceptionalShare:true` です。
- 数字が取得できること自体を採用理由にしないでください。

【画像生成】
画像生成の安全ルールは現在のmain image policyに従ってください。
- 1生成 = 1画像 = 1Target
- fresh independent text-to-image
- collage / grid / panel / montage / text禁止
- previous imageをreference/edit元にしない
- wrong-target / repeat / restageは自動Reject
- contamination時はRESET

Heroは1枚生成後に1回承認を求めます。

Hero承認後、SCENES_INITIALを自動開始してください。
S01〜S08を8つの独立生成callとしてBatch boundaryまで進めます。
正常なSceneの途中でユーザー承認を求めてはいけません。
8景が揃ってから1回だけScene Batch Reviewを求めます。

Scene Batch承認後、Taste roundを自動開始してください。
FOOD01〜FOOD04を4つの独立生成callとしてBatch boundaryまで進めます。
料理の途中でユーザー承認を求めてはいけません。
4枚が揃ってから1回だけTaste Batch Reviewを求めます。

REGENも同じです。対象画像をすべて独立生成した後に1回のREGEN Batch Reviewを行い、1枚ごとの承認は禁止です。

【画像の格納方法】
画像格納は `USER_HANDOFF` に一本化します。
Assistant側で生成画像をGitHubへ復元・格納しようとしないでください。
Hero + 8 Scenes + 4 Tasteがすべて承認されたら、13枚を一度にユーザーへ渡し、generation ID / 内容 / 最終格納パスをまとめたmanifestを提示してください。
ユーザーが13枚を格納し「格納した」と伝えた後、Repository上の13画像を一度だけBatch verificationしてください。
これは承認ゲートではなく作業上のhandoffです。

【画像後工程】
画像承認後にMapや本文を作り始めてはいけません。Pre-visual buildで完成済みであることが前提です。
ユーザーの画像格納後は原則として以下だけを1本で実行してください。
1. 13画像Batch verification
2. 必要な一括変換・dimensions/path/hygiene QA
3. Country JSONとのpath一致確認
4. strict validation
5. Review Packageを1回だけmainへ統合
6. targeted Desktop / Tablet / Mobile Browser QAを1回
7. canonical URL提示

Blocking defectがない限り、途中で進行確認を求めたり、複数のReview integration / Browser QA cycleを作らないでください。

通常のユーザー承認ゲートは以下のみです。
1. Hero
2. 8-Scene Batch
3. 4-Taste Batch
4. Canonical Country Page / Publish

画像handoffは承認ゲートではありません。

私が「進めて」と指示した場合は、その時点のProtocol 2 NEXTを実行してください。
```

## Repository authority

For a Protocol 2 new Country, use this order:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production-policy.json`
3. `ops/image-generation-policy.json`
4. `docs/COUNTRY_PRODUCTION_PROTOCOL_2.md`
5. current image-policy revision docs
6. authoritative Country Production State
7. `docs/CONTENT_QUALITY_RULES_V2.md`
8. Scene / Taste / Map / Country template specifications
9. chat history

The start prompt intentionally stays compact. Detailed rules live in the repository and must not be duplicated into an ever-growing per-Country prompt.
