# JOURNEY ATLAS

静かな余白とイラストで「この国へ行ってみたい」という気持ちをつくる、大人向けのビジュアル・トラベルアトラスです。現在は Iceland の1ページを収録しています。

## ディレクトリ構成

```text
.
├── index.html                 # 共通の国ページテンプレート
├── assets/
│   ├── css/style.css         # 共通スタイル
│   └── js/app.js             # JSON読込・描画・インタラクション
├── data/
│   └── countries/
│       └── iceland.json      # Icelandページの全コンテンツ
└── README.md
```

国を追加するときは `data/countries/` に同じ形式のJSONを追加し、URLの `?country=ファイル名` で表示できます。例: `?country=iceland`。将来は静的ホスティング側で国別URLへ書き換えることもできます。

## ローカルで確認する

JSONを読み込むため、ファイルを直接開かずローカルサーバーを起動してください。

```bash
python3 -m http.server 8000
```

ブラウザで <http://localhost:8000/> を開きます。Icelandを明示する場合は <http://localhost:8000/?country=iceland> です。

外部ライブラリ、ビルド処理、パッケージのインストールは不要です。

## 画像・地図の差し替え

- Heroと景色カードは現在CSSによるプレースホルダーです。画像が揃ったらJSONの各 `image` にパスを設定すると表示されます。
- 地図は推測で描かず、`#country-map-art` を正確なSVGへ差し替えられる構造にしています。番号マーカーも現在は非地理的な仮配置です。SVG導入時に各景色の正確な座標をJSONへ追加してください。
