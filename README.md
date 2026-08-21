# JOURNEY ATLAS

静かな余白と実景に寄せたイラストで「この国へ行ってみたい」という気持ちをつくる、大人向けのビジュアル・トラベルアトラスです。現在は Iceland の1ページを収録しています。

## 現在のIcelandページ

- Heroイラスト
- 緯度・経度に基づく8地点のマーカー
- Skógafoss / Jökulsárlón / Reynisfjara / Þingvellir / Geysir / Mývatn / Kirkjufell / Landmannalaugar の8景
- 季節、移動、基本情報、旅の相性、注意点
- ブラウザ内に保存する「この国に行きたい」機能

## ディレクトリ構成

```text
.
├── index.html
├── assets/
│   ├── css/style.css
│   ├── js/app.js
│   └── images/iceland/
├── data/
│   └── countries/
│       └── iceland.json
├── docs/
│   └── ICELAND_ART_BRIEF.md
└── README.md
```

国を追加するときは `data/countries/` に同じ形式のJSONを追加し、URLの `?country=ファイル名` で表示できます。例: `?country=iceland`。

## ローカルで確認する

JSONを読み込むため、ファイルを直接開かずローカルサーバーを起動してください。

```bash
python3 -m http.server 8000
```

ブラウザで <http://localhost:8000/> を開きます。Icelandを明示する場合は <http://localhost:8000/?country=iceland> です。

外部ライブラリ、ビルド処理、パッケージのインストールは不要です。

## 地図と出典

Icelandの地図は Wikimedia Commons の `Iceland location map.svg`（NordNordWest / CC BY-SA 3.0）を使用しています。地理的境界は N 66.8° / S 63.1° / W 25° / E 13° で、地点マーカーは各景色の緯度・経度から配置します。道路や推測ルートは描画しません。

人口など更新可能性のある基本情報は `data/countries/iceland.json` 内に出典メモを保持します。

## 画像方針

Heroと景色カードは、実景の地形・水・海岸線・植生・人工物との一致を優先します。観光ポスター的な誇張、実景にない山・道路・建物・オーロラなどの追加は避けます。詳細は `docs/ICELAND_ART_BRIEF.md` を参照してください。
