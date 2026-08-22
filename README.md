# JOURNEY ATLAS

「この国へ行ってみたい」という気持ちをつくる、大人向けのビジュアル・トラベルアトラスです。明るく美しい水彩・ガッシュ調のイラスト、イラスト地図、旅の見どころを一国一ページでまとめます。

## 現在のプロトタイプ

- ICELAND / アイスランド
- ANTARCTICA / 南極
- TAJIKISTAN / タジキスタン

トップページから各国ページへ遷移できます。国ページは `country.html?country=<slug>` の形式です。

## 公開

GitHub PagesをGitHub Actionsから自動デプロイします。

- Top: `https://yagenji.github.io/Journey-Atlas/`
- Iceland: `https://yagenji.github.io/Journey-Atlas/country.html?country=iceland`
- Antarctica: `https://yagenji.github.io/Journey-Atlas/country.html?country=antarctica`
- Tajikistan: `https://yagenji.github.io/Journey-Atlas/country.html?country=tajikistan`

`.github/workflows/deploy-pages.yml` が `main` へのpushごとに公開します。

## 制作方針

JOURNEY LENSで公開済みの国・地域を優先して制作します。全体対象は、日本が国家承認する外国195か国＋日本＋台湾＋北朝鮮＋南極の計199ページです。

画像は写真の代用品ではなく、実景の特徴を守りながら「美しい・行きたくなる」と感じる旅図鑑イラストを目指します。地図も位置関係を大きく崩さず、イラストだからできる視覚表現を取り入れます。

## データ検証

```bash
python3 scripts/validate_country.py
```

国データは `data/countries/`、国一覧は `data/countries/index.json` で管理します。
