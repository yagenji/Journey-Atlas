#!/usr/bin/env python3
"""One-off JOURNEY ATLAS Travel Scale round-trip migration.

Temporary implementation helper for the cross-sectional Travel Scale QA.
It edits only travelScale item text literals and is idempotent.
Remove this script before the final PR is merged.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY = ROOT / "data" / "atlas-destinations.json"

MANUAL_ROUTES = {('afghanistan', 1): 'カブール → バーブル庭園 → カブール',
 ('austria', 1): 'ウィーン → ヴァッハウ（クレムス／デュルンシュタイン） → ウィーン',
 ('bahrain', 1): 'マナーマ → バーレーン要塞 → バブ・アル・バーレーン → アル・ファテフ・モスク → ムハッラク → マナーマ',
 ('belgium', 1): 'ブリュッセル → ゲント → ブリュッセル',
 ('benin', 3): 'コトヌ → アボメ → ダサ＝ズメ → コトヌ',
 ('bhutan', 1): 'パロ → ティンプー → タクツァン → パロ',
 ('bhutan', 2): 'パロ → ティンプー → プナカ → フォブジカ → パロ',
 ('bhutan', 3): 'パロ → フォブジカ → トンサ → ブムタン（ウラ） → パロ',
 ('cambodia', 1): 'シェムリアップ → アンコール遺跡群 → トンレサップ → シェムリアップ',
 ('cambodia', 2): 'シェムリアップ → プノンペン → シェムリアップ',
 ('cambodia', 3): 'シェムリアップ → プノンペン → カンポット → ロン島 → シェムリアップ',
 ('cameroon', 3): 'ヤウンデ → クリビ → ヤウンデ',
 ('canada', 1): 'バンクーバー → バンクーバー島 → バンクーバー',
 ('canada', 2): 'トロント → ナイアガラ → モントリオール → ケベック → トロント',
 ('canada', 3): 'バンクーバー → バンクーバー島 → カナディアン・ロッキー → バンクーバー',
 ('chad', 2): 'ンジャメナ → アベシェ → ンジャメナ',
 ('chad', 3): 'ンジャメナ → ウニアンガ湖群 → ンジャメナ',
 ('comoros', 2): 'モロニ → モヘリ → ニウマシュワ → イツァミア → モロニ',
 ('cotedivoire', 3): 'アビジャン → グラン・バッサム → ヤムスクロ → マン → コロゴ → アビジャン',
 ('croatia', 1): 'スプリト → トロギール → スプリト',
 ('denmark', 1): 'コペンハーゲン → ヘルシンオア／クロンボー城 → コペンハーゲン',
 ('drcongo', 2): 'キンシャサ → マタディ → キンシャサ',
 ('drcongo', 3): 'キンシャサ → キサンガニ → キンシャサ',
 ('equatorialguinea', 3): 'ビオコ島 → リオ・ムニ → コリスコ → ビオコ島',
 ('estonia', 1): 'タリン → ラヘマー → タリン',
 ('finland', 1): 'ヘルシンキ → スオメンリンナ → ポルヴォー → ヘルシンキ',
 ('france', 1): 'パリ → ヴェルサイユ → パリ',
 ('gabon', 3): 'リーブルビル → ロアンゴ → リーブルビル',
 ('germany', 1): 'ベルリン → ポツダム → ベルリン',
 ('iran', 1): 'イスファハーン中心部 → ナクシェ・ジャハーン広場 → 周辺の庭園 → イスファハーン中心部',
 ('iran', 3): 'テヘラン → アルボルズ山脈周辺 → 中央高原 → ファールス → ケルマーン → テヘラン',
 ('iraq', 1): 'バグダッド中心部 → ティグリス河畔 → ムスタンスィリーヤ学院 → 旧市街 → バグダッド中心部',
 ('iraq', 2): 'バグダッド → バビロン → カルバラー／ナジャフ → バグダッド',
 ('ireland', 1): 'ダブリン → グレンダロッホ → ダブリン',
 ('italy', 1): 'ローマ → ティヴォリ → ローマ',
 ('jamaica', 1): 'キングストン → 街路・文化施設 → キングストン',
 ('latvia', 1): 'リガ → シグルダ → ケメリ湿原 → リガ',
 ('liberia', 3): 'モンロビア → クパタウィー滝 → 東ニンバ → モンロビア',
 ('lithuania', 1): 'ヴィリニュス → トラカイ → ヴィリニュス',
 ('macau', 2): 'マカオ半島 → タイパ → コタイ → コロアン村 → 黒沙海灘 → マカオ半島',
 ('macau', 3): 'マカオ歴史地区 → マカオ博物館 → タイパ旧市街 → コロアン村 → マカオ歴史地区',
 ('mali', 3): '南部・中部 → 北部・東部 → 南部・中部',
 ('malaysia', 3): 'クアラルンプール → ジョージタウン → コタキナバル／キナバル山 → クチン → クアラルンプール',
 ('mauritania', 3): '首都圏 → アドラール → 北部鉄道回廊 → 南西デルタ → 首都圏',
 ('mexico', 1): 'メキシコシティ → テオティワカン → プエブラ → メキシコシティ',
 ('mexico', 2): 'メキシコシティ → グアナフアト → オアハカ → メキシコシティ',
 ('mexico', 3): 'メキシコシティ → カンペチェ → バカラル → メキシコシティ',
 ('myanmarburma', 1): 'ヤンゴン → バガン → ヤンゴン',
 ('namibia', 3): 'ウィントフック → 中央・北部 → コールマンスコップ → フィッシュ・リバー・キャニオン → ウィントフック',
 ('nauru', 3): 'ヤレン → アニバレ湾 → ブアダ周辺 → 西岸 → ヤレン',
 ('netherlands', 1): 'アムステルダム → ハールレム → アムステルダム',
 ('newzealand', 1): 'ウェリントン → トンガリロ → ロトルア → ウェリントン',
 ('newzealand', 2): 'ウェリントン → ロトルア → トンガリロ → テカポ → アオラキ → ウェリントン',
 ('newzealand', 3): 'ウェリントン → ロトルア → トンガリロ → テカポ → 西海岸 → ミルフォード・サウンド → ウェリントン',
 ('nigeria', 3): 'ラゴス → オショグボ → アブジャ → ラゴス',
 ('northkorea', 1): '平壌 → 開城 → 平壌',
 ('norway', 1): 'ベルゲン → フロム → ネーロイフィヨルド → ベルゲン',
 ('oman', 3): 'マスカット → ニズワ → ジャバル・アフダル → アッ・シャルキーヤ砂漠 → サラーラ → ワディ・ダルバート → マスカット',
 ('palau', 2): 'コロール → ガラスマオの滝 → バドルルアウ → アイライのバイ → コロール',
 ('palestine', 3): '中央高地 → 北部 → ヨルダン低地 → 南部 → 中央高地',
 ('panama', 1): 'パナマシティ → カスコ・アンティグオ → アグア・クララ（またはミラフローレス） → パナマシティ',
 ('papuanewguinea', 2): 'ポートモレスビー → ハイランド → ポートモレスビー → 東ニューブリテン → ポートモレスビー',
 ('poland', 1): 'ワルシャワ → クラクフ → ワルシャワ',
 ('portugal', 3): 'リスボン → アレンテージョ → アルガルヴェ → ポルト／ドウロ → マデイラ → リスボン',
 ('solomonislands', 1): 'ホニアラ → ボネギ → テナル滝 → ホニアラ',
 ('spain', 1): 'マドリード → トレド → マドリード',
 ('stlucia', 3): 'カストリーズ → マリゴ湾 → スフリエール → ギミー山周辺の森 → デナリー → カストリーズ',
 ('stkittsnevis', 3): 'バセテール → リアムイガ山麓 → ロムニー・マナー → チャールズタウン → ネービス・ピーク山麓 → バセテール',
 ('sudan', 3): 'ナイル流域 → スアキン／サンガネブ → ナイル流域',
 ('sweden', 1): 'ストックホルム → ヴァックスホルム → ストックホルム',
 ('switzerland', 1): 'インターラーケン → ラウターブルンネン → グリンデルワルト → インターラーケン',
 ('togo', 3): 'ロメ → パリメ → アタクパメ → ロメ',
 ('unitedarabemirates', 1): 'アブダビ中心部 → シェイク・ザイード・グランド・モスク → 海岸部 → アブダビ中心部',
 ('unitedkingdom', 1): 'ロンドン → オックスフォード → ロンドン',
 ('unitedkingdom', 2): 'ロンドン → ヨーク → エディンバラ → ロンドン',
 ('unitedstates', 3): '東海岸 → 南部 → 西部 → 東海岸',
 ('uzbekistan', 3): 'タシケント → サマルカンド → ブハラ → ヒヴァ → フェルガナ → タシケント'}


def extract_route(text: str) -> str:
    if not isinstance(text, str) or "例：" not in text:
        return ""
    tail = text.split("例：", 1)[1].strip()
    return tail.split("。", 1)[0].strip()


def norm_node(value: str) -> str:
    value = value.strip()
    return re.sub(r"[。．.!！?？、,;；]+$", "", value).strip()


def route_nodes(route: str) -> list[str]:
    return [node for raw in route.split("→") if (node := norm_node(raw))]


def is_loop(route: str) -> bool:
    if "→" not in route:
        return False
    nodes = route_nodes(route)
    return len(nodes) >= 2 and nodes[0] == nodes[-1]


def replace_route(text: str, new_route: str) -> str:
    before, tail = text.split("例：", 1)
    if "。" in tail:
        _old_route, suffix = tail.split("。", 1)
        return before + "例：" + new_route + "。" + suffix
    return before + "例：" + new_route + "。"


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    slugs = [item["slug"] for item in registry.get("destinations", []) if item.get("atlasPublished")]
    if len(slugs) != 202:
        raise SystemExit(f"Expected 202 published destinations, found {len(slugs)}")

    changed_files = 0
    changed_items = 0
    total_items = 0

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        items = data.get("travelScale", {}).get("items", [])
        if len(items) != 3:
            raise SystemExit(f"{slug}: expected 3 Travel Scale items, found {len(items)}")

        file_changed = False
        for index, item in enumerate(items, 1):
            total_items += 1
            text = item.get("text", "")
            route = extract_route(text)
            if not route:
                raise SystemExit(f"{slug} item {index}: missing 例 route")
            if is_loop(route):
                continue

            key = (slug, index)
            if key in MANUAL_ROUTES:
                new_route = MANUAL_ROUTES[key]
            elif "→" in route:
                nodes = route_nodes(route)
                if len(nodes) < 2:
                    raise SystemExit(f"{slug} item {index}: route too short: {route}")
                new_route = route.rstrip("。").strip() + " → " + nodes[0]
            else:
                raise SystemExit(f"{slug} item {index}: non-arrow route needs manual mapping: {route}")

            new_text = replace_route(text, new_route)
            old_literal = json.dumps(text, ensure_ascii=False)
            new_literal = json.dumps(new_text, ensure_ascii=False)
            if raw.count(old_literal) != 1:
                raise SystemExit(f"{slug} item {index}: expected one exact text literal, found {raw.count(old_literal)}")
            raw = raw.replace(old_literal, new_literal, 1)
            item["text"] = new_text
            file_changed = True
            changed_items += 1

        if file_changed:
            json.loads(raw)
            path.write_text(raw, encoding="utf-8")
            changed_files += 1

    remaining = []
    for slug in slugs:
        data = json.loads((COUNTRY_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        for index, item in enumerate(data["travelScale"]["items"], 1):
            route = extract_route(item["text"])
            if not is_loop(route):
                remaining.append((slug, index, route))
    if remaining:
        raise SystemExit(f"Travel Scale round-trip migration incomplete: {remaining[:20]}")

    if total_items != 606:
        raise SystemExit(f"Expected 606 Travel Scale items, found {total_items}")

    print(f"Travel Scale round-trip migration: {changed_files} files / {changed_items} items; all 606 routes are loops.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
