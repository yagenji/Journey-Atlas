> **STATUS — COMPLETED (2026-09-05)**  
> This file is retained as a historical execution/plan record. The current authoritative renewal status is `data/country-renewal-status.json`: content / visual / map / sources = `DONE`, QA = `PASS`, production = `LIVE_CURRENT`. Any `PENDING`, `Still pending`, or pre-publish notes below describe an earlier checkpoint and are not current tasks.

# San Marino Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/sanmarino-renewal`

This document is the locked PHASE 2 content design for the San Marino Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Monte Titano / view from Fiorentino
- Hero lead
- Current eight scene locations and scene copy
- Current 1200×760 map geometry / markers / label offsets unless later browser QA finds a readability issue
- Signature Facts: current three topics
- Seasons: current four items
- For Whom: current three personas
- Travel Notes: current three items
- Related Destinations: Italy / Vatican City / Liechtenstein
- Theme taxonomy assignment: 街を歩く / 時をたどる
- JOURNEY LENS remains absent because the destination registry currently has `journeyLensPublished:false`

## Country Profile — KEEP STRUCTURE / FIX POPULATION DISPLAY

Visible Profile remains exactly six items. Region stays internal.

- 首都：サンマリノ市
- 人口：34,167人（2026年6月30日）
- 面積：61.19 km²（世田谷区とほぼ同じ規模）
- 言語：イタリア語（公用語）
- 主な宗教：キリスト教（カトリックが中心）
- 通貨：ユーロ（EUR）

Reason for the population copy fix: the current JSON already cites the official II quarter 2026 demographic bulletin and records 34,167 residents at 30 June 2026, while the visible copy still rounds this to “約3万人（2026年）”. Use the exact current official figure at implementation.

Source:
- Ufficio Nazionale di Statistica — Bollettino II trimestre 2026
  - https://www.statistica.sm/

## Signature Facts — KEEP 3

### 1. イタリアとの国境 — 約40 km

KEEP.

San Marino is entirely surrounded by Italy; the current official visitor information gives the border length as almost 40 km.

### 2. 国家元首 — 2人 × 6か月

KEEP.

Two Captains Regent jointly perform the Head of State function, with six-month terms beginning on 1 April and 1 October.

### 3. カミーノ・デル・ティターノ — 43 km

KEEP.

The official Walk of the Titano is a 43 km ring connecting the nine Castelli and links an overall 110 km trail network.

These three topics remain distinct: national geography / political institution / travel scale.

## Encounters — LOCKED 8

Replace the food-heavy current list so Taste can own the dish-level food topics.

1. 三つの塔
2. 石造建築
3. 丘陵農地
4. 葡萄畑
5. オリーブ畑
6. 木曜市
7. 職人工房
8. 森林の小径

Rationale:
- removes current dish-level entries ピアディーナ / ブストレンゴ before the new Taste section is added
- avoids turning Encounters into a scene-name index
- keeps architecture / agriculture / daily commerce / craft / walking landscape in balance

## Beyond the Scenery — KEEP 6 / REFRESH RAILWAY COPY

Keep the six current topics:

1. 13世紀以来の自由共和国の連続性
2. モンテ・ティターノを境に変わる土地利用
3. 1463年に加わった4つのCastelli
4. リミニ＝サンマリノ鉄道
5. 1906年のアレンゴ
6. 9つのCastelliと地域自治

### Railway topic — current-data refresh

Keep the historical role but update it to reflect the 2026 restoration.

**Title:** 1932年の「青白の列車」が、2026年に旧駅へ戻った

**Text:** 1932年開通のリミニ＝サンマリノ鉄道は、32kmを約1時間で結ぶ電気鉄道だった。1944年に運行を終えたが、保存・復元が進み、2026年6月にはAB-03電車がモンターレ・トンネルから旧サンマリノ駅前まで再び走れる約950mの区間が整備された。

**Points:**
- 本線の運行期間は1932〜1944年
- 2026年6月、復元区間が旧駅前まで延伸され、夏〜9月にはAB-03のガイド付き乗車体験が案内された

Sources:
- Visit San Marino — Montale Tunnel and Historic Train
- Visit San Marino — 30 June 2026, AB-03 returns to Station Square after 82 years
- Visit San Marino — Travel on the Treno Bianco Azzurro

The 2026 ride schedule is time-sensitive. At final publication, keep the restoration fact but recheck any schedule wording before surfacing it as current travel advice.

## Travel Trivia — LOCKED 5

Keep four current topics:

1. 観光案内所の記念パスポートスタンプ
2. 独自図柄のユーロ硬貨
3. 9月3日の歴史行列とクロスボウ競技
4. 夏季の公共宮殿の衛兵交代

Replace the current Torta Tre Monti Trivia card because Torta Tre Monti moves into Taste.

### New Trivia — Borgo Maggiore Thursday Market

**Category:** MARKET / 暮らし  
**Title:** 木曜朝の市場は、13世紀のMercataleから続く  
**Text:** ボルゴ・マッジョーレでは毎週木曜の朝に市場が開かれる。公式観光情報では最初の記録を1243年までさかのぼり、現在も日用品の露店が並ぶ週ごとの習慣として続いている。  
**Icon:** city  
**Source key planned:** borgoMarket

Source:
- Visit San Marino — Borgo Maggiore and agrifood markets
  - https://www.visitsanmarino.com/pub1/VisitSM/en/attivita/Shopping/Mercato-di-Borgo-Maggiore.html

## Taste — LOCKED

Kicker: `TASTE OF SAN MARINO`  
Title: `サンマリノで食べたいもの`

Intro: `手打ちパスタ、薄いピアディーナ、農家菓子、三塔を名に持つ菓子から、ロマーニャとマルケに接する小国の食文化をたどる。`

The four roles and silhouettes are intentionally distinct:
broth pasta / folded thin flatbread / rustic baked cake / layered round wafer cake.

### FOOD01 — カッペレッティ・イン・ブロード / Cappelletti in brodo

**Copy**  
詰め物をした小さなパスタを温かいブロードに浮かべる料理。サンマリノではクリスマス当日の伝統食として公式観光情報にも紹介され、家庭の祝祭と手打ちパスタ文化をつなぐ一皿。

Planned asset: `food-cappelletti-in-brodo.webp`

**DISH IDENTITY**
- small filled cappelletti pasta
- distinct folded / hat-like pieces
- clear golden broth
- pasta visible across the surface, not buried
- one simple soup bowl
- restrained home-style presentation

Source:
- Visit San Marino — Gastronomy of San Marino
  - https://www.visitsanmarino.com/pub2/VisitSM/en/contenuto/About-San-Marino/Gastronomia.html

### FOOD02 — サンマリノ式ピアディーナ / Piadina sammarinese

**Copy**  
サンマリノのピアディーナは、周辺のエミリア系の中でも特に薄いと紹介される平焼きパン。Terra di San Marinoでは地元小麦やオリーブ油などを使う規格があり、Casatellaなど地域の乳製品と合わせても食べられる。

Planned asset: `food-piadina-sammarinese.webp`

**DISH IDENTITY**
- one very thin round piadina, lightly browned
- folded once, not a thick sandwich
- soft white Casatella-style local fresh cheese visible
- optional small amount of rocket leaves
- flat plate
- bread remains the visual subject

Sources:
- Visit San Marino — Gastronomy of San Marino
- Consorzio Terra di San Marino — Piadina Terra di San Marino
  - https://www.terradisanmarino.com/cooperativa-ammasso-prodotti-agricoli

### FOOD03 — ブストレンゴ / Bustrengo

**Copy**  
乾いたパンや乳製品づくりの残り、干し葡萄などを無駄にしない農家の知恵から生まれた焼き菓子。公式観光情報でも、サンマリノで最も古く親しまれてきた菓子の一つとして紹介される。

Planned asset: `food-bustrengo.webp`

**DISH IDENTITY**
- low rustic round baked cake
- golden-brown top
- dense moist crumb
- visible sultanas / raisins
- one cut wedge may show the interior
- simple flat plate, no elaborate garnish

Sources:
- Visit San Marino — Gastronomy of San Marino
- Terra di San Marino — production specification for Bustrengo

### FOOD04 — トルタ・トレ・モンティ / Torta Tre Monti

**Copy**  
丸いウエハースを5層重ね、カカオとヘーゼルナッツのクリームを挟み、外周をダークチョコレートで仕上げる菓子。「三つの山」の名がモンテ・ティターノと三塔の国らしさを食へつなぐ。

Planned asset: `food-torta-tre-monti.webp`

**DISH IDENTITY**
- round low wafer cake
- five thin crisp wafer layers clearly visible in cut edge
- cocoa-hazelnut cream between layers
- dark chocolate coating around the outer rim
- one clean slice or partial cut revealing layers
- simple flat plate

Sources:
- Visit San Marino — Gastronomy of San Marino
- Visit San Marino — La Serenissima / Torta Tre Monti
  - https://www.visitsanmarino.com/pub2/VisitSM/en/attivita/Schede-Ristoranti/La-Serenissima.html

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Cappelletti in brodo
- FOOD02 — NOT STARTED / Piadina sammarinese
- FOOD03 — NOT STARTED / Bustrengo
- FOOD04 — NOT STARTED / Torta Tre Monti

Do not add these planned image paths to the production Country JSON until all four images are independently generated, user APPROVED, stored in the approved folder, fully decoded and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**山上の歴史地区とボルゴを歩く**

サンマリノ市を拠点に三つの塔と公共宮殿を歩き、ボルゴ・マッジョーレまで下ると、山上都市と麓の関係を無理なく見られる。  
例：サンマリノ市 → 三つの塔 → ボルゴ・マッジョーレ。

### 5〜7日 / map
**首都から東西のCastelliへ広げる**

歴史地区に加え、東のモンテジャルディーノ／ファエターノと、西のアクアヴィーヴァへ日を分けて広げると、首都だけでは見えない丘陵集落と土地利用が見えてくる。  
例：サンマリノ市 → ボルゴ・マッジョーレ → アクアヴィーヴァ → モンテジャルディーノ → ファエターノ。

### 8日以上 / compass
**9つのCastelliを歩き、小国全体を旅にする**

43kmのCammino del Titanoと8つのテーマ別散策路を軸にすると、国土61km²を短時間で「回る」のではなく、森林・農地・旧鉄道・周縁集落まで一つずつ読む旅にできる。  
例：サンマリノ市 → ボルゴ・マッジョーレ → Monte Cerreto → Chiesanuova / Gorgascura → Fiorentino / Castellaccio → Montegiardino → Serravalle / Domagnanoを複数日に分けてつなぐ。

Source:
- Visit San Marino — The Walk of the Titano
  - https://www.visitsanmarino.com/pub1/VisitSM/en/luogo/ITINERARI-NATURALISTICI/Il-cammino-del-Titano.html
- Visit San Marino — individual nature trails

Note: the 8-day tier exists because the global Reference v3 format is fixed. For San Marino it must be framed as a slow walking / all-Castelli journey, not as a claim that a conventional highlights trip requires eight days.

## Transport — LOCKED

Title: `バス・車・ロープウェイ・徒歩`  
Icon: `road`

Text:

`国内へ入る旅客鉄道はなく、鉄道利用ならイタリアのリミニ駅からバスへ乗り継ぐ。車はSS72などから入り、国内ではバスと車を軸に、ボルゴ・マッジョーレとサンマリノ市を結ぶロープウェイ、歴史地区や丘陵の徒歩を組み合わせる。`

Travel Scale explains **how much of San Marino to combine for a given stay**. Transport explains **how to enter and move through the country**.

Sources:
- Visit San Marino — How to get to San Marino
  - https://www.visitsanmarino.com/pub1/VisitSM/en/contenuto/Pianifica-il-viaggio/COME-ARRIVARE.html
- Visit San Marino — The Cable Car
  - https://visitsanmarino.com/pub2/VisitSM/en/contenuto/Vivi/Funivia.html

Cable-car hours / fares are time-sensitive and are not embedded in the locked Transport copy.

## For Whom — KEEP EXACTLY 3

1. 小さな共和国を制度と建築から理解したい人
2. 首都だけでなく丘陵の暮らしまで見たい人
3. 歩いて一国の輪郭をつかみたい人

No fourth persona.

## Travel Notes — KEEP 3

1. 街歩き用の靴だけで考えない
2. 国土は小さいが、高低差がある
3. イタリアとの国境に通常の出入国審査はない

These remain distinct from Travel Scale and Transport.

## Themes — KEEP

Taxonomy assignment remains:

- city / 街を歩く
- history / 時をたどる

Do not duplicate Theme assignment inside the Country JSON.

## Current-standard implementation notes

After Visual Complete Gate:

- Keep `schemaVersion: 2`
- Keep current Hero / 8 scenes / map
- Keep Signature Facts 3
- update visible Profile population to 34,167（2026年6月30日）
- replace Encounters with the locked eight-topic list
- refresh the railway Beyond card with the 2026 restoration fact
- replace the Torta Tre Monti Trivia card with the Borgo Maggiore Thursday Market card
- add the locked Taste section with four APPROVED image paths
- add the locked Spain-format Travel Scale
- change Transport title to Japanese and add `"icon": "road"`
- keep FOR WHOM exactly 3
- keep Travel Notes 3
- refresh `sourcesVerifiedAt`, `sourceDates` and source metadata for Taste / Travel Scale / Transport / Borgo market / 2026 railway
- keep Theme assignment only in `data/theme-taxonomy.json`
- do not add country-specific CSS or JS
- do not alter `atlasPublished:true` during renewal branch work

## Source lock — verified 2026-09-04

High-trust current sources:

- Ufficio Nazionale di Statistica — II quarter 2026 demographic bulletin
  - https://www.statistica.sm/
- Visit San Marino — Gastronomy of San Marino
  - https://www.visitsanmarino.com/pub2/VisitSM/en/contenuto/About-San-Marino/Gastronomia.html
- Consorzio Terra di San Marino — Piadina Terra di San Marino
  - https://www.terradisanmarino.com/cooperativa-ammasso-prodotti-agricoli
- Visit San Marino — La Serenissima / Torta Tre Monti
  - https://www.visitsanmarino.com/pub2/VisitSM/en/attivita/Schede-Ristoranti/La-Serenissima.html
- Visit San Marino — Borgo Maggiore and agrifood markets
  - https://www.visitsanmarino.com/pub1/VisitSM/en/attivita/Shopping/Mercato-di-Borgo-Maggiore.html
- Visit San Marino — The Walk of the Titano
  - https://www.visitsanmarino.com/pub1/VisitSM/en/luogo/ITINERARI-NATURALISTICI/Il-cammino-del-Titano.html
- Visit San Marino — How to get to San Marino
  - https://www.visitsanmarino.com/pub1/VisitSM/en/contenuto/Pianifica-il-viaggio/COME-ARRIVARE.html
- Visit San Marino — The Cable Car
  - https://visitsanmarino.com/pub2/VisitSM/en/contenuto/Vivi/Funivia.html
- Visit San Marino — Montale Tunnel and Historic Train
  - https://www.visitsanmarino.com/pub2/VisitSM/en/luogo/Arte-e-cultura/Galleria-Montale-e-Treno-storico.html
- Visit San Marino — AB-03 returns to Station Square after 82 years, 30 June 2026
  - https://visitsanmarino.com/pub1/VisitSM/en/visitnews/20260630_CS_Treno_Bianco_Azzurro.html

Existing official/high-trust source lock in the current Country JSON remains valid for area, language, religion, currency, Hero/scenes, political institutions, UNESCO, border formalities, euro coins and the 43 km Walk of the Titano.

## PHASE 2 gate

Content design: **DONE / LOCKED**

Still pending:
- PHASE 3 Image Decision
- Taste visual production and user approval
- approved-folder storage and verification
- Visual Complete Gate
- Country JSON implementation
- latest-main sync check
- automated QA
- browser visual QA
- final user approval
- production publication


## PHASE 3 — Image Decision

Date: 2026-09-04

### Hero

**KEEP**

Current asset:

`assets/images/sanmarino/approved/hero-monte-titano.png`

Decision basis:

- Current Hero concept remains Monte Titano / view from Fiorentino.
- The image is already the published production Hero and remains aligned with the Country identity: Mount Titano, the historic centre and the three-tower skyline.
- Latest-main all-published image audit fully decoded all published raster payloads and reported zero findings.
- The current validator requires Hero images to be at least 1200×760 and landscape; San Marino passes the current audit.
- PNG format alone is not a reason to normalize or regenerate.

### Scene 01 — Guaita First Tower

**KEEP**

`assets/images/sanmarino/approved/guaita-first-tower.png`

### Scene 02 — Piazza della Libertà / Palazzo Pubblico

**KEEP**

`assets/images/sanmarino/approved/piazza-della-liberta-public-palace.png`

### Scene 03 — Montale Third Tower

**KEEP**

`assets/images/sanmarino/approved/montale-third-tower.png`

### Scene 04 — Borgo Maggiore / Cable Car

**KEEP**

`assets/images/sanmarino/approved/borgo-maggiore-cable-car.png`

### Scene 05 — Montegiardino

**KEEP**

`assets/images/sanmarino/approved/montegiardino-village.png`

### Scene 06 — Monte Cerreto / Acquaviva

**KEEP**

`assets/images/sanmarino/approved/acquaviva-monte-cerreto.png`

### Scene 07 — Lago di Faetano

**KEEP**

`assets/images/sanmarino/approved/faetano-lake.png`

### Scene 08 — Chiesanuova

**KEEP**

`assets/images/sanmarino/approved/chiesanuova-hills.png`

### Landscape selection rationale

The current eight scenes already describe the country's small-scale diversity without requiring artificial replacement:

- Mount Titano fortress architecture
- civic / institutional centre
- wooded watchtower landscape
- vertical connection between Borgo Maggiore and the capital
- peripheral stone village
- western wooded hill terrain
- eastern everyday waterside landscape
- south-western agricultural hills

The set is intentionally not a ranking of famous places. It already broadens the page beyond the Three Towers and old town into the outer Castelli and everyday landscape.

### Technical image QA evidence

Relevant current-main validation evidence:

- all-published image audit: PASS
- 28 published Country Pages
- 324 raster payloads fully decoded
- zero image findings

Current validator requirements relevant to San Marino:

- Hero: minimum 1200×760 and landscape orientation
- Scene: minimum 1200×800
- Scene: exact 3:2 aspect ratio
- raster complete verify + load
- approved-folder reference hygiene
- map SVG canvas 1200×760

The San Marino renewal branch has not changed any Hero / Scene asset or image reference since the passing audit, so no new technical reason exists to regenerate or normalize the retained landscape set.

### Approved-folder hygiene — current landscape state

Current approved folder contains exactly nine published landscape rasters:

- 1 Hero
- 8 Scenes
- no Taste images yet
- no draft / temporary / test / placeholder / rejected / parts files detected in the approved folder listing

Taste assets will be added later only after user approval.

### NORMALIZE decision

**NONE**

No retained Hero or Scene needs resize, crop or file-format conversion to satisfy the current validator. Existing PNG format is supported and is not a reason by itself to convert to WebP.

### REGENERATE decision

**NONE for Hero / Scenes**

No current selection, technical or source-based reason requires landscape regeneration.

### Map

**KEEP**

`assets/images/sanmarino/map-atlas-v1.svg`

Structural checks:

- 1200×760 canvas: PASS
- role=img: PASS
- aria-label: PASS
- ellipse: none
- radialGradient: none
- current Hero / scene coordinates remain unchanged

Map Browser readability remains part of later visual QA and does not block the structural KEEP decision.

### Taste visual decision

Taste is the only new visual-production requirement.

1. FOOD01 — Cappelletti in brodo — **ADD / NEXT**
2. FOOD02 — Piadina sammarinese — **ADD / NOT STARTED**
3. FOOD03 — Bustrengo — **ADD / NOT STARTED**
4. FOOD04 — Torta Tre Monti — **ADD / NOT STARTED**

Each image must be generated independently under the Taste hard rule:

- one generation = one dish = one image
- 1200×800 final target
- exact 3:2
- WebP
- Spain Taste visual language
- clean pale beige / ivory background
- photo 6 : quiet watercolor 4
- no collage / no multi-panel / no text
- do not edit the previous food image into the next one

### Taste state after user review

- FOOD01 — **APPROVED** / Cappelletti in brodo
- FOOD02 — **APPROVED** / Piadina sammarinese
- FOOD03 — **APPROVED** / Bustrengo
- FOOD04 — **APPROVED** / Torta Tre Monti

All four images were generated as independent images in one production round and approved by the user. Do not regenerate unless explicitly requested. Repository storage / 1200×800 WebP normalization / complete decode / approved-folder hygiene are still pending before the Visual Complete Gate.

## PHASE 3 gate

Image Decision: **DONE / LOCKED**

- Hero: KEEP
- Scene 01–08: KEEP
- Map: KEEP
- NORMALIZE: 0
- Landscape REGENERATE: 0
- Taste: 4 new independent images required
- FOOD01 Cappelletti in brodo: NEXT
- FOOD02–04: NOT STARTED
- `hardImageGate`: remains **false**

Next phase: **VISUAL PRODUCTION — FOOD01 Cappelletti in brodo**
