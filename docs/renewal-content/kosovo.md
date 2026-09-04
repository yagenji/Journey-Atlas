# Kosovo Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/kosovo-renewal`

This document is the locked PHASE 2 content design for the Kosovo Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Old Stone Bridge / Sinan Pasha Mosque / Prizren
- Hero lead
- Current eight scene locations and scene copy
- Current 1200×760 map geometry / markers / label offsets unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Signature Facts: keep all three current topics
- Beyond the Scenery: keep all six current topics
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Related Destinations: Albania / North Macedonia / Montenegro
- Theme taxonomy assignment: 地球の風景 / 時をたどる / 暮らしに出会う

## Country Profile — KEEP / current v3 display behavior

Visible profile remains exactly six items:

1. 首都 — プリシュティナ
2. 人口 — 約158万人（2025年）
3. 面積 — 約10,905 km²（日本の約2.9%）
4. 言語 — アルバニア語、セルビア語（ともに公用語）
5. 主な宗教 — イスラム教が多数、正教会・カトリックなど
6. 通貨 — ユーロ（EUR）

The Region item remains in the Country JSON for internal data consistency but is not shown by the shared current renderer.

Population source remains Kosovo Agency of Statistics 2025 estimate: 1,582,322.

## Signature Facts — KEEP 3

The current three topics cover geography / monetary system / medieval religious heritage and are sufficiently distinct.

1. **河川がつながる海域 — 3つ**
   - Kosovo river basins drain toward the Black Sea, Adriatic Sea and Aegean Sea.
2. **EU非加盟でも通貨はユーロ — 2002年から**
   - Kosovo uses the euro as a de facto domestic currency without a monetary agreement with the EU.
   - The German mark was widely used first; the cash changeover to the euro took place in 2002.
3. **「コソボの中世建造物群」の構成資産 — 4件**
   - Dečani Monastery / Patriarchate of Peć / Gračanica / Church of the Virgin of Ljevisa.

Do not replace these with a simple highest-point, UNESCO-count-only or population-density fact.

## Encounters — LOCKED 8

Replace the current Flija tag because FOOD01 will cover Flija directly.

1. プリス
2. チフテリ
3. フィリグリー
4. オダ
5. バザール
6. ラホヴェツワイン
7. コーヒーハウス
8. 山岳トレイル

These remain short tags and are not expanded into explanatory copy.

## Beyond the Scenery — KEEP 6

Keep the current six topics because they cover distinct non-scenic layers and do not duplicate the planned Taste dishes:

1. Ulpiana / Roman-period urban layer
2. Diaspora summer-return rhythm
3. 2008 independence declaration and state formation
4. Oda / elders' social tradition
5. Albanian + Serbian official-language public space
6. Traditional crafts including filigree, woodworking, saddlery, embroidery and pottery

Light Japanese wording normalization is permitted during implementation, but do not replace these topics without a new content audit.

## Travel Trivia — LOCKED 5

Replace the current Flija trivia because FOOD01 will cover Flija. Keep the remaining four and add Prishtina coffee culture.

1. **白いフェルト帽「プリス」を市場や文化行事で探す**
2. **二本弦の楽器「チフテリ」の音を聴く**
3. **ラホヴェツでは、葡萄畑とワイナリーを一緒に見る**
4. **祭りでは、綱引きや石投げなど昔からの競技を探してみる**
5. **プリシュティナでは、マキアートを飲みながら街の時間を見る**

Planned copy for item 5:

`プリシュティナではカフェが日常の社交空間として使われ、エスプレッソやマキアートを飲みながら長く話す光景に出会う。建築を見るだけでなく、席に座ることで現在の首都の生活リズムが見えてくる。`

Source: Kosova.Travel — Prishtina coffee culture.

## Taste — LOCKED

Kicker: `TASTE OF KOSOVO`  
Title: `コソボで食べたいもの`

Intro: `層を重ねる家庭料理、炭火の肉料理、プリズレンの煮込み、甘い焼き菓子から、バルカン内陸の食卓をたどる。`

### FOOD01 — フリア / Flija

**Copy**  
薄い生地とクリーム状の乳製品を何層にも重ね、上から熱した蓋を当てながら少しずつ焼き上げる料理。時間をかけて作る工程そのものが家庭や人の集まりと結びついている。

Planned asset: `food-flija.webp`

**DISH IDENTITY**
- large round layered baked batter dish
- many thin visible layers when one wedge is cut
- golden-brown radial baked pattern on the surface
- pale cream / light golden interior
- served as one dish, usually on a simple round plate or pan
- not pie, cake, pizza or omelette
- no extra grilled meat or separate side dishes

Sources:
- Kosova.Travel — Flija as a key Kosovo gastronomy item
- Kosovo cultural heritage / municipal gastronomy sources listing Flija as traditional food

### FOOD02 — チェバパ / Qebapa

**Copy**  
ひき肉を小さな筒状にまとめて炭火で焼く、街中のqebaptoreで出会いやすい肉料理。温かい平たいパンや玉ねぎと合わせ、短い食事でも土地の日常に入りやすい。

Planned asset: `food-qebapa.webp`

**DISH IDENTITY**
- several short skinless grilled minced-meat cylinders
- clearly charcoal-grilled brown exterior
- arranged together as one serving
- warm flatbread may be included as the traditional accompaniment
- a small amount of chopped raw onion is acceptable
- not a hamburger patty
- not meat on skewers
- not long sausage links

Sources:
- Kosova.Travel — Prizren culinary listing for traditional qebapa
- Visit Prizren — qebaptore restaurant category / local grill culture

### FOOD03 — タヴァ・プリズレニ / Tavë Prizreni

**Copy**  
プリズレンに結びつくオーブン料理。肉とナス、ピーマン、トマト、オクラ、玉ねぎなどを土鍋でゆっくり火入れし、街の歴史とオスマン由来の調理文化が重なる一皿として知られる。

Planned asset: `food-tave-prizreni.webp`

**DISH IDENTITY**
- deep earthenware casserole
- visible pieces of lamb or beef
- eggplant, green peppers, tomatoes, okra and onions
- rustic slow-baked stew / casserole texture
- warm red-brown and vegetable colors
- served directly in one clay baking vessel
- not soup
- not a cheese-and-egg gratin
- not a mixed platter

Sources:
- Visit Prizren — Tavë Prizreni listed among prominent traditional dishes
- ScienceDirect food-science reference describing Kosovo Prizren tava with meat and vegetables

### FOOD04 — テスピシュテ / Tespishte

**Copy**  
小麦粉やセモリナ系の生地を平たく焼き、切り込みを入れて甘いシロップを含ませる菓子。プリズレンでも親しまれ、バクラヴァとは違う密度のある焼き菓子として出会える。

Planned asset: `food-tespishte.webp`

**DISH IDENTITY**
- dense baked syrup-soaked pastry / cake
- low, flat slab or round baked form
- clearly scored diamond or geometric pattern
- golden-brown surface with light syrup sheen
- one portion may be cut to show dense interior
- not baklava with many flaky phyllo layers
- not flija with many thin pancake layers
- no decorative fruit, ice cream or unrelated pastries

Sources:
- Visit Prizren — Tespishte listed among local preferred sweets
- TasteAtlas reference used only to clarify visual dish identity and scoring pattern

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Flija
- FOOD02 — NOT STARTED / Qebapa
- FOOD03 — NOT STARTED / Tavë Prizreni
- FOOD04 — NOT STARTED / Tespishte

Do not add these planned image paths to the production Country JSON until all four images are user APPROVED, stored in the approved folder, fully decoded and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**プリシュティナとプリズレンを軸に近郊へ**

首都と歴史都市を一つずつ歩き、近郊の宗教建築を加えるくらいが現実的。例：プリシュティナ → グラチャニツァ → プリズレン。

### 5〜7日 / map
**西部の町とルゴヴァ渓谷までつなぐ**

主要都市にジャコヴァ、ペヤと山岳景観を加えると、都市・市場・修道院・峡谷の距離感が見えてくる。例：プリシュティナ → プリズレン → ジャコヴァ → ペヤ／ルゴヴァ渓谷。

### 8日以上 / compass
**東部と南部の高地まで広げる**

西部だけでなくノヴォ・ブルドやシャル山地側へ回ると、小さな国土の中にある地形と歴史の幅を追いやすい。例：プリシュティナ → ノヴォ・ブルド → プリズレン → ジャコヴァ → ペヤ／ルゴヴァ → ブロド／シャル山地。

Sources:
- Kosova.Travel destination pages for Prishtina / Prizren / Peja / Gjakova / Novo Brdo
- Current Country map / destination coordinates
- Trainkos 2026 timetable for the limited rail corridors

## Transport — LOCKED

Title: `バス・車・鉄道`  
Icon: `road`

Text:

`都市間は道路移動を軸にすると組みやすく、バスと車でプリシュティナ、プリズレン、ジャコヴァ、ペヤなどをつなげる。Trainkosは2026年にプリシュティナ―ペヤ、プリシュティナ―スコピエ方面の定期旅客列車を案内しているが、景勝地全体を鉄道だけでは結べない。ルゴヴァ、ミルシャ、シャル山地などは道路移動を組み合わせる。`

Travel Scale explains **how much of the country to combine for a given stay**. Transport explains **which modes are practical inside Kosovo**.

Sources:
- Trainkos — 2026 regular passenger timetables
- Kosovo Multi-Modal Transport Strategy 2030
- Kosovo road passenger transport framework

## For Whom — KEEP EXACTLY 3

1. 歴史都市と宗教建築を地続きで見たい人
2. 山と峡谷を歩きたい人
3. バルカン半島を陸路でつなぎたい人

No fourth persona.

## Travel Notes — LOCKED 3

### 1. 北部のセルビア国境付近は、最新の安全情報を確認する

日本の外務省は、レポサヴィッチ、ズヴェチャン、ズビン・ポトク、ミトロヴィツァ北など北部国境付近の一部地域をレベル2としている。北部へ向かう場合は、出発前に対象地域と最新情報を確認する。

### 2. 山岳部は距離ではなく、道路状況と所要時間で旅程を組む

ルゴヴァやシャル山地では、都市からの直線距離が短くても谷沿いや山道の移動になる。山を含む日は予定を詰めすぎず、天候と道路状況を確認できる余白を残す。

### 3. 修道院やモスクでは、礼拝の場としてのルールを先に確認する

宗教建築は観光施設である前に現在も使われる礼拝の場。服装、撮影可否、礼拝中の立ち入りなどは現地表示や係員の案内に従い、見学時間にも余裕を持たせる。

Source for item 1:
- Ministry of Foreign Affairs of Japan, Kosovo Overseas Safety Information — current hazard page checked 2026-09-04; Level 2 remains in force for specified northern municipalities.

## Current-standard implementation notes

After Visual Complete Gate:

- Keep `schemaVersion: 2`
- Keep current Hero / 8 scenes / map
- Keep Region in JSON; shared renderer hides it so visible Profile = 6
- Replace Encounters with the locked eight tags
- Replace Flija Travel Trivia with the locked Prishtina coffee-culture item
- Add the locked Taste section with four APPROVED image paths
- Add the locked Spain-format Travel Scale
- Change Transport title to Japanese and add `"icon": "road"`
- Apply the locked Travel Notes wording
- Refresh `sourcesVerifiedAt` and source metadata for Taste / Travel Scale / Transport / safety
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS
- Do not alter `atlasPublished:true` during renewal branch work

## Source lock — verified 2026-09-04

Use the following current/high-trust sources during implementation:

- Kosovo Agency of Statistics — 2025 population estimate 1,582,322
  - https://ask.rks-gov.net/?lang=en
- Ministry of Foreign Affairs of Japan — Kosovo basic data / Japan recognition
  - https://www.mofa.go.jp/mofaj/area/kosovo/data.html
- Ministry of Foreign Affairs of Japan — Kosovo overseas safety information
  - https://www.anzen.mofa.go.jp/info/pcinfectionspothazardinfo_180.html
- European Commission — The euro outside the euro area; Kosovo uses euro as de facto domestic currency without an EU monetary agreement
  - https://economy-finance.ec.europa.eu/euro/use-euro/euro-outside-euro-area_en
- Trainkos — 2026 regular passenger timetables
  - https://www.trainkos.com/sherbimet/transporti-i-udhetareve/orari-i-trenave/
- Government of Kosovo — Tourism Strategy 2024–2030
  - https://kryeministri.rks-gov.net/en/kosovo-tourism-strategy-2024-2030/
- Government of Kosovo — Multi-Modal Transport Strategy 2030
  - https://kryeministri.rks-gov.net/wp-content/uploads/2023/05/MULTIMODAL-TRANSPORT-STRATEGY-2030.pdf
- Kosova.Travel — destination / gastronomy / Prishtina coffee culture
  - https://kosovo.travel/
- Visit Prizren — cuisine listings including Flija, Tavë Prizreni and Tespishte
  - https://visit-prizren.com/en/rreth-prizrenit/
- Municipality of Peja — gastronomy / Rugova traditional food and games
  - https://peja.rks-gov.net/en/folklori/
- Existing official/high-trust source lock in the current Country JSON remains valid for area, language, religion, climate, drainage, Gračanica, Ulpiana, Novo Brdo, Mirusha, Sharri, Gadime, independence, diaspora and cultural heritage.

## PHASE 2 gate

Content design: **DONE / LOCKED**

Still pending:
- PHASE 3 retained Landscape technical image decision / decode-and-dimension validation
- Taste visual production and user approval
- approved-folder storage and verification
- Visual Complete Gate
- Country JSON implementation
- latest-main sync check
- automated QA
- browser visual QA
- final user approval
- production publication
