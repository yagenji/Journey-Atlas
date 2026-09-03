# Iceland — Published Country Renewal Audit

Date: 2026-09-03  
Wave: 1 / Reference v3  
Classification: **B — medium renewal**

## Decision summary

- Hero: **KEEP**
- 8-scene selection: **KEEP 8**
- Scene production assets: **S01 REGENERATE / S02–S08 NORMALIZE DECISION PENDING**
- Map: **KEEP**
- Country Profile: **KEEP**
- Signature Facts: **REWRITE 1**
- Encounters: **KEEP**
- Beyond the Scenery: **REWRITE 1 when Taste is added**
- Travel Trivia: **KEEP 5 / copy fix 1**
- Taste: **ADD**
- Travel Scale: **ADD**
- Seasons / Transport / For Whom / Travel Notes: **KEEP, source-check during implementation**
- Themes: **KEEP — 地球の風景 / 道の先へ**
- Sources: **CURRENT BASE + ADD sources for new sections**
- Hard image gate: **OFF until renewal is complete**

## Visual audit

### Hero
Seljalandsfoss remains a strong series-level entrance to Iceland and is technically above the renewed Hero minimum. Keep the current visual direction.

### 8 scenes
Current set:
1. Skógafoss
2. Jökulsárlón
3. Stuðlagil
4. Mývatn
5. Kirkjufell
6. Þingvellir
7. Geysir
8. Landmannalaugar

The current eight are locked for renewal. Seljalandsfoss in the Hero and Skógafoss in Scene 1 are both waterfalls, but that is not treated as unnecessary duplication: waterfalls are one of Iceland's defining landscape experiences, and the two locations provide distinct scenes and scales. Do not weaken the page merely to increase category dispersion.

### Asset gate
All eight raster-backed SVG scene assets fully decode, but none currently pass the renewed 1200×800 / 3:2 gate:
- seven scenes: 1200×750
- Landmannalaugar: 1000×625

Because Iceland is a visual reference, preserve the approved visual direction. First determine whether the existing visuals can be production-normalized without visible quality loss; regenerate only where normalization is not sufficient or the scene itself changes.

### S01 normalization decision — 2026-09-03

**Skógafoss: REGENERATE.**

The current scene is 1200×750 (aspect ratio 1.60), while the renewed target is 1200×800 / 3:2 (aspect ratio 1.50). A true normalization cannot preserve the approved composition exactly: fitting to 3:2 requires either horizontal crop, added canvas/padding, or geometric distortion. All three visibly alter the image, so S01 does not qualify as NORMALIZE under the renewal rule.

Keep the scene/location itself. Regenerate only the production asset at the current JOURNEY ATLAS visual direction and target geometry. Do not connect the replacement path to Country JSON until approval and the visual-complete gate.

## Content audit

### Add current sections — LOCKED
- `contentQaVersion: 1`
- `taste`
- `travelScale`

#### Taste
Kicker: `TASTE OF ICELAND`  
Title: `アイスランドで食べたいもの`  
Intro: `火山島の気候と海、牧畜、地熱がそのまま食文化につながっている。`

1. **キョーツーパ / Kjötsúpa**  
   羊肉と根菜を煮込む素朴なスープ。冷えた日に湯気の立つ一杯を食べると、羊の放牧が身近な国の食卓が見えてくる。  
   Planned asset: `food-kjotsupa.webp`

2. **スキール / Skyr**  
   乳製品のスキールは、朝食や軽食として身近な存在。濃厚さがありながら酸味は穏やかで、ベリーやグラノーラと合わせても食べられる。  
   Planned asset: `food-skyr.webp`

3. **ルーグブロイズ / Rúgbrauð**  
   甘みのある濃い色のライ麦パン。地熱地帯では熱い地面を利用して焼く方法もあり、地中の熱が料理までつながる。  
   Planned asset: `food-rugbraud.webp`

4. **ハルズフィスクル / Harðfiskur**  
   魚を干して作る保存食。小さく裂いてそのまま食べられ、長い海岸線と漁業の歴史が日常の軽食に残っている。  
   Planned asset: `food-hardfiskur.webp`

#### Travel Scale
Kicker: `DURATION`  
Title: `旅の目安日程`

- **3〜4日 — レイキャヴィークから南西部をめぐる**  
  首都を拠点にゴールデンサークルと南岸の滝まで。短い日程でも、地熱・断層・滝というアイスランドの入口をつなげられる。

- **5〜7日 — 南岸を氷河湖まで伸ばす**  
  レイキャヴィークからヴィーク、ヨークルスアゥルロゥン方面へ。移動距離を増やすより、滝や黒砂海岸、氷河で立ち止まる時間を残す。

- **8日以上 — リングロードで島を一周する**  
  国道1号を軸に北部や東部までつなぐ。公式観光情報でも一周には少なくとも7日が目安とされるため、天候や寄り道を考えると8日以上あると組みやすい。

### Signature Facts — LOCKED
Use the following three facts in the renewed page:
- **活火山系：約30** — Icelandic Meteorological Office describes about 30 active volcanic systems in Iceland.
- **氷河：国土の約10%** — keep the current glacier-scale fact.
- **地熱暖房：約90%** — Orkustofnun states that about 90% of the energy used for domestic heating comes from geothermal energy.

This replaces both the generic population-density fact and the less travel-visible renewable-electricity statistic with a more balanced set: geology / ice / everyday life.

### Beyond the Scenery — LOCKED
Replace the current FOOD item with:

**LIFE / ロパペイサと羊毛**  
羊毛のセーター、ロパペイサは土産物というだけではなく、寒冷な暮らしと手仕事が結びついたアイスランドの日常文化。町の毛糸店や工房をのぞくと、自然素材が服として暮らしに残っていることが分かる。

Points:
- 円形のヨーク模様を持つロパペイサは、歴史・手仕事・日常生活を象徴する存在として紹介されている
- 地方の毛糸店や工房では、アイスランド産ウールを使った製品に触れられる

### Travel Trivia
Keep the current five topics. Fix the doubled Japanese quotation mark in the hot-dog phrase so it reads:

「エイナ・メズ・オッル」

### Encounters
Current eight are concise tags and fit the current rule. Keep.

## Map

Technical map validation passes. Keep the current map unless later visual review finds label/readability problems after scene selection is locked.

## Why B

The page structure, Hero, eight-scene selection, map, themes and most editorial content remain useful. The medium-renewal classification remains because all eight Scene production assets need normalization/renewal and the current Taste / Travel Scale sections must be added.


## Content source lock — 2026-09-03

Use these sources when implementing the Country JSON.

- Active volcanic systems: Icelandic Meteorological Office — about 30 active volcanic systems.
  https://en.vedur.is/media/vedurstofan-utgafa-2020/VI_2020_004.pdf
- Glacier coverage: Icelandic Meteorological Office — glaciers cover about 10% of Iceland.
  https://en.vedur.is/volcanoes/volcanic-hazards/glacial-outburst/
- Geothermal domestic heating: Orkustofnun — about 90% of energy used for domestic heating comes from geothermal energy.
  https://orkustofnun.is/en/natural_resources/district_heating
- Icelandic food overview / kjötsúpa / skyr / dried fish: Visit Iceland.
  https://www.visiticeland.com/article/top-10-foods-in-iceland/
- Geothermal rye bread: Visit Iceland / Geothermal Park and Laugarvatn Fontana.
  https://www.visiticeland.com/service-provider/64635a5b38c85f000b7f41b9
  https://www.visiticeland.com/service-provider/6093f0b386700f000a2791a2
- Icelandic knitting / lopapeysa: Visit Iceland.
  https://www.visiticeland.com/article/icelandic-knitting/
- Ring Road / travel scale: Icelandic Road and Coastal Administration + Visit Iceland.
  https://www.vegagerdin.is/en/home/exploring-iceland/the-ring-road
  https://www.visiticeland.com/article/the-ring-road/

Do not use the pre-June-2026 exact 1,322 km Ring Road length as a current Signature Fact: a new Hornafjörður section opened on 24 June 2026 and shortened the Ring Road by 12 km. The Travel Scale copy therefore uses the route concept and minimum-day guidance rather than an obsolete exact length.


### S01 approval — 2026-09-03

**Skógafoss: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `skogafoss.webp`
- Final path: `assets/images/iceland/approved/skogafoss.webp`
- Do not regenerate without explicit user instruction.


### S02 approval — 2026-09-03

**Jökulsárlón: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `jokulsarlon.webp`
- Final path: `assets/images/iceland/approved/jokulsarlon.webp`
- Do not regenerate without explicit user instruction.


### S03 approval — 2026-09-03

**Stuðlagil Canyon: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `studlagil.webp`
- Final path: `assets/images/iceland/approved/studlagil.webp`
- Do not regenerate without explicit user instruction.


### S04 approval — 2026-09-03

**Mývatn: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `myvatn.webp`
- Final path: `assets/images/iceland/approved/myvatn.webp`
- Do not regenerate without explicit user instruction.


### S05 approval — 2026-09-03

**Kirkjufell: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `kirkjufell.webp`
- Final path: `assets/images/iceland/approved/kirkjufell.webp`
- Do not regenerate without explicit user instruction.


### S06 approval — 2026-09-03

**Þingvellir: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `thingvellir.webp`
- Final path: `assets/images/iceland/approved/thingvellir.webp`
- Do not regenerate without explicit user instruction.


### S07 approval — 2026-09-03

**Geysir Geothermal Area: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `geysir.webp`
- Final path: `assets/images/iceland/approved/geysir.webp`
- Do not regenerate without explicit user instruction.


### S08 approval — 2026-09-03

**Landmannalaugar: APPROVED.**

- Scene/location: KEEP
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Final filename: `landmannalaugar.webp`
- Final path: `assets/images/iceland/approved/landmannalaugar.webp`
- Do not regenerate without explicit user instruction.


### FOOD01 approval — 2026-09-03

**Kjötsúpa: APPROVED.**

- Dish: Kjötsúpa / キョーツーパ
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Visual reference: Spain approved Taste series
- Final filename: `food-kjotsupa.webp`
- Final path: `assets/images/iceland/approved/food-kjotsupa.webp`
- Do not regenerate without explicit user instruction.


### FOOD02 approval — 2026-09-03

**Skyr: APPROVED.**

- Dish: Skyr / スキール
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Visual reference: Spain approved Taste series
- Final filename: `food-skyr.webp`
- Final path: `assets/images/iceland/approved/food-skyr.webp`
- Do not regenerate without explicit user instruction.


### FOOD03 approval — 2026-09-03

**Rúgbrauð: APPROVED.**

- Dish: Rúgbrauð / ルーグブロイズ
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Visual reference: Spain approved Taste series
- Final filename: `food-rugbraud.webp`
- Final path: `assets/images/iceland/approved/food-rugbraud.webp`
- Do not regenerate without explicit user instruction.


### FOOD04 approval — 2026-09-03

**Harðfiskur: APPROVED.**

- Dish: Harðfiskur / ハルズフィスクル
- Visual state: APPROVED
- Target production geometry: 1200×800 / 3:2
- Visual reference: Spain approved Taste series
- Final filename: `food-hardfiskur.webp`
- Final path: `assets/images/iceland/approved/food-hardfiskur.webp`
- Do not regenerate without explicit user instruction.


## Approved asset packaging — 2026-09-03

The eight renewed Scene visuals and four Taste visuals have been exported from their approved 1536×1024 source generations to final 1200×800 / 3:2 WebP files without cropping or distortion.

Local technical verification:
- 12 / 12 files: complete decode PASS
- 12 / 12 files: 1200×800 PASS
- 12 / 12 files: WebP PASS
- visual state: user APPROVED for all 12
- Hero remains KEEP at its existing production path

Production gate remains **BLOCKED** until the final WebP binaries are physically present in:
`assets/images/iceland/approved/`

Do not connect the new Scene or Taste paths to `data/countries/iceland.json` until repository presence and approved-folder hygiene are verified.


## Travel Planning alignment — 2026-09-03

Human preview review found that Iceland's Travel Scale looked denser than Spain because of longer item headings/copy. The shared Country Template and CSS are already identical, so no country-specific style change is required.

Adjusted only Iceland content density:
- 3〜4日: `首都を拠点に南西部へ`
- 5〜7日: `南岸を氷河湖まで`
- 8日以上: `リングロードで島を一周`
- Transport title changed from English `RING ROAD / ROAD TRIP` to Japanese `レンタカー・リングロード`
- Transport icon explicitly set to `road`
