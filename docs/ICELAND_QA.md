# Iceland Page QA

最終更新：2026-08-23

Icelandページを、公開前に「実景との一致」「データ整合」「操作性」「レスポンシブ」「将来の国追加」の5観点で確認するための台帳。

## 1. 実景との一致

| 対象 | 現状 | 最終確認ポイント |
| --- | --- | --- |
| Hero | 構造実装済み / visual差し替え待ち | **Stokksnes / Vestrahornの実景を基準にした専用Hero**へ差し替える。 |
| Skógafoss | 構造実装済み / visual差し替え待ち | 滝幅、崖形状、滝壺、人物尺度。 |
| Jökulsárlón | 構造実装済み / visual差し替え待ち | 氷河湖と奥の氷河の連続性、氷塊の色。 |
| Reynisfjara | 構造実装済み / visual差し替え待ち | 柱状節理、黒砂、Reynisdrangarの位置関係。 |
| Þingvellir | 構造実装済み / visual差し替え待ち | 裂け目地形を誇張していないこと。 |
| Geysir | 構造実装済み / visual差し替え待ち | 間欠泉の噴出を火山噴火のようにしていないこと。 |
| Mývatn | 構造実装済み / visual差し替え待ち | 湖、火山地形、島・丘の比率。 |
| Kirkjufell | 構造実装済み / visual差し替え待ち | 山の輪郭とKirkjufellsfossの位置関係。 |
| Landmannalaugar | 構造実装済み / visual差し替え待ち | 流紋岩の色を虹色に誇張していないこと。 |

### 現時点の評価

- ページ構造・地図連動・情報設計はテンプレート候補として成立している。
- 既存SVGは旧スタイルのため、最終production artworkとしては扱わない。
- 最終画像はJOURNEY ATLAS固定基準の **photo 60 / illustration 40** を使う。
- 画像はすべて実在する特定景観を基準にし、写真そのものには見せない。
- JOURNEY LENSの実写写真と一目で差が分かることを確認する。

## 2. データ整合

- [x] Icelandは8景。
- [x] scene idは一意。
- [x] 各景に緯度・経度を設定。
- [x] 地図境界は `N 66.8 / S 63.1 / W 25 / E 13`。
- [x] 地図はWikimedia Commonsの地理参照地図を使用。
- [x] 地図の出典表示をページに表示。
- [x] 人口は2026年6月末の約39.7万人として管理。
- [x] `data/countries/index.json` を国レジストリとして追加。
- [x] `scripts/validate_country.py` を追加。
- [x] GitHub Actionsで国データ検証を行う構成を追加。

## 3. 操作性

- [x] 地図上の番号と景色カードを同じscene idで連動。
- [x] hover / focus / clickで対応景色を強調。
- [x] 地図マーカーをクリックすると対応カードへスクロール。
- [x] URLハッシュ（例 `#skogafoss`）で景色を直接指定可能。
- [x] キーボードのEnter / Spaceでも景色を選択可能。
- [x] 「この国に行きたい」はlocalStorageに保存。
- [x] 地図画像が読み込めない場合のフォールバックあり。
- [x] Header utility navigationを実リンク化し、dead controlを解消。
- [x] PAGE NOT FOUNDからトップへ戻る導線を明確化。

## 4. レスポンシブ

- [x] 1100px以下で地図・8景を縦積みに切替。
- [x] 700px以下で景色カードを1列化。
- [x] 700px以下で関連国を1列化。
- [x] スマホでは地図ラベルを隠し、番号を優先。
- [ ] 実機iPhoneで最終目視確認。

## 5. 確定した判断

1. **Hero**：Mývatnの再利用ではなく、Stokksnes / Vestrahornを基準にした専用Heroを制作する。
2. **アートスタイル**：旧水彩／ガッシュ調ではなく、写真60 / 絵40のpainterly realismを最終基準とする。
3. **関連国**：Norway / New Zealand / Chileは、各国ページ制作前でも画像なしで成立する現在の構造を維持する。画像完成はIceland公開のblockerにしない。

## 6. 公開前に残る作業

1. Hero production illustrationの差し替え。
2. 8 scene production illustrationsの差し替え。
3. illustration差し替え後のcrop / readability QA。
4. 実機iPhone最終目視。
5. country JSON validationの再実行。

この5点が完了したらIceland構造をcountry-page templateとしてlockする。
