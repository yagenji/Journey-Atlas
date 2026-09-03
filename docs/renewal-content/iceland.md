# Iceland Renewal — Locked Content Specification

Date: 2026-09-03  
Branch: `country/iceland-renewal`

This document is the locked content design for the Iceland renewal. It does not connect unapproved replacement images to production.

## Keep unchanged

- Hero location / concept: Seljalandsfoss
- Current eight scene locations
- Map
- Country Profile six visible facts
- Encounters eight tags
- Themes: 地球の風景 / 道の先へ
- Current Seasons / Transport / For Whom / Travel Notes, subject only to source freshness checks during implementation

## Signature Facts

1. **活火山系 — 約30**
   - Note: 約30の活動的な火山系がある。火山、地熱、溶岩原が一つの島に連続して現れる背景になる。
   - Source: Icelandic Meteorological Office

2. **氷河 — 国土の約10%**
   - Note: 氷河は島の高地を広く覆い、火山と氷が同じ場所に重なることで氷河湖やヨークルフロイプなど独特の地形現象を生む。
   - Source: Icelandic Meteorological Office

3. **地熱暖房 — 約90%**
   - Note: 家庭暖房に使われるエネルギーの約90%が地熱由来。温泉だけでなく、地中の熱が日常の暮らしを支えている。
   - Source: Orkustofnun

## Beyond the Scenery replacement

Replace the current FOOD card with:

**LIFE / 暮らしに出会う**  
**ロパペイサと羊毛**

羊毛のセーター、ロパペイサは土産物というだけではなく、寒冷な暮らしと手仕事が結びついたアイスランドの日常文化。町の毛糸店や工房をのぞくと、自然素材が服として暮らしに残っていることが分かる。

- 円形のヨーク模様を持つロパペイサは、歴史・手仕事・日常生活を象徴する存在として紹介されている
- 地方の毛糸店や工房では、アイスランド産ウールを使った製品に触れられる

## Taste

**TASTE OF ICELAND**  
**アイスランドで食べたいもの**

Intro: 火山島の気候と海、牧畜、地熱がそのまま食文化につながっている。

1. **キョーツーパ / Kjötsúpa**
   羊肉と根菜を煮込む素朴なスープ。冷えた日に湯気の立つ一杯を食べると、羊の放牧が身近な国の食卓が見えてくる。
   Asset: `food-kjotsupa.webp`

2. **スキール / Skyr**
   乳製品のスキールは、朝食や軽食として身近な存在。濃厚さがありながら酸味は穏やかで、ベリーやグラノーラと合わせても食べられる。
   Asset: `food-skyr.webp`

3. **ルーグブロイズ / Rúgbrauð**
   甘みのある濃い色のライ麦パン。地熱地帯では熱い地面を利用して焼く方法もあり、地中の熱が料理までつながる。
   Asset: `food-rugbraud.webp`

4. **ハルズフィスクル / Harðfiskur**
   魚を干して作る保存食。小さく裂いてそのまま食べられ、長い海岸線と漁業の歴史が日常の軽食に残っている。
   Asset: `food-hardfiskur.webp`

## Travel Scale

**DURATION**  
**旅の目安日程**

### 3〜4日 — 首都を拠点に南西部へ
レイキャヴィークを拠点に、ゴールデンサークルと南岸の滝を組み合わせる。短い日程なら移動範囲を絞り、地熱・断層・滝をつなぐ。

### 5〜7日 — 南岸を氷河湖まで
ヴィークを経てヨークルスアゥルロゥン方面へ。滝、黒砂海岸、氷河をつなぎながら、各地で立ち止まる時間も残す。

### 8日以上 — リングロードで島を一周
国道1号を軸に北部・東部までつなぐ。天候や寄り道を考えると、少なくとも一週間より余裕を持たせると組みやすい。

## Trivia copy fix

Change:
`「「エイナ・メズ・オッル」」`

to:
`「エイナ・メズ・オッル」`

## JSON implementation notes

- Add `contentQaVersion: 1`
- Do not add `taste` image paths to the production Country JSON until all four food images are APPROVED.
- Do not connect renewed Scene assets until the visual-complete gate is passed.
- Add/refresh the source keys only at implementation, using the locked source list in the audit document.


## Transport wording update — 2026-09-03

- Title: `レンタカー・リングロード`
- Keep the shared Spain Reference v3 travel-planning component; do not add Iceland-specific CSS.
- Travel Scale titles are shortened to match the Spain reference information density and reduce wrapping.
