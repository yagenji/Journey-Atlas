> **STATUS — COMPLETED (2026-09-05)**  
> This file is retained as a historical execution/plan record. The current authoritative renewal status is `data/country-renewal-status.json`: content / visual / map / sources = `DONE`, QA = `PASS`, production = `LIVE_CURRENT`. Any `PENDING`, `Still pending`, or pre-publish notes below describe an earlier checkpoint and are not current tasks.

# Croatia Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/croatia-renewal`

This document is the locked PHASE 2 content design for the Croatia Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Srđ / Dubrovnik Old City
- Hero lead
- Current eight scene locations and scene copy
- Current 1200×760 map geometry / markers / offsets unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Signature Facts: keep all three current topics
- Encounters: keep the current eight tags
- Beyond the Scenery: keep all six current topics
- Travel Trivia: keep all five current topics
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Travel Notes: keep the current three items
- Related Destinations: Slovenia / Montenegro / Italy
- Theme taxonomy assignment: 街を歩く / 時をたどる / 海の世界へ

## Signature Facts — KEEP 3

The current three topics are distinct and travel-relevant:

1. **島・小島・岩礁 — 1,244**
2. **ネクタイの原型がパリで注目 — 1630年**
3. **ユーロ圏・シェンゲン — 2023年**

Do not replace them with generic highest-point, heritage-count or national-park-count facts.

## Encounters — KEEP 8

1. ブーラ
2. 朝市
3. カフェテラス
4. ラベンダー
5. パグチーズ
6. ペカ料理
7. タンブリツァ
8. グラゴル文字

These remain short encounter tags. The planned Taste dishes are deliberately different, so the current Encounter list does not become a duplicate of Taste.

## Beyond the Scenery — KEEP 6

Keep the current six topics because they cover distinct layers beyond the landscape and do not duplicate the planned Taste dishes:

1. Diocletian's Palace reused as a living city
2. Klapa multipart singing
3. Croatian dialect diversity: Štokavian / Kajkavian / Čakavian
4. Dry-stone construction
5. Pelješac Bridge and territorial connection
6. Lipizzan horse-breeding culture in eastern Croatia

## Travel Trivia — KEEP 5

1. Zagreb Funicular — 66 m
2. Zadar Sea Organ — 35 pipes
3. Istrian truffle hunting
4. Northern Croatian gingerbread hearts
5. Sinjska Alka

No planned Taste dish duplicates these five topics.

## Taste — LOCKED

Kicker: `TASTE OF CROATIA`  
Title: `クロアチアで食べたいもの`

Intro: `北部のチーズ料理から、アドリア海のイカ墨、ダルマチアの煮込み、冬の揚げ菓子まで、地域差の大きい食文化を4皿からたどる。`

### FOOD01 — シュトゥルクリ / Štrukli

**Copy**  
薄く伸ばした生地にフレッシュチーズと卵のフィリングを包む、ザゴリェ地方とザグレブで身近な料理。茹でる形と焼く形があり、Taste画像では表面に軽く焼き色のついた焼きシュトゥルクリを使う。

Planned asset: `food-strukli.webp`

**DISH IDENTITY**
- Croatian cheese-filled pastry / baked štrukli
- thin dough rolled around fresh cheese filling
- several short rectangular rolled pieces as one serving
- pale cream surface with light golden browning
- shallow simple ceramic baking dish or plate
- not lasagna, not puff pastry, not sweet strudel

Source: Zagreb Tourist Board / InfoZagreb — Štrukli gastronomy and preparation pages.

### FOOD02 — ブラックリゾット / Crni rižot

**Copy**  
イカやコウイカの墨で米を黒く仕上げる、アドリア海沿岸で出会いやすい魚介のリゾット。見た目の黒さそのものが、内陸とは異なる海の食文化を端的に伝える。

Planned asset: `food-crni-rizot.webp`

**DISH IDENTITY**
- Croatian black risotto
- glossy black rice from cuttlefish or squid ink
- small visible pieces of cuttlefish or squid
- moist risotto texture, not dry fried rice
- served in a shallow simple bowl or plate
- no pasta, no paella pan, no oversized seafood garnish

Source: Dubrovnik Tourist Board; Split-Dalmatia County Tourist Board.

### FOOD03 — パシュティツァダ / Pašticada

**Copy**  
牛肉を時間をかけて煮込み、濃いソースとニョッキを合わせるダルマチアの料理。魚介だけではない沿岸部の家庭料理と祝いの食卓を見せる一皿になる。

Planned asset: `food-pasticada.webp`

**DISH IDENTITY**
- Dalmatian slow-cooked beef
- tender sliced or thick-cut beef in a rich dark brown sauce
- small potato gnocchi served alongside or partly under the sauce
- sauce is glossy and deep brown, not tomato-red
- one plated main dish
- not generic beef stew in a soup bowl

Source: Split-Dalmatia County Tourist Board / Visit Split.

### FOOD04 — フリトゥレ / Fritule

**Copy**  
小さく丸めた生地を揚げ、粉砂糖をかけるダルマチアの菓子。特にクリスマス期の食卓や街角と結びつき、季節の行事から暮らしへ関心を広げられる。

Planned asset: `food-fritule.webp`

**DISH IDENTITY**
- small irregular round fried dough balls
- natural golden-brown exterior
- lightly dusted with powdered sugar
- 5–7 pieces as one serving
- raisins may be subtly visible but are not decorative props
- not doughnuts with holes, not churros, not cream-filled pastries

Source: Visit Split — Christmas / gastronomy guidance.

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Štrukli
- FOOD02 — NOT STARTED / Crni rižot
- FOOD03 — NOT STARTED / Pašticada
- FOOD04 — NOT STARTED / Fritule

Do not add these planned image paths to the production Country JSON until all four images are user APPROVED, stored in the approved folder, fully decoded, dimension-checked, and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**スプリトを拠点に近郊へ**

一つの都市に滞在し、近郊の歴史都市まで加えるくらいが現実的。例：スプリト＋トロギール。

### 5〜7日 / map
**首都・湖群・ダルマチアをつなぐ**

内陸から海岸へ南下すると、都市、カルスト湖、アドリア海岸の違いを一度の旅で比べられる。例：ザグレブ → プリトヴィツェ湖群 → スプリト。

### 8日以上 / compass
**島を加えて南部まで旅を広げる**

海岸都市だけでなく島泊を加えると、クロアチアの細長い国土とアドリア海の距離感が見えてくる。例：ザグレブ → プリトヴィツェ湖群 → スプリト → フヴァル → ドゥブロヴニク。

Source logic: current HŽ Passenger Transport timetable for Zagreb–Split rail options; Jadrolinija current ferry schedules for island connections. Exact departures remain date-dependent.

## Transport — LOCKED

Title: `鉄道・都市間バス・フェリー・車`  
Icon: `road`

Text:

`ザグレブと内陸では鉄道も使えるが、海岸都市間は都市間バスや車を組み合わせやすい。島へ渡る区間はJadrolinijaなどのフェリー・高速船が旅程の一部になり、同じ距離でも季節と接続で所要時間が変わる。南北に長い国土では、沿岸と島の接続時間まで含めて移動を組む。`

Travel Scale explains **how far a given stay can realistically reach**. Transport explains **which modes are used to move through Croatia**.

Sources: HŽ Putnički prijevoz current 2025/2026 timetable; Jadrolinija current sailing schedules.

## For Whom — KEEP EXACTLY 3

1. 海岸と島を移動しながら見たい人
2. 自然と歴史を同じ地図で追いたい人
3. 有名な海岸以外のクロアチアも知りたい人

No fourth persona.

## Travel Notes — KEEP 3

1. 島へ行く日は、便名だけでなく発着港まで確認する
2. プリトヴィツェは入口と散策ルートを先に決める
3. 夏の旧市街歩きは、朝と夕方を使う

The first note is retained because it is operationally specific to ferry ports and seasonal island services; it is not a restatement of the general Transport section.

## Current-standard implementation notes

After Visual Complete Gate:

- Keep `schemaVersion: 2`
- Keep current Hero / 8 scenes / map
- Add the locked Taste section with four APPROVED image paths
- Add the locked Spain-format Travel Scale
- Change Transport title to Japanese and add `"icon": "road"`
- Change SEO copy from the ambiguous `地図と9つの景観` wording to a current-system expression centered on Hero + 8 scenes
- Refresh `sourcesVerifiedAt` and source metadata for Taste / Travel Scale / Transport
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS
- Do not alter `atlasPublished:true` during renewal branch work

## Source lock — verified 2026-09-04

Use these current/high-trust sources during implementation:

- Zagreb Tourist Board / InfoZagreb — Štrukli is an authentic Zagreb / Zagorje dish; it can be boiled or baked.
  - https://www.infozagreb.hr/en/about-zagreb/basic-facts
  - https://www.infozagreb.hr/en/explore-zagreb/sightseeing/gastro-tours/culinary-workshop-preparation-of-strukli
- Dubrovnik Tourist Board — black risotto gets its appearance from cuttlefish or squid ink.
  - https://visitdubrovnik.hr/gastronomy/
- Split-Dalmatia County Tourist Board — black risotto, peka and pašticada are characteristic Dalmatian dishes; pašticada is slow-cooked beef commonly served with gnocchi.
  - https://www.dalmatia.hr/what-to-see-in-croatia-on-your-first-visit-a-guide-to-central-dalmatia/
  - https://www.dalmatia.hr/with-20c-in-winter-and-autumn-dalmatia-is-an-ideal-off-season-escape/
- Visit Split — fritule are small fried dough balls associated particularly with the Christmas season; pašticada is also part of Dalmatian holiday cuisine.
  - https://visitsplit.com/en/4916/codfish-imported-holiday-king
  - https://visitsplit.com/en/4406/christmas-split-style
- HŽ Putnički prijevoz — current 2025/2026 timetable is in force through 12 December 2026, with September 2026 changes published.
  - https://hzpp.hr/en/timetable
- Jadrolinija — current ferry / fast-ship schedules; sailing schedules are subject to change.
  - https://www.jadrolinija.hr/en
  - https://www.jadrolinija.hr/en/search-buy-ticket
- Existing official/high-trust source lock in the current Croatia Country JSON remains valid for population, area, currency, religion, scenes, Signature Facts, Beyond, Trivia and Travel Notes unless later source QA finds a change.

## PHASE 2 gate

Content design: **DONE / LOCKED**

Still pending:
- PHASE 3 retained Landscape technical decision: complete decode / dimensions / visual consistency
- Taste visual production and user approval
- approved-folder storage and asset verification
- Visual Complete Gate
- Country JSON implementation
