# JOURNEY ATLAS Map System

## 目的
国ページの「旅の地図」は、景色カードの位置関係を正確かつ静かに示すアトラス図版とする。
地図はAI画像生成で描かない。正確な地理データからSVGを生成し、JOURNEY ATLAS共通のデザインを適用する。

## 固定方針

### 1. 正確性を先に固定する
- 国境・国土形状: Natural Earth Admin 0 1:10m を標準とする。
- 海岸線が体験上重要な島国・海岸国家: 必要に応じてGSHHS/GSHHGの海岸線を使用する。
- 緯度経度はWGS84を基準とする。
- 手描きで国の輪郭を作らない。
- 外部の完成済み地図画像を埋め込まない。

### 2. 地図に置く情報
必須:
- 正確な国土・主要島嶼の輪郭
- 必要な主要湖沼
- 景色カードの番号マーカー
- Hero地点の小さな位置マーカー

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

各国の `data/maps/{slug}.json` に地図表示用boundsを保存する。

```json
{
  "slug": "iceland",
  "source": "assets/images/iceland/map-atlas.svg",
  "projection": "equirectangular",
  "bounds": {
    "west": -25.8,
    "east": -12.2,
    "south": 62.8,
    "north": 67.1
  },
  "style": "journey-atlas-map-v1"
}
```

`assets/js/atlas-map-runtime.js` が同じboundsで景色地点とHero地点を投影する。
これによりSVGとマーカーの位置計算を一致させる。

## マーカーが密集する場合
原則として実座標を維持する。
重なりが発生した場合のみ `markerOffsets` で最小限補正する。

```json
"markerOffsets": {
  "hero": { "x": -0.8, "y": 0 },
  "example-scene": { "x": 1.2, "y": -0.5 }
}
```

補正値はパーセントポイント。位置を大きく偽装しない。

## 国別制作フロー
1. 国のslugと景色地点座標を確定する。
2. 正確な地理データを選ぶ。
3. 国を収めるboundsを決める。
4. `scripts/generate_country_map.py` でSVGを生成する。
5. `assets/images/{slug}/map-atlas.svg` に保存する。
6. `data/maps/{slug}.json` を追加する。
7. 実ページで番号マーカーの位置と重なりを確認する。
8. 必要な場合だけmarkerOffsetsを追加する。

## QA
公開前に必ず確認する。

- 国の輪郭が正しい
- 主要島嶼が欠落していない
- 隣国領土を誤って含めていない
- 景色地点が実際の地域と一致している
- マーカー同士が読める
- 国名や不要記号が地図内に重複していない
- 他国ページと同じ配色・線・余白になっている

## Iceland benchmark
Icelandは新Map Systemの最初の基準国。
- coastline: GSHHS intermediate-resolution data
- projection: equirectangular
- bounds: W -25.8 / E -12.2 / S 62.8 / N 67.1
- visual style: journey-atlas-map-v1

今後の国はこのIceland地図をデザイン基準として展開する。
