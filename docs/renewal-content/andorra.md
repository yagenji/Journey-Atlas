# Andorra Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/andorra-renewal`

This document is the locked PHASE 2 content design for the Andorra Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Sant Joan de Caselles / Canillo
- Hero lead
- Current eight scene locations and scene copy
- Current 1200×760 map geometry / markers / label offsets unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Travel Trivia: keep all five current topics
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Travel Notes: keep the current three items
- Related Destinations: France / Spain / Liechtenstein
- Theme taxonomy assignment: 地球の風景 / 道の先へ
- JOURNEY LENS remains absent because the destination registry currently has `journeyLensPublished:false`

## Signature Facts — LOCKED 3

Replace the current `92%超` tourism-marketing statistic with a more structurally meaningful Andorra-specific fact.

### 1. 共同元首 — 2人

**Label:** 共同元首  
**Value:** 2人  
**Note:** アンドラの国家元首は、ウルジェイ司教とフランス共和国大統領の2人。1993年憲法は両者を共同かつ不可分の国家元首と定め、中世のパリアージュに由来する制度が現代国家に続いている。  
**Icon:** history

Reason: stronger country identity and less ambiguous than the current “92% natural heritage” wording, which can be misread as a formal legal-protection ratio.

Source: Consell General d’Andorra — Constitution, Article 43.

### 2. 3つのスキーエリア合計 — 308 km

**KEEP current topic and value.**

Grandvalira / Pal Arinsal / Ordino Arcalís together provide 308 km of skiable terrain and more than 200 slopes. This is a strong travel-motivation number and explains the winter scale of a 468 km² country.

Source: Visit Andorra / Grandvalira Resorts.

### 3. 2025年の平均実在人口 — 約13.6万人

**KEEP current topic and value.**

Resident population alone understates the number of people using roads, shops and urban infrastructure because visitors, seasonal workers and cross-border commuters are present each day. Keep this as the social / mobility fact.

Source lock: current Govern d’Andorra / Departament d’Estadística effective-population data already recorded in the Country JSON.

## Encounters — KEEP 8

The existing list is concise, non-explanatory and broader than a simple scene index.

1. ロマネスク教会
2. 氷河湖
3. 石造村
4. 温泉
5. スキー
6. 高山草地
7. 山岳道路
8. 移牧文化

No rewrite is required.

## Beyond the Scenery — LOCKED 6

Because the co-principality moves into Signature Facts, remove the current Pareatges/co-principality Beyond card to avoid topic duplication.

Keep five current topics:

1. **7つの教区とComú** — 谷ごとの集落と地方行政
2. **谷道に沿うロマネスク建築** — 教会・集落・旧道の関係
3. **移牧と高山草地** — 山を季節的な生活空間として使う文化
4. **カタルーニャ語だけを公用語とする国家** — 多言語社会の中の国家言語
5. **FHASAと近代道路** — 水力発電投資が道路整備と近代化を進めた歴史

Add one new topic:

### 6. タバコ畑から工業化へ

**Theme:** LIFE / HISTORY  
**Title:** タバコは、山国の農業から近代産業へつながった  
**Text:** 17世紀末に栽培が入り、20世紀にはタバコの栽培と製造がアンドラの重要な産業になった。サン・ジュリア・デ・ロリアの旧工場群を見ると、観光や商業が中心になる前の経済と、谷の農地がどう使われてきたかが見えてくる。  
**Points:**
- アンドラ国立公文書館は17世紀末からタバコ栽培が加わったことを記録
- 旧Reig工場は1909〜1957年に稼働し、タバコ産業の歴史を伝える

Sources:
- Govern d’Andorra / Arxiu Nacional — Els cultius de l’Andorra dels segles XIV–XX
- Museus d’Andorra — Fàbrica Reig Museum
- Govern d’Andorra — 2025 heritage inventory decision for the former tobacco factories of Sant Julià de Lòria

## Travel Trivia — KEEP 5

1. 軍隊を持たない国
2. 夏至の火祭り
3. 冬の「熊」の祭り
4. フランスとスペインの郵便が共存
5. 自由キャンプは標高2,000m未満では禁止

These are sufficiently distinct from Beyond / Taste / Travel Notes.

## Taste — LOCKED

Kicker: `TASTE OF ANDORRA`  
Title: `アンドラで食べたいもの`

Intro: `冬の煮込み、山の野菜料理、祝祭のパスタ、食後のクリームから、ピレネーの暮らしと周辺文化の重なりをたどる。`

The four items are intentionally distinct in role and silhouette: soup bowl / browned mountain vegetable cake / baked pasta rolls / shallow custard dessert.

### FOOD01 — エスクデリャ / Escudella

**Copy**  
肉、ソーセージ、季節の野菜、豆、米や麺を一緒に煮込む冬の代表料理。家庭の鍋料理として続き、1月のSant AntoniやSant Sebastiàでは地域で大鍋のエスクデリャが振る舞われる。

Planned asset: `food-escudella.webp`

**DISH IDENTITY**
- deep traditional soup / stew
- warm clear-to-light-brown broth
- visible chickpeas or white beans
- cabbage, potato and root vegetables
- pieces of meat and thick sausage
- a small amount of rice or short/thick noodles
- served in one simple bowl

Source: Visit Andorra — Escudella / Local products.

### FOOD02 — トリンシャット・アンブ・ロスタ / Trinxat amb rosta

**Copy**  
冬キャベツとじゃがいもをつぶし、フライパンで丸く香ばしく焼いてベーコンを添える山の料理。伝統料理を出すbordaのレストランでも見つけやすく、寒い季節のピレネーらしい一皿。

Planned asset: `food-trinxat-amb-rosta.webp`

**DISH IDENTITY**
- round rustic potato-and-cabbage cake
- pale green / cream interior
- browned pan-seared surface
- one or two crisp bacon strips as the traditional rosta
- compact but handmade shape
- served on a simple flat plate

Source: Visit Andorra — Trinxat amb rosta.

### FOOD03 — アンドラ風カネロニ / Canelons a l’andorrana

**Copy**  
豚、鶏、羊などの肉を詰めたパスタを並べ、ベシャメルとチーズをかけて焼く料理。カタルーニャ経由で広まり、かつてはクリスマス期の祝祭食だったが、現在は一年を通じて食べられる。

Planned asset: `food-canelons-andorrana.webp`

**DISH IDENTITY**
- 3–4 clearly recognisable filled cannelloni rolls
- meat filling
- pale béchamel sauce
- lightly browned grated-cheese top
- baked presentation
- shallow plain ceramic baking dish or plate

Source: Visit Andorra — Andorran-style cannelloni.

### FOOD04 — アンドラ風クレマ / Crema a l’andorrana

**Copy**  
牛乳、卵黄、砂糖を使ったクリームの表面を焦がして仕上げる伝統菓子。Sant Josepの日と結びついてきたが、現在は家庭やレストランで一年を通じて食べられている。

Planned asset: `food-crema-andorrana.webp`

**DISH IDENTITY**
- pale yellow smooth custard
- shallow round ceramic dish rather than a deep bowl
- thin caramelised burnt-sugar surface
- optional restrained piped white egg-foam details around the edge, reflecting Andorran tradition
- clean dessert presentation
- no unrelated garnish

Source: Visit Andorra — Crema a l’andorrana.

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Escudella
- FOOD02 — NOT STARTED / Trinxat amb rosta
- FOOD03 — NOT STARTED / Canelons a l’andorrana
- FOOD04 — NOT STARTED / Crema a l’andorrana

Do not add these planned image paths to the production Country JSON until all four images are independently generated, user APPROVED, stored in the approved folder, fully decoded and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**首都圏を拠点に石造の町と山へ**

アンドラ・ラ・ベリャ／エスカルデスを拠点に、ロマネスク教会や石造集落を1〜2か所加えるくらいが現実的。  
例：アンドラ・ラ・ベリャ／エスカルデス → カニーリョ → オルディノ。

### 5〜7日 / map
**北の湖と南東の渓谷までつなぐ**

町歩きに日帰りの高山ハイクを組み込み、国の北・中央・南東を行き来すると地形の差が見えてくる。  
例：アンドラ・ラ・ベリャ → マドリウ渓谷 → オルディノ／トリスタイナ湖群 → アリンサル。

### 8日以上 / compass
**複数の谷を歩き、峠道まで旅を広げる**

トリスタイナやマドリウに加え、コマペドローサ、グラウ・ロイグ、南部の山岳道路を別日に組むと、小国を「一つの谷」ではなく複数の高地世界として見られる。  
例：アンドラ・ラ・ベリャ → マドリウ → カニーリョ → グラウ・ロイグ → オルディノ／トリスタイナ → アリンサル／コマペドローサ → サン・ジュリア・デ・ロリア／コル・デ・ラ・ガリナ。

Sources:
- Visit Andorra — public transport / mobility
- Visit Andorra — Madriu hiking route
- Visit Andorra — Tristaina Lakes route
- Visit Andorra — Comapedrosa route / nature park

## Transport — LOCKED

Title: `バス・車・徒歩`  
Icon: `road`

Text:

`国内に空港や国境内へ入る鉄道はなく、スペイン・フランスからは国際バスまたは車で入る。国内は毎日運行する路線バスが主要な町を結び、遠い谷ほど本数が少なくなる。高山の湖や渓谷は、路線バスや車で登山口へ近づき、徒歩や季節運行のゴンドラを組み合わせる。`

Travel Scale explains **how much of Andorra to combine for a given stay**. Transport explains **how to enter the country and which modes are practical once there**.

Sources:
- Visit Andorra — Visitor information / public transport
- Visit Andorra — Get around easily
- Visit Andorra — Tristaina summer access

## For Whom — KEEP EXACTLY 3

1. 高山湖と谷を、自分の足でつないで見たい人
2. 小国の歴史を、建築と制度から読みたい人
3. 移動そのものを旅にしたい人

No fourth persona.

## Travel Notes — KEEP 3

1. 11月1日〜5月15日は冬装備のルールを確認する
2. スマートフォンの料金プランにアンドラが含まれるか確認する
3. トリスタイナは夏季でも車で上まで行けるとは限らない

The 2026 Tristaina operating-date detail is time-sensitive and must be rechecked immediately before final implementation / publication if the publication date has moved materially.

## Profile — KEEP

Visible Profile remains exactly six items. Region stays internal.

- 首都：アンドラ・ラ・ベリャ
- 人口：90,021人（2026年7月）
- 面積：468 km²（日本の約0.12%）
- 言語：カタルーニャ語（公用語）／スペイン語・フランス語など
- 主な宗教：キリスト教（カトリックが中心）
- 通貨：ユーロ（EUR）

Current official population dashboard still reports 90,021 for July 2026.

## Current-standard implementation notes

After Visual Complete Gate:

- Keep `schemaVersion: 2`
- Keep current Hero / 8 scenes / map
- Replace Signature Fact `92%超` with the locked `共同元首 2人` fact
- Replace the co-principality Beyond card with the tobacco/agriculture-to-industry card
- Keep Encounters 8
- Add the locked Taste section with four APPROVED image paths
- Add the locked Spain-format Travel Scale
- Change Transport title to Japanese and add `"icon": "road"`
- Keep FOR WHOM exactly 3
- Keep Travel Notes 3
- Refresh `sourcesVerifiedAt` and source metadata for Taste / Travel Scale / Transport / new Signature Fact / tobacco Beyond
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS
- Do not alter `atlasPublished:true` during renewal branch work

## Source lock — verified 2026-09-04

High-trust current sources:

- Govern d’Andorra / Departament d’Estadística — official dashboard; population July 2026 = 90,021
  - https://sig.govern.ad/Sigdde.Public/Inici?Idioma=ca&Pag=PAG_Inici
- Consell General d’Andorra — Constitution, Article 43; two co-princes
  - https://www.consellgeneral.ad/ca/el-consell-dandorra/constitucio-i-reglament/la-constitucio-del-principat-d-andorra
- Visit Andorra — Gastronomy
  - https://visitandorra.com/en/gastronomy/
- Visit Andorra — Local products
  - https://visitandorra.com/en/gastronomy/local-products/
- Visit Andorra — Andorran recipes
  - https://visitandorra.com/en/gastronomy/andorran-recipes.html/
- Visit Andorra — Trinxat amb rosta
  - https://visitandorra.com/en/gastronomy/andorran-recipes/trinxat-amb-rosta-cabbage-potato-and-pork-crackling/
- Visit Andorra — Andorran-style cannelloni
  - https://visitandorra.com/en/gastronomy/andorran-recipes/andorran-style-canellonni/
- Visit Andorra — Crema a l’andorrana
  - https://visitandorra.com/en/gastronomy/andorran-recipes/crema-a-landorrana-andorrana-style-cream/
- Visit Andorra — Public transport / mobility
  - https://visitandorra.com/en/visitor-information/
  - https://visitandorra.com/en/visitor-information/transport-and-mobility/get-around-easily/
- Visit Andorra — Tristaina Lakes
  - https://visitandorra.com/en/nature--sports/hiking-route-estanys-de-tristaina/
- Visit Andorra — Madriu Valley
  - https://visitandorra.com/en/nature--sports/hiking-route-itinerari-de-la-vall-del-madriu/
- Visit Andorra — Comapedrosa
  - https://visitandorra.com/en/nature--sports/hiking-route-cami-de-l-alt-de-comapedrosa/
- Govern d’Andorra / Arxiu Nacional — traditional crops and tobacco
  - https://www.govern.ad/ca/tematiques/cultura-i-esports/arxiu-nacional/publicacions/la-peca-del-mes/2026
- Museus d’Andorra — Fàbrica Reig
  - https://museus.ad/en/museus/museo-fabrica-reig
- Govern d’Andorra — former tobacco factories added to heritage inventory, 2025
  - https://www.govern.ad/ca/w/govern-dona-llum-verda-inclusio-antigues-fabriquestabac-sant-julia-loria-inventari-general-patrimoni-cultural

Existing official/high-trust source lock in the current Country JSON remains valid for area, language, religion, currency, current scenes, current Trivia, current Travel Notes and the 308 km ski-area fact.

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

`assets/images/andorra/approved/hero-san-joan-de-caselles.png`

Decision basis:

- Current Hero concept remains Sant Joan de Caselles / Canillo.
- The asset is already in the approved production folder and was part of the published Andorra page.
- Latest-main all-published image audit fully decoded all published raster payloads and reported zero findings.
- The current validator requires Hero images to be at least 1200×760 and landscape; Andorra passes the current audit.
- PNG format itself is supported and is not a reason to normalize or regenerate.

### Scene 01 — Madriu-Perafita-Claror Valley

**KEEP**

`assets/images/andorra/approved/madriu-perafita-claror-valley.png`

### Scene 02 — Tristaina Lakes

**KEEP**

`assets/images/andorra/approved/tristaina-lakes.png`

### Scene 03 — Ordino Old Town

**KEEP**

`assets/images/andorra/approved/ordino-old-town.png`

### Scene 04 — Casa de la Vall

**KEEP**

`assets/images/andorra/approved/casa-de-la-vall.png`

### Scene 05 — Caldea / Escaldes-Engordany

**KEEP**

`assets/images/andorra/approved/caldea-escaldes-engordany.png`

### Scene 06 — Grau Roig / Grandvalira

**KEEP**

`assets/images/andorra/approved/grau-roig-grandvalira.png`

### Scene 07 — Comapedrosa Valley

**KEEP**

`assets/images/andorra/approved/comapedrosa-valley.png`

### Scene 08 — Coll de la Gallina

**KEEP**

`assets/images/andorra/approved/coll-de-la-gallina.png`

### Landscape selection rationale

The current eight scenes already cover distinct Andorran roles without requiring a selection change:

- cultural landscape / long-term mountain land use
- glacial lakes
- stone settlement
- political / civic history
- modern thermal urban architecture
- winter ski plateau
- high-alpine hiking terrain
- mountain-road / cycling geography

There is no current selection-quality reason to replace a scene merely for geographic equalisation or because another landscape type is visually different.

### Technical image QA evidence

Latest current-main validation run:

`33853388412`

Result:

- Validate country data: PASS
- All-published image audit: PASS
- 28 published Country Pages
- 324 raster payloads fully decoded
- zero image findings

Current validator requirements relevant to Andorra:

- Hero: minimum 1200×760 and landscape orientation
- Scene: minimum 1200×800
- Scene: exact 3:2 aspect ratio
- raster complete verify + load
- approved-folder reference hygiene
- map SVG canvas 1200×760

The Andorra renewal branch has not changed any Hero / Scene asset or Country image reference since that audit, so the technical result applies directly to the retained landscape set.

### Approved-folder hygiene — landscape state

Current approved folder contains exactly the nine existing landscape production rasters:

- 1 Hero
- 8 Scenes
- no Taste images yet
- no draft / temporary / test / placeholder / rejected / parts files

Taste assets will be added later only after user approval.

### NORMALIZE decision

**NONE**

No retained Hero or Scene needs resize, crop, file-format conversion or recompression to meet the current validator. Do not normalize merely because the existing approved images are PNG.

### REGENERATE decision

**NONE for Hero / Scenes**

No current technical or selection reason requires landscape regeneration.

### Map

**KEEP**

`assets/images/andorra/map-atlas-v1.svg`

Structural checks:

- 1200×760 canvas: PASS
- role=img: PASS
- aria-label: PASS
- ellipse: none
- radialGradient: none
- current scene / Hero coordinates remain unchanged

Browser label readability is still part of later visual QA; that does not block the current structural KEEP decision.

### Taste visual decision

Taste is the only new visual-production requirement.

1. FOOD01 — Escudella — **ADD / NEXT**
2. FOOD02 — Trinxat amb rosta — **ADD / NOT STARTED**
3. FOOD03 — Canelons a l’andorrana — **ADD / NOT STARTED**
4. FOOD04 — Crema a l’andorrana — **ADD / NOT STARTED**

Each image must be generated independently under the Taste rule:

- one generation = one dish = one image
- 1200×800 final target
- exact 3:2
- WebP
- Spain Taste visual language
- no collage / no multi-panel / no text
- do not edit the previous food image into the next one

## PHASE 3 gate

Image Decision: **DONE / LOCKED**

- Hero: KEEP
- Scene 01–08: KEEP
- Map: KEEP
- NORMALIZE: 0
- Landscape REGENERATE: 0
- Taste: 4 new independent images required
- FOOD01 Escudella: NEXT
- FOOD02–04: NOT STARTED
- `hardImageGate`: remains **false**

Next phase: **VISUAL PRODUCTION — FOOD01 Escudella**


## Taste approvals — 2026-09-05

- FOOD01 **Escudella** — APPROVED
  - Final filename: `food-escudella.webp`
  - Target production path: `assets/images/andorra/approved/food-escudella.webp`
  - Source generated image is approved for use, but repository storage / 1200×800 WebP normalization / complete decode verification remain pending.
- FOOD02 **Trinxat amb rosta** — NEXT
- FOOD03 **Canelons a l’andorrana** — NOT STARTED
- FOOD04 **Crema a l’andorrana** — NOT STARTED

Do not regenerate FOOD01 unless explicitly requested by the user.


## Taste approval update — FOOD02

- FOOD02 **Trinxat amb rosta** — **APPROVED**
  - Do not regenerate unless explicitly requested.
  - Final filename: `food-trinxat-amb-rosta.webp`
  - Target production path: `assets/images/andorra/approved/food-trinxat-amb-rosta.webp`

Current Taste state:

- FOOD01 — APPROVED / Escudella
- FOOD02 — APPROVED / Trinxat amb rosta
- FOOD03 — NEXT / Canelons a l’andorrana
- FOOD04 — NOT STARTED / Crema a l’andorrana

Visual Complete Gate remains blocked until FOOD03–04 are also user APPROVED and all four final WebP files are stored, fully decoded, dimension-checked and approved-folder hygiene passes.
