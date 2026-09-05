> **STATUS — COMPLETED (2026-09-05)**  
> This file is retained as a historical execution/plan record. The current authoritative renewal status is `data/country-renewal-status.json`: content / visual / map / sources = `DONE`, QA = `PASS`, production = `LIVE_CURRENT`. Any `PENDING`, `Still pending`, or pre-publish notes below describe an earlier checkpoint and are not current tasks.

# France Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/france-renewal`

This document is the locked PHASE 2 content design for the France Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Mont-Saint-Michel
- Hero lead
- Current eight scene locations and scene copy
- Map geometry / markers / labels unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Travel Trivia: keep all five current topics
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Related Destinations: Italy / Spain / Switzerland
- Theme taxonomy assignment: 街を歩く / 時をたどる / 食をめぐる

## Signature Facts — LOCKED

Use three distinct topics: food culture / society / urban craft.

1. **バゲット — 年間約60億本**
   - Note: パン屋が街の身近な存在で、バゲットは毎日の食卓に根づいている。
   - Topic key: `baguette-everyday-culture`
   - Source: Confédération Nationale de la Boulangerie-Pâtisserie Française / UNESCO

2. **法定労働時間 — 週35時間**
   - Note: フルタイム労働者の法定労働時間は週35時間。これは最大時間ではなく、原則として時間外労働を数える基準になる。
   - Topic key: `statutory-workweek-35-hours`
   - Source: Ministère du Travail / Service-Public.fr

3. **パリの亜鉛屋根 — 約80%**
   - Note: ユネスコによると、パリの屋根のおよそ8割が亜鉛で覆われる。灰色の屋根景観を支える職人技は2024年に無形文化遺産へ登録された。
   - Topic key: `paris-zinc-roofs-80-percent`
   - Source: UNESCO Intangible Cultural Heritage

Remove the Alsace Wine Route number from Signature Facts. The Wine Route remains valuable context for Scene 6 and can continue to be supported in Sources, but keeping it as a Signature Fact would leave two of three facts in the same food/wine topic.

## Encounters — LOCKED 8

The current list is too close to a literal eight-scene index. Replace it with a mixture of landscape, built environment and everyday experience.

1. ゴシック建築
2. カフェのテラス
3. 地方市場
4. 葡萄畑
5. アルプス
6. 地中海の入り江
7. 大西洋の砂丘
8. コルシカの山地

These remain short encounter tags and are not expanded into explanatory copy.

## Beyond the Scenery — LOCKED 6

Keep four current cards and replace the FOOD and ROAD cards so this section does not duplicate Taste or Transport.

### 1. CITY / 街を歩く — KEEP
**パリはセーヌ川から地区を読む**

シテ島を核に、右岸と左岸へ街が広がる。川沿いを歩くと、ノートルダム、ルーヴル周辺、近代の大通りまで、建築の時代差と都市の方向が同時に見えてくる。

Points:
- セーヌ川を基準にすると主要地区の位置関係をつかみやすい
- 大通りだけでなく市場や住宅地へ入ると、観光都市とは別の日常が見える

### 2. HISTORY / 時をたどる — KEEP
**修道院、大聖堂、城を同じ国土でつなぐ**

中世のモン・サン＝ミシェルとノートルダム、ルネサンス期のロワールの城館まで、建築様式は土地と権力の変化を映す。建物単体ではなく、川、湾、農地との位置関係を見ると歴史が立体的になる。

Points:
- モン・サン＝ミシェルでは潮汐地形と宗教建築が重なる
- シュノンソーではシェール川そのものが建築の一部になっている

### 3. LIFE / 暮らしに出会う — KEEP
**地方へ行くほど、暮らしの輪郭が変わる**

パリからアルザス、プロヴァンス、コルシカへ移ると、家の形、食材、言葉の響き、街の速度が変わる。フランスを一つの都市文化として見るより、地域の違いを移動して比べる方が国の幅を理解しやすい。

Points:
- 市場や住宅地へ入ると地域の日常が見えやすい
- 同じ共和国の中でも建築や生活文化は地方ごとの差が大きい

### 4. CULTURE / 文化に触れる — KEEP
**職人は「フランス巡歴」で技を受け継ぐ**

コンパニョナージュは、石、木、金属、革、繊維、食などの技能を、都市を移動しながら学び継承するフランスの職人教育の仕組み。完成した建築や製品の背後に、移動と修業を組み込んだ長い技能継承の文化がある。

Points:
- 若い職人は国内外の都市を巡りながら異なる技術や仕事の方法を学ぶ
- コンパニョナージュは2010年にユネスコ無形文化遺産へ登録された

### 5. LANGUAGE / 言葉に触れる — REPLACE FOOD
**フランス語の隣に、地域の言葉が残る**

共和国の公用語はフランス語だが、ブルターニュ語、コルシカ語、アルザス語、バスク語、オック語など多くの地域語も文化遺産として受け継がれている。地方へ移ると、地名や地域文化の背景に別の言語圏が見えてくる。

Points:
- 憲法75条1項は「地域語はフランスの文化遺産に属する」と定める
- 文化省は本土だけでもブルターニュ語、バスク語、コルシカ語、オック語、アルザス語など多数の地域語を挙げている

Source: Ministère de la Culture / Constitution Article 75-1

### 6. LIFE / 暮らしに出会う — REPLACE ROAD
**カフェは、飲み物だけの場所ではない**

フランスの都市では、カフェやビストロが食事の場であるだけでなく、人が座り、話し、通りを眺める街の居場所にもなってきた。観光名所を移動するだけでなく、テラスで一度足を止めると街の日常の速度が見えてくる。

Points:
- パリのカフェ文化は作家、思想家、芸術家が集まる社会的・文化的な場として長い歴史を持つ
- ビストロや市場の食堂は、地域の日常へ入りやすい場所の一つ

Source: France.fr / Explore France

## Travel Trivia — KEEP 5

Keep the current five topics without adding food duplication:

1. 海外領土 — ヨーロッパの外にもフランスが続いている
2. 潮汐 — モン・サン＝ミシェルは高潮で再び島になる
3. 音楽 — 6月21日は街そのものが音楽会場になる
4. 食文化 — 「フランス人の美食術」は料理名ではない
5. 地形 — ピラ砂丘は少しずつ森側へ動いている

During implementation, add distinct `topicKey` values so cross-section duplication can be validated.

## Taste — LOCKED

Kicker: `TASTE OF FRANCE`  
Title: `フランスで食べたいもの`

Intro: `パン屋、港町、地方の粉もの、家庭料理まで、土地ごとに違う食文化を4皿からたどる。`

### FOOD01 — クロワッサン / Croissant

**Copy**  
薄い生地とバターを折り重ねて焼く、フランスのパン屋で身近なヴィエノワズリー。朝の街で焼きたてを一つ買うだけでも、ブーランジュリーが日常に近いことが分かる。

Planned asset: `food-croissant.webp`

**DISH IDENTITY**
- 三日月形の単体ペストリー
- バターを折り込んだ層が見える
- 表面は自然な黄金色
- 中身・クリーム・チョコレートなし
- 粉砂糖や果物などの装飾なし
- パン籠ではなくクロワッサン1個が主役

Source: France.fr

### FOOD02 — ブイヤベース / Bouillabaisse

**Copy**  
マルセイユの港町で育った魚料理。地中海の魚を香草や香辛料とともに煮込み、海と都市が近い南フランスの食文化を一皿で感じられる。

Planned asset: `food-bouillabaisse.webp`

**DISH IDENTITY**
- 魚が主役の地中海スープ／煮込み
- オレンジ〜黄金色の魚介スープ
- 魚の切り身が明確に見える
- パエリアやパスタではない
- 過剰な貝殻・豪華なシーフード盛りにしない
- ボウルまたは深皿で自然に提供

Source: France.fr / Marseille destination guidance

### FOOD03 — ガレット・コンプレット / Galette complète

**Copy**  
ブルターニュのそば粉のガレットに、卵、ハム、チーズを合わせる定番。小麦のクレープとは違う香ばしい生地から、ブルターニュの土地と粉食文化が見えてくる。

Planned asset: `food-galette-complete.webp`

**DISH IDENTITY**
- 薄い茶褐色のそば粉ガレット
- 四辺を内側へ折った四角に近い形
- 中央に目玉焼き
- ハムと溶けたチーズ
- 甘いクレープではない
- 果物・生クリーム・チョコレートなし

Source: France.fr / Brittany gastronomy guidance

### FOOD04 — キッシュ・ロレーヌ / Quiche lorraine

**Copy**  
卵、クリーム、燻製豚肉をパイ生地に流して焼くロレーヌの塩味のタルト。材料はシンプルだが、地方名がそのまま料理名として残る代表的な地域料理。

Planned asset: `food-quiche-lorraine.webp`

**DISH IDENTITY**
- 円形の塩味タルト
- 黄金色のパート・ブリゼ
- 卵とクリームの淡い黄色のフィリング
- 小さな燻製豚肉／ラルドンが見える
- 伝統形として野菜を入れない
- チーズを主役にしない

Source: France.fr / Lorraine tourism guidance

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Croissant
- FOOD02 — NOT STARTED / Bouillabaisse
- FOOD03 — NOT STARTED / Galette complète
- FOOD04 — NOT STARTED / Quiche lorraine

Do not add these planned image paths to the production Country JSON until all four images are user APPROVED and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**パリを拠点に近郊へ**

一つの都市を拠点にし、日帰りで宮殿や歴史都市を加えるくらいが現実的。例：パリ＋ヴェルサイユ、またはパリ＋シャルトル。

### 5〜7日 / map
**高速鉄道で2〜3都市をつなぐ**

TGVを使うと、首都から地方都市へ移動して地域差を比べやすい。例：パリ → ストラスブール → コルマール。

### 8日以上 / compass
**南へつなぎ、島まで旅を広げる**

高速鉄道に地方交通や航空・フェリーを足すと、本土から地中海の島まで国土の幅が見えてくる。例：パリ → リヨン → アヴィニョン → マルセイユ → コルシカ。

Source: SNCF / SNCF Connect for TGV and reservation system; France.fr for regional itinerary logic.

## Transport — LOCKED

Title: `高速鉄道・在来線・車・フェリー`  
Icon: `road`

Text:

`都市間はTGVを軸にし、地方ではTERや地域バスへつなぐ。葡萄畑、アルプス、カランク、砂丘などは徒歩や車を足し、コルシカを入れる場合は航空またはフェリーを含む別区間として考える。`

Travel Scale explains **how far a given number of days can reasonably reach**. Transport explains **which modes are used to move through France**.

## For Whom — KEEP EXACTLY 3

1. 建築と街を歩きながら時代をたどりたい人
2. 山・海・砂丘まで地形の幅を見たい人
3. 食と地方文化を産地まで追いたい人

No fourth persona.

## Travel Notes — LOCKED 3

Replace the current first note because it would duplicate Travel Scale. Keep the other two with light wording normalization.

### 1. TGVは長距離区間から先に決める

TGV INOUIや一部INTERCITÉSは予約が必要。週末や休暇期など移動日が決まっているなら、地方交通より先に都市間の長距離区間を押さえると旅程を組みやすい。

Source: SNCF Connect

### 2. カランクは当日の入山条件を確認する

夏は山火事リスクに応じて自然地域へのアクセスが制限されることがある。アン・ヴォーへ向かう日は、国立公園の最新アクセス情報を確認してから出発する。

Source: Parc national des Calanques

### 3. 高山と海岸は都市と同じ感覚で予定を組まない

ラック・ブランは残雪や天候、ピラ砂丘や海岸は風・暑さの影響を受ける。移動時間だけでなく、その日の自然条件を旅程に入れる。

Source: Chamonix-Mont-Blanc tourism / Grand Site de la Dune du Pilat

## Current-standard implementation notes

After Visual Complete Gate:

- Add `contentQaVersion: 1`
- Add the locked Taste section with four APPROVED image paths
- Add the locked Spain-format Travel Scale
- Replace Signature Fact 2 with the 35-hour statutory workweek
- Add distinct `topicKey` values across Signature Facts / Beyond / Trivia / Travel Notes where supported by the current schema
- Replace Encounters with the locked eight tags
- Replace Beyond FOOD and ROAD cards with LANGUAGE and café/social-life cards
- Change Transport title to Japanese and add `"icon": "road"`
- Replace Travel Note 1
- Refresh `sourcesVerifiedAt` and `sourceDates`
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS

## Source lock — verified 2026-09-04

Use the following high-trust/current sources during implementation:

- Population: INSEE — metropolitan France population 66,792,845 / approximately 66.793 million on 1 January 2026.
  - https://www.insee.fr/en/statistiques/serie/001760078
  - https://www.insee.fr/fr/statistiques/5225246
- Statutory workweek: French Ministry of Labour / Service-Public.fr — legal full-time reference is 35 hours per week; it is not an absolute maximum.
  - https://travail-emploi.gouv.fr/la-duree-legale-du-travail
  - https://www.service-public.fr/particuliers/vosdroits/F1911
- Regional languages: French Ministry of Culture / Constitution Article 75-1.
  - https://www.culture.gouv.fr/thematiques/langue-francaise-et-langues-de-france/agir-pour-les-langues/promouvoir-les-langues-de-france/langues-regionales
  - https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000019241104
- Compagnonnage: UNESCO Intangible Cultural Heritage.
- Paris zinc roofs: UNESCO Intangible Cultural Heritage, inscribed 2024.
- Café / bistro social culture: France.fr / Explore France.
  - https://www.france.fr/en/article/5-most-famous-cafes-to-visit-in-paris/
  - https://www.france.fr/fr/article/a-table-en-france-conseils-pour-une-exp%C3%A9rience-gourmande-authentique/
- Croissant: France.fr.
  - https://www.france.fr/en/article/croissants-france-favorite-snack/
- Bouillabaisse: France.fr / Marseille destination page.
  - https://www.france.fr/en/destination/marseille/
- Breton crêpes / galettes: France.fr, updated 23 January 2025.
  - https://www.france.fr/fr/article/5-minutes-pour-tout-savoir-sur-les-crepes-bretonnes/
- Quiche Lorraine: France.fr / Lorraine gastronomy.
  - https://www.france.fr/fr/article/5-specialites-de-lorraine-a-gouter-absolument/
- TGV reservation / planning: SNCF Connect.
  - https://www.sncf-connect.com/aide/le-placement-bord-des-trains
  - https://www.sncf-connect.com/aide/l-ouverture-des-ventes
- En-Vau access: Parc national des Calanques.
  - https://www.calanques-parcnational.fr/en/en-vau
- Alsace Wine Route background: Visit Alsace — inaugurated 1953, more than 170 km.
  - https://pro.visit.alsace/en/the-wine-route/
- Dune du Pilat movement: Grand Site de la Dune du Pilat.

## PHASE 2 gate

Content design: **DONE / LOCKED**

Still pending:
- exact binary image audit for retained Hero + 8 scenes
- Taste visual production and user approval
- Visual Complete Gate
- Country JSON implementation
- automated QA
- browser visual QA
- final user approval
- production publication


## Taste approvals — 2026-09-04

All four France Taste images were user APPROVED as one review batch.

- FOOD01 **Croissant** — APPROVED
  - Final filename: `food-croissant.webp`
  - Target production path: `assets/images/france/approved/food-croissant.webp`
- FOOD02 **Bouillabaisse** — APPROVED
  - Final filename: `food-bouillabaisse.webp`
  - Target production path: `assets/images/france/approved/food-bouillabaisse.webp`
- FOOD03 **Galette complète** — APPROVED
  - Final filename: `food-galette-complete.webp`
  - Target production path: `assets/images/france/approved/food-galette-complete.webp`
- FOOD04 **Quiche lorraine** — APPROVED
  - Final filename: `food-quiche-lorraine.webp`
  - Target production path: `assets/images/france/approved/food-quiche-lorraine.webp`

Local export QA:
- source generation: 1536×1024 / exact 3:2
- final export: 1200×800 WebP
- complete decode: PASS 4/4
- dimensions: PASS 4/4
- format: WebP PASS 4/4

Do not regenerate any of these four images without explicit user instruction.
