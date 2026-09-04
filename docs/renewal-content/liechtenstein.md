# Liechtenstein Renewal — Locked Content Specification

Date: 2026-09-04  
Branch: `country/liechtenstein-renewal`

This document is the locked PHASE 2 content design for the Liechtenstein Reference v3 renewal. It does not connect unapproved Taste images to the production Country JSON.

## Keep unchanged

- Hero location / concept: Red House / Herawingert / Vaduz Castle
- Hero lead
- Current eight scene locations and scene copy
- Current 1200×760 map geometry / markers / label offsets unless later browser QA finds a readability issue
- Country Profile facts, with Region retained in JSON and hidden by the shared renderer so the visible profile remains exactly six items
- Signature Facts: keep all three current topics
- Travel Trivia: keep all five current topics
- Beyond the Scenery: keep all six current topics
- Seasons: keep all four current items
- For Whom: keep the current three personas
- Related Destinations: Switzerland / Austria / Luxembourg
- Theme taxonomy assignment: 地球の風景 / 道の先へ

## Signature Facts — KEEP 3

The current three facts cover geography / topography / cross-border labour and are sufficiently distinct.

1. **国土の最大延長 — 24.6 × 12.4 km**
2. **標高差 — 430 → 2,599 m**
3. **国内就業者の越境通勤 — 57.4%（2024年末）**

Do not replace the elevation fact with a simple highest-point fact. Its value is the approximately 2,169 m vertical range inside a 160 km² country.

## Encounters — LOCKED 8

Replace the current list with a slightly broader set that avoids over-concentrating on generic alpine labels.

1. アルプス
2. ライン川
3. 山城
4. ヴァルザー文化
5. 葡萄畑
6. 湿地
7. ハイキング
8. 小さな首都

These remain short tags and are not expanded into explanatory copy.

## Beyond the Scenery — KEEP 6

Keep the current six topics because they cover distinct non-scenic layers and do not duplicate the planned Taste dishes:

1. Walser settlement / Triesenberg
2. Philately since 1912
3. Swiss customs territory since 1923
4. Women’s suffrage introduced in 1984
5. Constitutional Prince + people / direct-democratic structure
6. Herawingert vineyard / wine culture

Light Japanese wording normalization is permitted during implementation, but do not replace these topics without a new content audit.

## Travel Trivia — KEEP 5

1. 二重内陸国は世界に2か国だけ
2. 75kmの道が全11自治体をつなぐ
3. 1901年の木橋を歩いてスイスへ渡れる
4. 国民の日は毎年8月15日
5. 1868年以来、自国軍を持っていない

No Taste duplication is introduced.

## Taste — LOCKED

Kicker: `TASTE OF LIECHTENSTEIN`  
Title: `リヒテンシュタインで食べたいもの`

Intro: `チーズの山料理、農家の主食、秋のスープ、季節の揚げ菓子から、小国の食卓をたどる。`

### FOOD01 — ケーゼクネップフレ / Käsknöpfle

**Copy**  
小さな生地をゆで、チーズを重ねて香ばしい玉ねぎをのせる代表料理。多くのレストランで見つけやすく、伝統的にはアップルソースを添えて食べる。

Planned asset: `food-kaesknoepfle.webp`

**DISH IDENTITY**
- 小さく不揃いなKnöpfle状の生地
- 溶けたチーズが全体に絡む
- 表面に焼き色のある玉ねぎ
- 伝統的なアップルソースは少量の付け合わせとして可
- 長い麺、マカロニ、グラタンではない
- パンやサラダなど別料理を追加しない

Source: Liechtenstein Tourism — Käsknöpfle / Käsknöpfle in Liechtenstein

### FOOD02 — リーベル / Ribel

**Copy**  
トウモロコシ粉を牛乳と水で蒸らし、バターで細かく香ばしく炒る素朴な料理。かつて農家や暮らしを支えた主食で、現在は伝統料理として受け継がれている。

Planned asset: `food-ribel.webp`

**DISH IDENTITY**
- 細かくほぐれた黄金〜淡褐色のトウモロコシ粉
- 乾いた粉ではなく、バターで炒った粒状・そぼろ状
- 浅い皿または小さな鋳物風の器
- ポレンタの一枚固めや粥ではない
- 肉料理・パスタではない
- 装飾的な果物やハーブを散らさない

Source: Liechtenstein Tourism — Ribel

### FOOD03 — 大麦スープ / Gerstensuppe

**Copy**  
大麦、野菜、燻製豚肉などをゆっくり煮込む、秋に親しまれる温かいスープ。大鍋で準備しやすく、祭りや人が集まる場にも向く、山地の暮らしに近い一皿。

Planned asset: `food-gerstensuppe.webp`

**DISH IDENTITY**
- 淡いクリーム〜ベージュ色の温かいスープ
- 大麦の粒が明確に見える
- 小さく切ったにんじん、リーキ、燻製豚肉
- シンプルなボウルで提供
- ミネストローネのような赤いトマトスープではない
- パン、ワイン、余計なハーブ飾りを追加しない

Source: Liechtenstein Tourism — Gerstensuppe

### FOOD04 — ファスナハツキュアヒレ / Fasnachtsküachle

**Copy**  
薄く伸ばした生地を油で揚げ、粉砂糖をかけるカーニバル期の菓子。Fasnachtの「第5の季節」と結びつき、食から年間行事へ興味を広げられる。

Planned asset: `food-fasnachtskueachle.webp`

**DISH IDENTITY**
- 薄く丸い、やや不規則な揚げ生地
- 表面に軽い膨らみ・気泡
- 自然な黄金色
- 粉砂糖を控えめにまぶす
- ドーナツ状の厚い輪ではない
- クリーム、ジャム、果物などの追加トッピングなし

Source: Liechtenstein Tourism — Fasnachtsküachle

### Taste visual state after PHASE 2

- FOOD01 — NOT STARTED / Käsknöpfle
- FOOD02 — NOT STARTED / Ribel
- FOOD03 — NOT STARTED / Gerstensuppe
- FOOD04 — NOT STARTED / Fasnachtsküachle

Do not add these planned image paths to the production Country JSON until all four images are user APPROVED, stored in the approved folder, fully decoded and the Visual Complete Gate passes.

## Travel Scale — LOCKED / Spain format

Kicker: `DURATION`  
Title: `旅の目安日程`  
Intro: empty

### 3〜4日 / city
**ファドゥーツを拠点に谷と山へ**

首都とライン川沿いを歩き、LIEmobilで山腹や高地を加えるくらいが現実的。例：ファドゥーツ＋旧ライン橋 → トリーゼンベルク → マルブン。

### 5〜7日 / map
**南北の集落と山地をつなぐ**

バスと徒歩で南部から北部へ移ると、城、斜面集落、湿地まで短距離で景観が切り替わる。例：バルザース → ファドゥーツ → トリーゼンベルク／マルブン → ルッゲル。

### 8日以上 / compass
**Liechtenstein Trailを歩いて国全体へ**

75km・5ステージのLiechtenstein Trailを軸に、マルブンの山歩きを別日に加えると、小国を急がず地形と集落の変化で理解できる。例：バルザース → トリーゼンベルク → ファドゥーツ → ネンデルン → ルッゲル → シャーンヴァルト＋マルブン。

Source: Liechtenstein Tourism — Liechtenstein Trail / walking stages

## Transport — LOCKED

Title: `バス・徒歩・自転車`  
Icon: `road`

Text:

`国内移動の軸はLIEmobil。ファドゥーツ、南北の集落、トリーゼンベルク、マルブンへバスでつなぎ、近距離は徒歩や自転車を組み合わせる。鉄道で入る場合はスイスのザルガンス／ブーフス、またはオーストリアのフェルトキルヒでバスへ接続する。`

Travel Scale explains **how much of the country to combine for a given stay**. Transport explains **which modes are practical inside and on approach to Liechtenstein**.

Source: Liechtenstein Tourism — Travel & mobility; LIEmobil 2026 timetable

## For Whom — KEEP EXACTLY 3

1. 小さな国で地形の落差を見たい人
2. 国境を越える日常に興味がある人
3. 歩いて一国の輪郭をつかみたい人

No fourth persona.

## Travel Notes — LOCKED 3

### 1. ファドゥーツ城は内部見学できない

現在も公爵家の居所で、一般公開されていない。城そのものへ入る計画ではなく、ファドゥーツ中心部からの徒歩ルートと外観・ライン谷の眺めを組み合わせる。

### 2. フュルステンシュタイクは晩春でも残雪を確認する

ドライ・シュヴェステルンとフュルステンシュタイクの山道では、晩春まで雪が残る可能性がある。出発前に登山道の状況を確認し、雪がある場合は装備とルート判断を優先する。

### 3. 車で入るなら周辺国のヴィニェットを確認する

スイスまたはオーストリアの高速道路を使って入国する場合は、各国の高速道路通行証（ヴィニェット）が必要。リヒテンシュタイン国内だけでなく、往復の進入ルートまで含めて確認する。

This replaces the current duplicated wording `高速道路通行証（高速道路通行証）`.

## Current-standard implementation notes

After Visual Complete Gate:

- Keep `schemaVersion: 2`
- Keep current Hero / 8 scenes / map
- Replace Encounters with the locked eight tags
- Add the locked Taste section with four APPROVED image paths
- Add the locked Spain-format Travel Scale
- Change Transport title to Japanese and add `"icon": "road"`
- Apply the Travel Note 3 wording correction
- Refresh `sourcesVerifiedAt` and source metadata for Taste / Travel Scale / Transport
- Keep Theme assignment only in `data/theme-taxonomy.json`
- Do not add country-specific CSS or JS
- Do not alter `atlasPublished:true` during renewal branch work

## Source lock — verified 2026-09-04

Use the following current/high-trust sources during implementation:

- Liechtenstein Tourism — Gastronomy overview: Käsknöpfle and Ribel are identified as national dishes.
  - https://en.tourismus.li/entdecken/ganzjaehrig/gastronomie/uebersicht.html
- Käsknöpfle:
  - https://en.tourismus.li/rezepte/detail/kasknopfle-dc0e5593-abe1-418e-943e-a897c7979b3e.html
  - https://en.tourismus.li/kaesknoepfle-essen-in-liechtenstein.html
- Ribel:
  - https://en.tourismus.li/rezepte/detail/ribel-7c5968ff-9518-486d-9bb6-bfca9d1382f4.html
- Gerstensuppe:
  - https://en.tourismus.li/rezepte/detail/gerstensuppe-4b93d8ee-008c-4e6d-8baa-cfd50d29382e.html
- Fasnachtsküachle:
  - https://en.tourismus.li/rezepte/detail/fasnachtskuachle-0973cb88-95d4-4277-8c57-55746683b8c6.html
- Travel & mobility / LIEmobil access:
  - https://en.tourismus.li/reiseland/anreise-mobilitaet.html
- Liechtenstein Trail / five walking stages:
  - https://en.tourismus.li/entdecken/liechtenstein-weg/gehen.html
- LIEmobil 2026 timetable:
  - https://liemobil.li/static/LIEmobil_Gesamtesfahrplan-cb87dd5927873f50abe90c1a24c9747a.pdf
- Existing official/high-trust source lock in the current Country JSON remains valid for population, area, employment, state system, customs relationship, National Day, military history and existing scenes.

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


## PHASE 3 — Landscape Image Decision

Date: 2026-09-04

### Hero

**KEEP**

- Current asset: `assets/images/liechtenstein/approved/hero-vaduz-castle-vineyard.png`
- Current concept remains Red House / Herawingert / Vaduz Castle.
- Prior publication review explicitly kept the approved Hero unchanged.
- Latest-main all-published image audit fully decodes this referenced raster and reports no finding.
- PNG format itself is supported by the current validator; format-only conversion is not justified.

### Scene 01 — Government Quarter / Vaduz

**KEEP**  
`assets/images/liechtenstein/approved/vaduz-government-district.png`

### Scene 02 — Old Rhine Bridge / Vaduz–Sevelen

**KEEP**  
`assets/images/liechtenstein/approved/old-rhine-bridge-vaduz.png`

### Scene 03 — Gutenberg Castle / Balzers

**KEEP**  
`assets/images/liechtenstein/approved/gutenberg-castle-balzers.png`

### Scene 04 — Triesenberg / Walser village

**KEEP**  
`assets/images/liechtenstein/approved/triesenberg-walser-village.png`

### Scene 05 — Peace Chapel / Malbun

**KEEP**  
`assets/images/liechtenstein/approved/malbun-peace-chapel-winter.png`

### Scene 06 — Sareis / Malbuntal

**KEEP**  
`assets/images/liechtenstein/approved/sareis-ridge-malbun.png`

### Scene 07 — Ruggeller Riet / Ruggell

**KEEP**  
`assets/images/liechtenstein/approved/ruggeller-riet-iris.png`

### Scene 08 — Dux / Drei Schwestern

**KEEP**  
`assets/images/liechtenstein/approved/drei-schwestern-dux.png`

### Technical image QA evidence

Latest current-main validation run: **33842921093**

- Validate country data: PASS
- All-published image audit: PASS
- 28 published Country Pages
- 320 raster payloads fully decoded
- zero image findings
- validator checks:
  - complete raster verify + load
  - Hero minimum 1200×760 and landscape orientation
  - Scene minimum 1200×800
  - Scene 3:2 aspect ratio
  - map SVG 1200×760
  - approved-folder hygiene

The renewal branch is based on the same current main and has not changed any Liechtenstein landscape asset or Country image reference. Therefore the result applies directly to the retained Liechtenstein Hero + eight Scene assets.

### NORMALIZE decision

**NONE**

No technical failure requires resize, crop, format conversion or recompression. Do not normalize solely because the retained assets are PNG.

### REGENERATE decision

**NONE**

No Hero or Scene has a current selection, visual-history or technical-QA basis for regeneration.

### Taste visual decision

Taste is new content and requires four **NEW INDEPENDENT IMAGES**:

1. FOOD01 Käsknöpfle — ADD / NOT STARTED
2. FOOD02 Ribel — ADD / NOT STARTED
3. FOOD03 Gerstensuppe — ADD / NOT STARTED
4. FOOD04 Fasnachtsküachle — ADD / NOT STARTED

Target for each final asset:

- 1200×800
- exact 3:2
- WebP
- Spain Taste Global Visual Language
- no text / map / UI inside image
- each food generated independently, one image at a time

## PHASE 3 gate

Landscape decision: **DONE / LOCKED**

- Hero: KEEP
- Scene 01–08: KEEP
- NORMALIZE: 0
- REGENERATE: 0
- Map: KEEP
- Taste: 4 new images required / NOT STARTED
- `hardImageGate`: remains **false**

Next phase: **VISUAL PRODUCTION — Taste FOOD01 → FOOD04**.


## Taste approvals — 2026-09-04

All four Liechtenstein Taste images were user APPROVED as one review batch.

- FOOD01 **Käsknöpfle** — APPROVED
  - Final filename: `food-kaesknoepfle.webp`
  - Target production path: `assets/images/liechtenstein/approved/food-kaesknoepfle.webp`
- FOOD02 **Ribel** — APPROVED
  - Final filename: `food-ribel.webp`
  - Target production path: `assets/images/liechtenstein/approved/food-ribel.webp`
- FOOD03 **Gerstensuppe** — APPROVED
  - Final filename: `food-gerstensuppe.webp`
  - Target production path: `assets/images/liechtenstein/approved/food-gerstensuppe.webp`
- FOOD04 **Fasnachtsküachle** — APPROVED
  - Final filename: `food-fasnachtskueachle.webp`
  - Target production path: `assets/images/liechtenstein/approved/food-fasnachtskueachle.webp`

Do not regenerate any of these four images without explicit user instruction.

Repository storage / final WebP normalization / complete decode / dimension verification remain pending. Visual Complete Gate must remain blocked until those checks pass.


## Asset handoff / repository verification — 2026-09-04

User-uploaded Taste assets were verified in `assets/images/liechtenstein/approved/`.

Final assets:

- `food-kaesknoepfle.webp` — 1200×800 / WebP / full local decode PASS / Git blob `e8cc7a31b60dfdb1fceacefe3a16393c915b8761`
- `food-ribel.webp` — 1200×800 / WebP / full local decode PASS / Git blob `8b0ec3ba36d6f04d37ccf7d99b7aa29eb82a0d30`
- `food-gerstensuppe.webp` — 1200×800 / WebP / full local decode PASS / Git blob `39a9b23f55af21bc3aff27e77e52add03b8ff346`
- `food-fasnachtskueachle.webp` — 1200×800 / WebP / full local decode PASS / Git blob `e00a7c147e8b0083c60ea8b0119e250a34024722`

The GitHub repository blob SHAs exactly match the locally approved 1200×800 masters.

Approved-folder hygiene:

- Hero: 1
- Scenes: 8
- Taste: 4
- Total production assets: 13
- draft / temporary / placeholder / .b64 / parts / rejected assets: 0

## Visual Complete Gate — PASS

- Hero: KEEP / approved existing asset
- Scene 01–08: KEEP / approved existing assets
- Map: KEEP
- FOOD01 Käsknöpfle: APPROVED / stored / verified
- FOOD02 Ribel: APPROVED / stored / verified
- FOOD03 Gerstensuppe: APPROVED / stored / verified
- FOOD04 Fasnachtsküachle: APPROVED / stored / verified
- Taste final geometry: 1200×800 / exact 3:2 / WebP
- Complete local decode: PASS 4/4
- Repository Git blob match: PASS 4/4
- Approved-folder hygiene: PASS

Visual production is complete. Country JSON implementation is now unblocked.

`hardImageGate` remains false until the approved Taste paths are connected to the Country JSON and renewed-country validation can enforce them.
