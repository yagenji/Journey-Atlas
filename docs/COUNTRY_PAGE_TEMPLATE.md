# JOURNEY ATLAS Country Page Template

最終更新：2026-08-30

Icelandを基準に、以後の国・地域ページを同じ構造で制作するためのテンプレート仕様。

## 1. 固定構成

1. Header / utility navigation
2. Hero
3. 旅の地図
4. この国で見たい景色
5. その国で出会えるもの
6. 旅するなら（季節 / 移動）
7. こんな人に
8. 基本情報
9. 知っておきたいこと
10. 関連国
11. 行きたい国保存
12. Footer

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
その国の景観・文化・旅の特徴を短い語で8件前後。

### Beyond the Scenery
その国を理解するための深掘り。歴史・暮らし・文化・食・都市・移動などを、背景や意味まで含めて説明する。

### Travel Trivia
現地で見つける、使う、気づくことで旅が少し楽しくなる小さな知識を扱う。

- Beyond the Scenery と同じ人物・出来事・伝統・食・移動・文化題材を繰り返さない。
- 「同じ情報の短縮版」にしない。
- 5件なら原則5つの異なるトピックを選ぶ。
- 深掘りは Beyond the Scenery、軽い発見は Travel Trivia に役割分担する。
- Country最終QAで両セクションのtopic duplicationを確認する。

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

## 6. Related countries

- 3件を基本。
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

1. content design / scene lock
2. Hero + 8 scene visual production and approval
3. Country JSON / map / shared template implementation
4. desktop / tablet / mobile QA
5. data / asset / accessibility validation
6. Review Deployment at canonical /countries/{slug}/ URL
7. keep atlasPublished = false / noindex / sitemap excluded
8. user review and fixes on the same URL
9. user approval
10. atlasPublished = true / index / sitemap / formal discovery links
