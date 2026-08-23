# JOURNEY ATLAS Top Page QA

最終更新：2026-08-23

トップページを「完成版」として扱うための最終チェック台帳。デザイン探索は終了し、以後は不具合修正・アクセシビリティ・レスポンシブ・承認済み素材への差し替えのみを行う。

## 1. 構成

- [x] Header
- [x] Hero
- [x] 3つの入口（国 / 地図 / テーマ）
- [x] 国から探す
- [x] 地図から探す
- [x] テーマから探す
- [x] JOURNEY LENS
- [x] About
- [x] Footer

## 2. Hero

- [x] タイトルは2行固定。
- [x] CTAを置かない。
- [x] 5枚のHeroビジュアルを切替可能。
- [x] 自動切替あり。
- [x] prefers-reduced-motionでは自動切替停止。

固定コピー：

```text
次に行きたい世界を、
見つける。

まだ知らない景色、心に残る出会い。
文化や人々の暮らし。
199の国・地域を、イラストとともに
めぐる世界図鑑です。
```

## 3. 国から探す

- [x] 199 destinationsをregistryから描画。
- [x] 公開済み国のみリンク化。
- [x] 横スクロール。
- [x] 全件一覧。
- [x] 英語名 / 日本語名検索。
- [x] A-Z絞り込み。
- [x] 未完成イラストはneutral fallbackで表示可能。

### Release rule
199枚のproduction illustration完成はトップページ公開の条件にしない。承認済み画像から順次差し替える。

## 4. 地図から探す

- [x] 7大地域。
- [x] 必要地域にsubregion。
- [x] SVG country geometryを利用。
- [x] country hover / select。
- [x] 右側country listと地図を連動。
- [x] zoom / pan / reset。
- [x] 選択解除。
- [x] dateline対応（Kiribati等）。
- [x] Europe / Western Europe / North America / Northern North Americaのframing調整をmain `map-regions.js`へ統合。

### Lock
地図のframing処理は `assets/js/map-regions.js` のみに置く。別のframing fix scriptを追加しない。

## 5. テーマから探す

- [x] 8テーマ固定。
- [x] approved spriteを利用。
- [x] テーマ選択で候補国を表示。

固定テーマ：
- earth — 地球の風景
- city — 街を歩く
- history — 時をたどる
- life — 暮らしに出会う
- wildlife — 野生に会う
- sea — 海の世界へ
- food — 食をめぐる
- road — 道の先へ

## 6. JOURNEY LENSとの差別化

- [x] ATLASはイラスト主体。
- [x] LENSは写真と物語への外部導線。
- [x] トップではLENSをcompact horizontal stripとして扱う。
- [x] ATLASの国イラストは写真60 / 絵40のpainterly realismを基準にする。

## 7. Responsive / accessibility

- [x] スマホHeroを縦積み。
- [x] 3入口をスマホで縦積み。
- [x] Themeを2列化。
- [x] Mapはモバイル用レイアウトあり。
- [x] 国カード・地図にaria labelを設定。
- [x] keyboard操作を地図に用意。
- [ ] 実機iPhone最終目視（ユーザー端末で行う項目）。

## 8. 完成判定

コード上のトップページは完成版としてlockする。

今後トップで行う作業：
1. 明確な表示崩れの修正。
2. 壊れた操作・リンクの修正。
3. 実機で判明したresponsive修正。
4. 199 destination illustrationsのprogressive replacement。

新しいトップページ案の再設計はしない。
