> **STATUS — COMPLETED (2026-09-05)**  
> This file is retained as a historical execution/plan record. The current authoritative renewal status is `data/country-renewal-status.json`: content / visual / map / sources = `DONE`, QA = `PASS`, production = `LIVE_CURRENT`. Any `PENDING`, `Still pending`, or pre-publish notes below describe an earlier checkpoint and are not current tasks.

# Monaco Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/monaco-renewal`

This document is the locked PHASE 2 content design for the Monaco Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Port Hercule from Le Rocher / Monaco-Ville
- Current eight scene locations and scene copy
- Map geometry / markers / labels unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Signature Facts: keep all three current topics
- Travel Trivia: keep all five current topics, with one wording normalization noted below
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Travel Notes: keep all three current topics, with source refresh
- Related Destinations: France / Italy / San Marino
- Theme taxonomy assignment: 街を歩く only

## Signature Facts — KEEP 3

The current three facts already cover three distinct and useful topics: compact geography / land creation / resident composition.

1. **国土の最大幅 — 1,140 m**
   - KEEP.
   - Shows the physical scale of the Principality directly.

2. **マレテラで増えた土地 — 6 ha**
   - KEEP.
   - Shows how urban development can physically change the territory of a microstate.

3. **居住者に占めるモネガスク — 23.9%**
   - KEEP.
   - Shows that nationality and residence are not the same thing in Monaco.

Do not replace these with generic highest-point, World Heritage or population-density facts.

## Encounters — LOCKED 8

The current list is structurally valid but too close to the eight-scene index. Replace it with a broader mix of geography, urban form and culture.

1. 地中海
2. 急斜面の街
3. ベル・エポック
4. マリーナ
5. 海洋文化
6. 公道サーキット
7. 庭園
8. モネガスク文化

These remain short encounter tags and are not expanded into explanatory copy.

## Beyond the Scenery — LOCKED 6

Keep five current cards. Replace the FOOD card so Beyond does not duplicate the new Taste section.

### 1. HISTORY — KEEP
**1297年、修道士に変装してル・ロシェを奪った**

Keep current copy and points.

### 2. SCIENCE — KEEP
**アルベール1世は28回の海洋調査航海を行った**

Keep current copy and points.

### 3. ROAD — KEEP
**3.337kmの公道がレースコースに変わる**

Keep current copy and points.

### 4. CULTURE — KEEP
**守護聖人の日には港で小舟を燃やす**

Keep current copy and points.

### 5. CULTURE / 暮らしに出会う — REPLACE FOOD
**赤と白の衣装で踊る、ラ・パラディエンヌ**

ラ・パラディエンヌ・ド・モナコは、マンドリンやギターなどの演奏と伝統舞踊を組み合わせる民俗グループ。地域行事や文化行事で伝統衣装と音楽が現れ、宮殿やカジノだけでは見えないモナコの文化継承に触れられる。

Points:
- 伝統舞踊と弦楽器の演奏を組み合わせる
- モナコの文化行事で現在も披露されている

Source: VisitMonaco / Monaco cultural heritage material, including La Palladienne de Monaco.

### 6. SEA — KEEP
**海水浴場の沖にはポシドニアの保護区がある**

Keep current copy and points.

## Travel Trivia — KEEP 5 / one normalization

Keep all five topics:

1. モンテカルロの名はシャルル3世公に由来する
2. モネガスク国民は国内の賭博場で賭けられない
3. モネガスク語は学校とコンテストで受け継がれている
4. モナコとインドネシアの国旗はよく似ている
5. ASモナコはフランスのリーグ・アンで戦う

For item 5, remove wording that unnecessarily ties the card to a single season. Use evergreen current wording:

`モナコは独立した主権国家だが、ASモナコはフランスのプロリーグ体系に参加している。国境とサッカーのリーグ境界が一致しない、小国ならではの関係が見える。`

Current-season source should still be checked during implementation, but the visible copy should not become stale every year.

## Taste — LOCKED

Kicker: `TASTE OF MONACO`  
Title: `モナコで食べたいもの`

Intro:

`旧市街の郷土料理から、海の保存食、リヴィエラの粉食、祝い菓子まで、モナコの日常側を4品からたどる。`

The selection deliberately avoids making luxury restaurants the centre of Monaco's food identity. The four items show the local Riviera / Monegasque food tradition that a traveller can actually encounter.

### FOOD01 — バルバジュアン / Barbagiuàn

**Copy**

フダンソウなどの青菜を詰めた生地を揚げる、モナコを代表する小さな包み料理。フランスとリグーリアの間にある土地らしい食文化を、気軽な一品から感じられる。

Planned asset: `food-barbajuan.webp`

**DISH IDENTITY**
- 小ぶりの揚げた包み料理
- 半月〜小さなラビオリ状
- 表面は自然なきつね色
- 中身はフダンソウなどの青菜が中心
- 甘い菓子ではない
- ピザ、パン、揚げ餃子風に誇張しない

Source: VisitMonaco / Monaco Now official communication material / France.fr.

### FOOD02 — ストカフィ / Stocafi

**Copy**

乾燥させたタラを戻して煮込む、モナコの海辺の食文化を伝える料理。保存できる魚とオリーブオイル、香味野菜を使う一皿に、地中海と交易の歴史が重なる。

Planned asset: `food-stocafi.webp`

**DISH IDENTITY**
- 乾燥タラを戻した煮込み
- 魚の身が大きめに見える
- オリーブオイル、玉ねぎ、にんにく、黒オリーブを使う伝統的方向性
- 赤茶〜トマト系の煮汁は自然な範囲
- 魚介スープやブイヤベースではない
- パスタや米料理ではない

Source: VisitMonaco / Monaco Now official communication material / France.fr.

### FOOD03 — ソッカ / Socca

**Copy**

ひよこ豆の粉とオリーブオイルで焼く薄い生地。ニースを中心とするリヴィエラの料理だが、モナコでも身近に食べられ、国境を越えて続く海岸の食文化を感じられる。

Planned asset: `food-socca.webp`

**DISH IDENTITY**
- ひよこ豆粉の薄い焼きもの
- 大きな円形から切り分けた自然な形
- 黄金色で縁や表面に軽い焼き目
- 薄く、厚いパンではない
- チーズやトマトソースを載せない
- ピザ、クレープ、オムレツに見せない

Source: VisitMonaco La Condamine / France.fr Côte d'Azur culinary guidance.

### FOOD04 — モナコ風フガス / Fougasse monégasque

**Copy**

オレンジの花の香りをつけ、アーモンドやアニスを添えるモナコの甘いフガス。南フランスで見かける塩味の葉形パンとは異なり、祝いの場にも結びつく土地固有の菓子として受け継がれている。

Planned asset: `food-fougasse-monegasque.webp`

**DISH IDENTITY**
- 甘いモナコ式フガス
- 小ぶりで平たい焼き菓子／甘いパン
- 自然な黄金色
- オレンジ blossom / citrus の菓子としての方向性
- アーモンドとアニスが料理自体の一部
- 一般的な塩味の葉形 fougasse ではない
- ハーブ、オリーブ、チーズを載せない

Source: VisitMonaco practical information / Monaco Now official communication material / France.fr.

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Barbagiuàn
- FOOD02 — NOT STARTED / Stocafi
- FOOD03 — NOT STARTED / Socca
- FOOD04 — NOT STARTED / Fougasse monégasque

Do not add these planned image paths to the production Country JSON until all four images are user APPROVED and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

Monaco is a microstate. The global duration format remains unchanged, but forcing an eight-day itinerary entirely inside 2.084 km² would be artificial. For 5–7 days and 8+ days, the itinerary explicitly uses Monaco as the base and extends along the immediately connected Riviera. This is intentional and must remain clear in the copy.

### 3〜4日 / city
**国土を地区ごとに分けて歩く**

ル・ロシェ、ラ・コンダミーヌ、モンテカルロ、ラルヴォット、フォンヴィエイユを分けて歩くと、小さな国でも高低差と地区の役割の違いが見えてくる。例：モナコ＝ヴィル → ラ・コンダミーヌ → モンテカルロ → ラルヴォット → フォンヴィエイユ。

### 5〜7日 / map
**モナコを拠点に近隣の海岸都市へ**

モナコを数日歩いた後、TERや地域バスで国境の外へ日帰りすると、同じ海岸線の中で街の性格を比べられる。例：モナコ＋エズ＋マントン＋ニース。

### 8日以上 / compass
**コート・ダジュールからリグーリアまでつなぐ**

モナコだけで日数を埋めるのではなく、鉄道でフランスとイタリアの海岸都市へ広げると、この小国が地中海沿岸のどこに位置するかが分かる。例：ニース → エズ → モナコ → マントン → ヴェンティミリア／サンレモ。

Sources:
- VisitMonaco official 72-hour itinerary / city map / surrounding access guidance
- SNCF Connect current TER service Monaco–Nice and Riviera stations
- VisitMonaco road/bus guidance for Nice / Èze / Menton connections

## Transport — LOCKED

Title: `鉄道・バス・徒歩・公共エレベーター`  
Icon: `road`

Text:

`外部からはモナコ＝モンテカルロ駅のTERが使いやすく、国内はCAMのバスと徒歩を組み合わせる。国土は小さいが高低差が大きいため、公共エレベーターやエスカレーターを使うと、港・モンテカルロ・ル・ロシェ間の移動が大きく変わる。`

Transport explains **how to move through Monaco**. Travel Scale explains **how to use a given number of days realistically**.

Current transport verification:
- CAM currently operates lines 1–6 plus night/express services.
- SNCF Connect currently shows frequent direct TER services between Monaco-Monte-Carlo and Nice.
- VisitMonaco mobility material documents public lifts, escalators and travelators as core pedestrian infrastructure.

## For Whom — KEEP EXACTLY 3

Keep current three personas:

1. 都市を地形と建築の両方から歩きたい人
2. 小国の土地利用と都市設計に興味がある人
3. 小国の日常文化まで見てみたい人

No fourth persona.

## Travel Notes — KEEP 3 / source refresh

### 1. 短い距離でも高低差を先に見る
KEEP.

### 2. 鉄道駅は出口を選んでから歩く
KEEP.

### 3. 空港はニースを玄関口にする
KEEP the topic, but update current transport provenance.

Current 2026 verification:
- Monaco has no commercial airport; Nice Côte d'Azur is the practical international gateway.
- Regular Nice–Monaco helicopter service is currently operating.
- Monacair currently states approximately 7 minutes.
- Monaco government orders published in April and August 2026 confirm authorised regular helicopter operators on the Nice–Monaco route through 31 December 2026.

Avoid presenting helicopter transfer as the default transport mode; it remains an optional connection after rail/road.

## Current 2026 temporary condition — La Condamine market

VisitMonaco states that La Condamine market is undergoing renovation with a temporary closure from January 2026 and reopening scheduled for early 2027.

Implementation rule:
- Do not write 2026 copy that implies the historic market hall is currently operating normally.
- Taste remains valid because the selected dishes are available beyond a single market venue.
- Do not turn this temporary closure into an evergreen Travel Note unless the production page is given an explicit expiry/update mechanism.

## Themes — KEEP

Keep Monaco assigned only to:

- **街を歩く / city**

Do not add:
- 食をめぐる — Taste exists, but food is not a sufficiently strong primary reason to choose Monaco over neighbouring Riviera destinations.
- 海の世界へ — the Mediterranean and marine culture matter, but the destination is not primarily chosen for marine/underwater travel.
- 時をたどる — history is present, but the page's strongest travel motivation is the compressed urban landscape, architecture and walkability.

Theme assignment remains only in `data/theme-taxonomy.json`.

## Current-standard implementation notes

After Visual Complete Gate:

- Add locked Taste section with four APPROVED image paths and `imageState: "APPROVED"`
- Add locked Spain-format Travel Scale
- Replace Encounters with the locked eight tags
- Replace Beyond FOOD / Barbajuan card with La Palladienne
- Normalize AS Monaco trivia wording so it is not season-specific
- Change Transport title to Japanese and add `"icon": "road"`
- Keep For Whom at exactly 3
- Keep Travel Notes at exactly 3
- Refresh `sourcesVerifiedAt` to 2026-09-04
- Add sourceDates for Taste / Travel Scale / Transport / current helicopter provenance / temporary Condamine closure as applicable
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS

## Source lock — verified 2026-09-04

High-trust/current sources for implementation:

- Population: Journal de Monaco, Arrêté Ministériel n° 2026-174 — official 2025 population 38,857.
- Area / width: IMSEE, Monaco en chiffres 2026 — territory 208.4 ha / maximum width 1,140 m.
- Local food:
  - VisitMonaco, local experiences / Monaco-Ville / La Condamine — Barbajuan, Stocafi, Socca, Fougasse.
  - Monaco Now / Direction de la Communication — Monegasque gastronomy, Barbajuan, stockfish, Socca, Fougasse.
  - France.fr — Monaco food and drink specialities.
- Fougasse monégasque: VisitMonaco practical information — sweet Monegasque fougasse with orange blossom, almonds and anise.
- 72-hour itinerary: VisitMonaco Media & Trade — official 72-hour itinerary.
- Current Monaco bus network: CAM — current lines 1–6, night and express routes.
- Current rail: SNCF Connect — Monaco–Nice direct TER service, current September 2026 timetable.
- Public mechanised links: VisitMonaco / Monaco mobility guidance — public lifts, escalators and travelators.
- Cross-border access: VisitMonaco road access guidance — current regional bus links via Nice / Èze / Menton.
- Helicopter route: Monacair current line information; Journal de Monaco Arrêté Ministériel n° 2026-457 of 7 August 2026.
- La Condamine renovation: VisitMonaco “Coming soon” — temporary closure from January 2026, reopening scheduled early 2027.
- La Palladienne: VisitMonaco Monaco cultural heritage / traditional dance material.

## PHASE 2 gate

Content design: **DONE / LOCKED**

Still pending:
- technical dimension / complete-decode audit for retained Hero + 8 scenes
- Taste visual production and user approval
- repository asset handoff / verification
- Visual Complete Gate
- Country JSON implementation
- latest main sync check 2
- Common CI pre-flight
- automated Country / System QA
- browser visual QA
- final user approval
- production publication
