# JOURNEY ATLAS Map System

## 目的
国ページの「旅の地図」は、景色カードの位置関係を正確かつ静かに示すアトラス図版とする。地図はAI生成や手描き輪郭ではなく、正確な地理データからSVGを生成し、JOURNEY ATLAS共通デザインを適用する。

## 固定仕様
- canvas: `1200 × 760`
- projection: equirectangular
- visual style: `journey-atlas-map-v1`
- production quality profile: `atlas-v2`
- WGS84の緯度経度をSingle Source of Truthとする
- SVG生成時のboundsとページ上のmarker投影boundsを一致させる

## 地理データ
新規Countryでは海岸・島嶼を十分に保持できるgeometryを使う。優先順は次を基本とする。

1. `geoBoundaries gbOpen ADM0`
2. ADM0で海岸・島嶼がbenchmarkより粗い場合は `geoBoundaries gbOpen ADM1` を国単位へdissolve
3. 孤立した島国や海岸線の再現に適する場合はGSHHS/GSHHG
4. Natural Earth 1:10mは1200×760でbenchmarkと同等の情報量が確認できる場合のみ採用

source、build/version、licenseはCountry JSONの`map.source`またはSVG metadataへ残す。

禁止:
- 国の輪郭を手描きで補完しない
- 粗いgeometryを装飾線でごまかさない
- 外部の完成済み地図画像を貼らない
- ファイルサイズ削減だけを理由に主要島嶼や群島を消さない

## geometry / bounds品質
- 海岸線が大きな直線・折れ線へ単純化されていないこと
- 国を理解する上で重要な主要島嶼・群島が残っていること
- 隣国領土を誤って含めないこと
- boundsは国土bboxを基準に通常3〜10%程度の余白を持たせ、不要に広くしないこと
- 国土がcanvas上で小さくなりすぎないこと

`scripts/generate_country_map.py` のatlas-v2初期値:
- geoBoundaries: simplify `0.0008°`
- GSHHS/GSHHG: `0.0010°`
- Natural Earth: `0.0030°`

これは初期値であり、最終判断は1200×760 PNGと実ページの目視QAで行う。粗く見える場合は単純化値だけでなくsource geometryから見直す。

## 共通デザイン
- 海: 薄いブルーグレー〜生成りの静かなウォッシュ
- 陸: 淡いオーカー / モス系
- 海岸線: 軽いブルーグレー
- shadow: ごく弱い浮遊感のみ
- 地図本体のラベル: 原則なし
- 国名、山型、意味のない装飾線を追加しない

## マーカー補正ルール
実地点の`coordinates`は変更しない。衝突回避は各地点の`mapOffset: {x, y}`だけで行う。x / yはmap canvasに対する百分率。

### atlas-v2自動QA
`scripts/qa_map_markers.py`はapp.jsと同じ線形投影でCapital / Hero / 8 scenesの最終表示位置を1200×760へ投影する。

Release Gate:
- marker中心間距離: **42px以上**
- canvas端からのclearance: **12px以上**
- mapOffset各軸: **±5%以内**
- mapOffsetベクトル: **5.5%以内**
- atlas-v2 SVG: `viewBox="0 0 1200 760"`
- atlas-v2 SVG: `data-map-quality="atlas-v2"`

衝突した場合はvalidation failureとし、そのまま公開しない。

補正順序:
1. boundsが不必要に広くないか確認
2. 実座標のまま読めるなら補正しない
3. Scene markerを最小量だけ補正
4. Capitalは位置を大きく動かす前に`labelPosition`を調整
5. Hero / Capitalとの衝突は必要なら複数markerへ小さく分散
6. 数値QA通過後に1200×760 PNGと実ページで目視

通常は2.5%以内を目標とし、5%近い補正が必要ならboundsや地点密度を再検討する。

## Country制作フロー
1. Hero / 8景 / Capitalの緯度経度を確定
2. geography sourceを選択
3. tight boundsを決定
4. `scripts/generate_country_map.py`で`map-atlas-v2.svg`を生成
5. XML parse / 1200×760 renderを確認
6. Iceland / Norway / Denmarkと横並びで海岸線・島嶼・余白・線幅を比較
7. Country JSONに`qualityProfile: "atlas-v2"`、`markerQaVersion: 1`を設定
8. `python3 scripts/qa_map_markers.py`を実行
9. 必要な場合だけ`mapOffset`を追加
10. CI validation
11. Review URLでDesktop / Tablet / Mobileを確認
12. 問題がなければreleaseへ進む

`scripts/new_country.py`は新規Countryにatlas-v2設定を標準で作成する。

## Release Gate
Data QA:
- 国土形状が正しい
- 海岸線が粗くない
- 主要島嶼・群島が欠落していない
- 隣国領土を誤って含めていない
- Capital / Hero / 8景の緯度経度が正しい

Asset QA:
- SVG XML parse PASS
- 1200×760 render PASS
- `data-map-quality="atlas-v2"`
- ファイル途中欠損なし
- source / license情報あり
- 正しいasset pathを参照

UI QA:
- 1〜8 / Hero / Capitalが地図内に収まる
- marker衝突QA PASS
- 首都ラベルが読める
- 国名や不要線が重複しない
- Iceland / Norway / Denmarkと同じシリーズに見える
- Desktop / Tablet / Mobileで確認済み

## Benchmark
Iceland / Norway / DenmarkをMap Quality Benchmarkとする。Sweden / Finlandはatlas-v2更新で同じ基準へ合わせる。

比較項目:
- 海岸線の情報密度
- 主要島嶼・群島の保持
- canvasの使い方と余白
- 陸・海・strokeの共通デザイン
- markerの分離
- Hero / Capital / 8景の地理的一貫性

「SVGが生成できた」「CIが成功した」だけではMap QA完了としない。実ページで確認して初めて完成候補とする。

## PMルール
不具合時は `data → geometry source → asset → reference → render → marker → cache` の順に切り分ける。Country固有の暫定回避策を増やさず、共通問題はMap System側を修正する。ユーザーの画面を最初のQA環境にせず、内部preflight後にレビューを依頼する。
