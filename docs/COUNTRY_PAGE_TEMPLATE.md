# JOURNEY ATLAS Country Page Template

最終更新：2026-09-07

Icelandを基準に、以後の国・地域ページを同じ構造で制作するためのテンプレート仕様。

## 1. 固定構成

1. Header / utility navigation
2. Hero
3. 旅の地図
4. この国で見たい景色
5. その国で出会えるもの
6. Beyond the Scenery
7. Taste
8. Travel Trivia
9. こんな人に / 知っておきたいこと
10. 旅するなら（旅の目安日程 / 季節 / 移動）
11. NEXT ROUTES（0〜3件、成立する国のみ）
12. NEXT DESTINATIONS
13. 行きたい国保存
14. JOURNEY LENS
15. Footer

## 2. Hero

- 1つの実在する風景を使う。
- 国の名物を複数合成しない。
- JOURNEY ATLAS固定スタイル：photo 60 / illustration 40。
- 左側に国名・リードが重なる前提でsafe areaを確保する。
- Heroとsceneで同じ画像を安易に重複利用しない。国全体の入口として別の実在景観を選べる場合は専用Heroを優先する。

## 3. Scene

- 原則8景を基準にする。ただし国の規模や内容により6〜10景まで許容。
- 各sceneは実在する特定地点。
- 各sceneに `id / name / nameLocal / mapLabel / description / coordinates / image` を持つ。
- 地図markerとscene cardは同じidで連動する。
- Scene artworkは1地点1景。コラージュ禁止。

## 4. Map

- 国土形状は可能な限り正確な地理ベースを使う。
- scene coordinatesをmap boundsに投影し、番号markerを表示する。
- markerとscene cardはhover / focus / clickで連動。
- 出典を表示する。
- 地図画像が失敗した場合はfallbackを出す。

## 5. Information blocks

### encounters
「その国で何が見えるのか」を、一目で伝える視覚的な目次として8件前後を置く。

- 原則として、説明なしで意味が分かる一般名詞・一般的な表現を使う。
- 景観、自然、街並み、建築、動物、広く認知された文化的な光景を優先する。
- 固有の道具名、専門用語、地域限定の呼称、特定ブランドやキャラクターは原則使わない。
- 「知ると面白い文化知識」を入れる場所ではない。そうした題材は Beyond the Scenery / Travel Trivia へ回す。
- 例：湖 / アルプス / 洞窟 / 港町 / 葡萄畑 / 城 / オーロラ / サンタクロース。
- 不適切な例：説明が必要な舟・楽器・衣装・工芸品の固有名、特定キャラクター。
- 8景の名称をそのまま並べるのではなく、ページ全体を数秒で俯瞰できる粒度にする。

### Beyond the Scenery
その国を理解するための深掘り。歴史・暮らし・文化・食・都市・移動などを、背景や意味まで含めて説明する。

### Travel Trivia
現地で見つける、使う、気づくことで旅が少し楽しくなる小さな知識を扱う。

- Beyond the Scenery と同じ人物・出来事・伝統・食・移動・文化題材を繰り返さない。
- 「同じ情報の短縮版」にしない。
- 5件なら原則5つの異なるトピックを選ぶ。
- 深掘りは Beyond the Scenery、軽い発見は Travel Trivia に役割分担する。
- Country最終QAで両セクションのtopic duplicationを確認する。

### travelScale
旅の目安日程は3段階のUI構造を共通化するが、日数の閾値は国ごとに可変とする。

- 固定：3項目、`DURATION`、`旅の目安日程`、`city / map / compass` の順。
- **日程表記は全3段階とも「日」に統一し、第3段階は必ず上限を置かず `○日以上` とする。**
- 例：`3〜4日 / 5〜7日 / 8日以上`。
- 小国なら `半日〜1日 / 2日 / 3日以上` のように短縮してよい。
- 広域国なら `3〜4日 / 7〜10日 / 12日以上` のように拡張してよい。
- 第3段階は「その日数で旅が終わる」という上限ではなく、地域やテーマをさらに広げられる長期滞在の入口として扱う。
- 各段階の「例」は網羅リストではなく、旅の流れを理解するための代表ルートに絞る。原則3〜6地点程度とし、8景や主要スポットをすべて詰め込まない。
- 面積だけでなく、見どころの分散、地域差、島嶼・山岳、国内移動負荷、実際に成立する旅程で決める。
- テンプレートを埋めるための日数水増し、または大国を固定日数へ圧縮することを禁止する。

### seasons
4区分を基本とし、季節差が弱い国では雨季 / 乾季など現地の実態に合わせて再定義する。

### transport
旅の移動体験を1つのまとまりとして説明する。距離値は意味がある場合のみ表示。

### personas
3件。FOR WHOMは全Countryで3項目に固定する。

### facts
最低限：地域 / 首都 / 人口 / 言語 / 通貨。

### tips
旅行者が知っておくべき3件前後。安全・自然条件・移動・文化など、その国固有の内容を優先する。

## 6. NEXT ROUTES / NEXT DESTINATIONS

### NEXT ROUTES

その国から旅程を自然に続けられる、代表的な越境周遊ルートだけを扱う。

- optional。0〜3件。0件ならセクション自体を表示しない。
- 「国境がある」だけでは採用しない。旅行者が実際に使うメジャーな周遊ルートであることを最優先する。
- 陸路、鉄道、橋、定期フェリーなど、旅が連続する移動を対象にする。
- 島国でも、フィンランド–エストニアやマルタ–シチリアのような代表的フェリー周遊は採用してよい。
- 飛行機でしか実質的に成立しない場合は作らない。アイスランドやキプロスのように0件でもよい。
- 1国しか隣接しない国では、同じ隣国への異なる代表ルートを複数載せてもよい。
- 各カードは「行き先国 / 代表ルート / そのルートで見える景観や文化の変化」の短文だけにする。
- 運賃、所要時間、便数、列車番号など変動の大きい実務情報は載せない。

### NEXT DESTINATIONS

「この国が気に入ったなら、次にどの国も合いそうか」という旅先推薦。

- 3件を基本。
- 隣国である必要はない。景観、地形、都市、文化、旅のスタイルなどの親和性で選ぶ。
- NEXT ROUTESと同じ国が重複してもよい。役割が異なるため、重複そのものは問題にしない。
- reasonは「国境を越えて続ける」説明ではなく、「この国の何に惹かれた人へ薦めるか」を書く。
- 小さなflag + English / Japanese + reason。
- 関連国ページが未公開の場合はclickableにしない。
- 関連国imageの完成はそのページ公開のblockerにしない。

## 7. Wish list

- localStorage保存を維持。
- account / loginは現段階では不要。
- top pageの行きたい国表示と同じstorage keyを使う。

## 8. Navigation

Dead controlsを置かない。

固定utility links：
- トップ → `./`
- 国を探す → `./#countries`
- テーマ → `./#themes`

## 9. Responsive baseline

- 1100px以下：map / scenesを縦積み。
- 700px以下：scene card 1列。
- 700px以下：related country 1列。
- small screenではmap labelよりmarker numberを優先。

## 10. Validation

各国追加時に確認：

1. slugがregistryと一致。
2. scene id重複なし。
3. coordinatesがbounds内。
4. 画像pathが存在。
5. map source記載。
6. populationなど時点依存データにsourceまたはupdatedAtを持つ。
7. Review Deploymentでは `atlasPublished:false` を維持し、ユーザー承認後のみ `true` にする。

## 11. Production sequence

Operational sequencing is defined only by `docs/COUNTRY_PRODUCTION_STATE.md` and `ops/country-production/{slug}.json` on `main`.

Normal user-facing gates are:
1. Hero approval
2. S01–S08 batch review
3. FOOD01–FOOD04 batch review
4. canonical Country URL final review / publication approval

Scenes and Taste are generated as independent images without per-image user approval. After visual approval, Map → asset QA → Country JSON / taxonomy implementation → validation → Review Deployment → targeted Desktop / Tablet / Mobile QA proceeds as one automatic chain unless a real blocking specification decision is required.

Review Deployment keeps `atlasPublished:false`, `noindex,follow`, sitemap exclusion, and normal-navigation exclusion. Only explicit final user approval may switch to `atlasPublished:true`, indexing, sitemap inclusion, and formal discovery links.
