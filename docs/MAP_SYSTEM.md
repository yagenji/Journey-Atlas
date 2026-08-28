# JOURNEY ATLAS Map System

## 目的
国ページの「旅の地図」は、景色カードの位置関係を正確かつ静かに示すアトラス図版とする。
地図はAI画像生成で描かない。正確な地理データからSVGを生成し、JOURNEY ATLAS共通のデザインを適用する。

## 固定方針

### 1. 正確性を先に固定する
- 国境・国土形状: Natural Earth Admin 0 1:10m を標準とする。
- Natural Earthで海岸・島嶼が1200×760上で粗く見える場合は、geoBoundaries gbOpen の詳細境界を使用する。
- geoBoundariesのADM0が十分でない場合はADM1を国単位にdissolveし、行政区の内部線を出さず海岸・島嶼だけを保持する。
- 海岸線が体験上重要な孤立した島国では、必要に応じてGSHHS/GSHHGを使用する。
- 地理データのsource URL / version・commit / licenseをmap sourceまたはSVG metadataに残す。
- 緯度経度はWGS84を基準とする。
- 手描きで国の輪郭を作らない。
- 外部の完成済み地図画像を埋め込まない。

### 2. 地図に置く情報
必須:
- 正確な国土・主要島嶼の輪郭
- 景色カードの番号マーカー
- Hero地点の小さな位置マーカー

必要な場合のみ:
- 視認できる主要湖沼

原則置かない:
- 国名の重複表示
- 意味のない山型・三角記号
- 装飾目的の都市名・山名
- 実データに基づかない地形記号
- 方位記号や凡例（機能上必要な場合を除く）

### 3. デザイン
スタイル名: `journey-atlas-map-v1`

- 海: 薄いブルーグレー〜生成りの静かなウォッシュ
- 陸: 淡いオーカー / モス系の水彩調
- 海岸線: JOURNEY ATLASの濃紺より少し軽いブルーグレー
- 紙目: 極弱
- 影: ごく弱い浮遊感のみ
- ラベル: 原則なし
- 地図そのものは写真化・写実化しない

世界観は「記号を足す」ことで作らず、色、線、余白、面の質感で作る。

## 投影
国ページ内のマーカーとの整合を優先し、基本は equirectangular（緯度経度の線形投影）を使用する。
地図SVGを生成したboundsと、ページ上のマーカー計算に使うboundsを必ず一致させる。

## マーカー補正ルール
実座標はSingle Source of Truthとし、緯度経度そのものを重複回避のために変更しない。
表示上の補正は各地点の `mapOffset: {x, y}` だけで行う。x / y はmap canvasに対する百分率。

### 自動Validation
`scripts/validate_country.py` は1200×760へ投影した最終表示位置を検査する。

最小中心間距離:
- Scene / Scene: 25px
- Scene / Hero: 22px
- Scene / Capital: 20px
- Hero / Capital: 16px

これを下回る場合はvalidation failureとし、公開しない。
また、markerはcanvas端から種類ごとの安全余白を確保する。

### 補正の順序
1. まずboundsが不必要に広すぎないか確認する。
2. 実座標のまま十分に読める場合は補正しない。
3. 衝突する場合はScene markerを最初に最小補正する。
4. Capitalはmarkerを大きく動かす前に `labelPosition` を検討する。
5. Hero / Capitalを動かす場合も、複数markerへ小さく分散させる。
6. `mapOffset` のベクトルは5%以内。通常は2.5%以内を目標とする。
7. 40px未満の近接ペアは、validationを通っていても目視QA対象とする。

補正後も「実際の地域を指している」と認識できる範囲を超えてはならない。

## 国別制作フロー
1. 国のslugと景色地点座標を確定する。
2. 正確な地理データを選ぶ。
3. 国を収めるboundsを決める。地理geometryの東西・南北bboxに対して、通常3〜10%程度の余白を基本とし、不要に広いboundsを置かない。
4. `scripts/generate_country_map.py` でSVGを生成する。productionのsimplifyは原則0.003以下とし、粗く見える場合はさらに下げる。
5. ローカルでXML構文検証を行う。
6. ローカルでSVGをPNGへ1200×760でレンダリングし、Iceland / Norway / Denmarkと並べて国土形状・主要島嶼・海岸線密度・余白・線幅を目視確認する。
7. SVGをGitHubへ配置する。
8. GitHub上のファイル末尾・サイズ・SHAなどを確認し、途中欠損がないことを確認する。
9. 国別map configから対象SVGを参照する。
10. 公開ページで地図表示、番号位置、Hero位置を確認する。
11. 必要な場合だけmarkerOffsetsを追加する。

## Release Gate
ユーザーに確認を依頼する前に、以下をすべて通す。

### Data QA
- 国の輪郭が正しい
- 海岸線が大きな直線・折れ線に単純化されていない
- 主要島嶼だけでなく、その国の地理理解に必要な群島・沿岸島嶼が欠落していない
- 隣国領土を誤って含めていない
- 景色地点の緯度経度が実際の地域と一致している

### Asset QA
- SVGがXMLとしてparseできる
- ローカルで画像としてrenderできる
- GitHub配置後のファイルが途中欠損していない
- 参照URLが実在する
- キャッシュ更新番号が変更されている

### UI QA
- 地図本体が表示される
- 1〜8等のマーカーが地図上に収まる
- マーカー同士が読める
- Hero地点が地図と一致する
- 国名や不要記号が重複していない
- 配色・線・余白がJOURNEY ATLASの世界観と一致する

### PMルール
- 「原因未特定のまま修正を重ねる」を禁止する。
- 不具合発生時は、データ → asset → 参照 → render → cache の順に切り分ける。
- 暫定回避策を追加する前に、既存の暫定処理を増やさず直せるか確認する。
- 変更範囲は最小化し、一度に複数レイヤーを変更しない。
- 「生成済み」「GitHub配置済み」「実装済み」「公開確認済み」を明確に区別する。
- ユーザーの画面を最初のQA環境にしない。内部preflightを通した後にレビューを依頼する。

## Iceland benchmark
Icelandは新Map Systemの最初の基準国。
- coastline: GSHHS intermediate-resolution data
- projection: equirectangular
- bounds: W -25.8 / E -12.2 / S 62.8 / N 67.1
- visual style: journey-atlas-map-v1

今後の国はこのIceland地図を正確性・情報量・デザイン・QAの基準として展開する。


## Map Quality Benchmark（2026-08）

公開CountryではIceland / Norway / Denmarkを最低比較基準とする。
Sweden / Finlandは2026-08に詳細境界へ更新し、この水準へ統一した。

新規Countryは「SVGが生成できた」だけでは合格にしない。
1200×760 PNGで既存benchmarkと横並びにし、以下が同程度であることを確認する。

- 海岸線の情報密度
- 主要島嶼・群島の残り方
- 国土がcanvasを使う割合と余白
- 陸・海・海岸線の色
- strokeの視認性
- markerの分離
- Hero / Capital / 8景の地理的一貫性

粗さを回避するために独自の手描き補完は行わず、source geometryの解像度を上げて解決する。
