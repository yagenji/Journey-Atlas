#!/usr/bin/env python3
"""Temporary one-shot Travel Scale route-loop remediation for the 202-destination audit."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "data" / "countries"
REGISTRY = ROOT / "data" / "atlas-destinations.json"
ARROW_RE = re.compile(r"\s*[→➡➜]\s*")

# Human-reviewed route completions for examples that cannot be safely inferred
# from the repeated-base heuristic. These alter only the text after 「例：」.
OVERRIDES: dict[tuple[str, int], str] = {
    ("uzbekistan", 3): "タシュケント → サマルカンド → ブハラ → ヒヴァ → フェルガナ → タシュケント",
    ("saudiarabia", 3): "ジェッダ → アルウラ／ヘグラ → タブーク → ワディ・アル・ディサ → ジェッダ",
    ("belize", 2): "キー・カーカー → ベリーズ・シティ → サン・イグナシオ → シュナントゥニッチ → キー・カーカー",
    ("belize", 3): "ベリーズ・シティ → クルックド・ツリー → ラマナイ → サン・イグナシオ → ホプキンス → キー・カーカー → ベリーズ・シティ",
    ("tanzania", 3): "ダルエスサラーム → ニエレレ → ルアハ → ダルエスサラーム",
    ("andorra", 1): "アンドラ・ラ・ベリャ／エスカルデス → カニーリョ → オルディノ → アンドラ・ラ・ベリャ／エスカルデス",
    ("bahrain", 1): "マナーマ → バーレーン要塞 → バブ・アル・バーレーン → アル・ファテフ・モスク → バーレーン・ベイ → ムハッラク真珠採取の道 → マナーマ",
    ("bahrain", 3): "ムハッラク → マナーマ → アアリ → アル・ジャスラ → サヒール → 南岸 → ハワール諸島 → ムハッラク",
    ("bhutan", 3): "パロ → ティンプー → フォブジカ → トンサ → ブムタン → パロ",
    ("cambodia", 1): "シェムリアップ → アンコール遺跡群 → トンレサップ → シェムリアップ",
    ("canada", 1): "バンクーバー → バンクーバー島 → バンクーバー",
    ("canada", 2): "トロント → ナイアガラ → モントリオール → ケベック・シティ → トロント",
    ("canada", 3): "バンクーバー → カナディアン・ロッキー → カルガリー → バンクーバー",
    ("croatia", 1): "スプリト → トロギール → スプリト",
    ("dominicanrepublic", 1): "サントドミンゴ旧市街 → ロス・トレス・オホス → サントドミンゴ旧市街",
    ("elsalvador", 2): "サン・サルバドル → アパネカ高地 → ホヤ・デ・セレン → スチトト → 太平洋岸 → サン・サルバドル",
    ("elsalvador", 3): "サン・サルバドル → 西部火山地帯 → ヒキリスコ湾 → コンチャグア → サン・サルバドル",
    ("equatorialguinea", 3): "マラボ → ビオコ島 → リオ・ムニ → コリスコ／アンノボン → マラボ",
    ("germany", 3): "ハンブルク → ベルリン → ライン渓谷 → ハイデルベルク → ミュンヘン → ハンブルク",
    ("honduras", 1): "サン・ペドロ・スーラ → コパン・ルイナス → コパン考古公園 → サン・ペドロ・スーラ",
    ("jamaica", 1): "キングストン中心部 → 街路・文化施設 → キングストン中心部",
    ("kiribati", 1): "ボンリキ → 南タラワ → ベティオ → ボンリキ",
    ("kiribati", 3): "タラワ → キリスィマスィ島 → タラワ",
    ("kuwait", 1): "クウェート市 → クウェート・タワーズ → グランド・モスク → ムバラキーヤ市場 → サドゥ・ハウス → クウェート市",
    ("malta", 3): "マルタ島 → ゴゾ島 → コミノ島 → マルタ島",
    ("marshallislands", 1): "ウリガ → 平和記念公園 → ラウラ → ウリガ",
    ("morocco", 2): "カサブランカ → ラバト → フェズ → シェフシャウエン → タンジェ → カサブランカ",
    ("newzealand", 1): "ウェリントン → トンガリロ → ロトルア → ウェリントン",
    ("newzealand", 2): "オークランド → ロトルア → トンガリロ → クライストチャーチ → テカポ → アオラキ → オークランド",
    ("newzealand", 3): "オークランド → ロトルア → トンガリロ → クライストチャーチ → テカポ → 西海岸 → クイーンズタウン／ミルフォード・サウンド → オークランド",
    ("norway", 1): "ベルゲン → フロム → ネーロイフィヨルド → ベルゲン",
    ("palau", 1): "コロール → ロックアイランド → ジェリーフィッシュ・レイク → コロール",
    ("palau", 2): "コロール → ガラスマオの滝 → バドルルアウ → アイライのバイ → コロール",
    ("palau", 3): "コロール → ペリリュー → カヤンゲル → コロール",
    ("philippines", 1): "セブ → ボホール → パングラオ → セブ",
    ("qatar", 1): "ドーハ → コーニッシュ → イスラム美術館 → スーク・ワキーフ → カタール国立博物館 → カタラ → ドーハ",
    ("stkittsnevis", 3): "バセテール → リアムイガ山麓 → ロムニー・マナー → チャールズタウン → ネービス・ピーク山麓 → バセテール",
    ("stlucia", 3): "カストリーズ → 北西岸 → マリゴ湾 → スフリエール → ギミー山周辺の森 → デナリー → カストリーズ",
    ("singapore", 1): "マリーナ・ベイ → カンポン・グラム → チャイナタウン → ホーカーセンター → マリーナ・ベイ",
    ("singapore", 2): "ジョー・チアット → シンガポール植物園 → マクリッチー貯水池 → ジョー・チアット",
    ("singapore", 3): "シンガポール中心部 → チェク・ジャワ（プラウ・ウビン） → スンゲイ・ブロー → HDB住宅地 → シンガポール中心部",
    ("solomonislands", 1): "ホニアラ中央市場 → ボネギ → テナル滝 → ホニアラ中央市場",
    ("srilanka", 3): "ジャフナ → アヌラーダプラ → シギリヤ → キャンディ → エッラ → ヤーラ → ゴール → コロンボ",
    ("switzerland", 1): "インターラーケン → ラウターブルンネン → グリンデルワルト → インターラーケン",
    ("tonga", 3): "トンガタプ → ヴァヴァウ → ハアパイ → トンガタプ",
    ("trinidadtobago", 3): "ポート・オブ・スペイン → トリニダード各地 → スカーバラ → アーガイル滝 → メイン・リッジ → ピジョン・ポイント → ポート・オブ・スペイン",
    ("turkiye", 1): "スルタンアフメト → エミノニュ → カラキョイ → カドゥキョイ → スルタンアフメト",
    ("tuvalu", 1): "フナフティ空港 → フォンガファレの集落 → ラグーン側 → 夕方の滑走路 → フナフティ空港",
    ("unitedarabemirates", 1): "アブダビ中心部 → シェイク・ザイード・グランド・モスク → 海岸部 → アブダビ中心部",
    ("unitedarabemirates", 2): "ドバイ → アブダビ → アル・アイン → ドバイ",
    ("unitedstates", 1): "ニューヨーク → ワシントンD.C. → ニューヨーク／サンフランシスコ → ヨセミテ → サンフランシスコ",
    ("unitedstates", 2): "サンフランシスコ → ヨセミテ → ロサンゼルス → グランドキャニオン → サンフランシスコ",
    ("hong-kong", 1): "セントラル → ピーク → スターフェリー → 九龍 → 志蓮淨苑 → セントラル",
    ("hong-kong", 3): "香港島 → 米埔 → 西貢・東壩 → 茘枝窩 → 香港島",
    ("macau", 1): "セナド広場 → 媽閣廟 → リラウ → 聖ポール天主堂跡 → セナド広場",
    ("macau", 2): "マカオ半島 → タイパ → コタイ → コロアン村 → 黒沙海灘 → マカオ半島",
}

# Deliberate exceptions: either a practical open-jaw ending already exists, or
# current safety conditions make a prescriptive circuit inappropriate.
EXCEPTIONS: set[tuple[str, int]] = {
    ("namibia", 3),
    ("burkinafaso", 3),
    ("chad", 2), ("chad", 3),
    ("haiti", 1), ("haiti", 2), ("haiti", 3),
    ("indonesia", 3),
    ("iran", 1), ("iran", 3),
    ("iraq", 1), ("iraq", 3),
    ("jordan", 3),
    ("mali", 3),
    ("mauritania", 3),
    ("niger", 3),
    ("somalia", 2), ("somalia", 3),
    ("sudan", 3),
    ("unitedstates", 3),
    ("yemen", 1),
    ("macau", 3),
    ("palestine", 1), ("palestine", 3),
}


def clean_node(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return re.sub(r"[。．.!！?？、,;；:：]+$", "", value).strip()


def semantic_key(value: str) -> str:
    value = clean_node(value)
    value = re.sub(r"（.*?）", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    for word in ("滞在", "周辺", "中心部"):
        value = value.replace(word, "")
    return value.strip()


def first_route_node(text: str) -> str:
    m = re.search(r"例[:：]\s*(.+?)(?:。|$)", text)
    if not m:
        return ""
    route = m.group(1).strip()
    if re.search(r"[→➡➜]", route):
        return semantic_key(ARROW_RE.split(route)[0])
    if "＋" in route:
        return semantic_key(route.split("＋", 1)[0])
    return ""


def returned_to_base(first: str, later: str) -> bool:
    key = semantic_key(first)
    later_key = semantic_key(later)
    if key and key in later_key:
        return True
    for part in re.split(r"[・/／]", key):
        part = part.strip()
        if len(part) >= 2 and part in later_key:
            return True
    return False


def make_loop(route: str, bases: set[str]) -> tuple[str, bool]:
    route = route.strip()
    if not route:
        return route, False
    if re.search(r"[→➡➜]", route):
        nodes = [clean_node(x) for x in ARROW_RE.split(route) if clean_node(x)]
        if len(nodes) < 2:
            return route, False
        first = nodes[0]
        first_key = semantic_key(first)
        later = " ".join(nodes[1:])
        if returned_to_base(first, later):
            return route, False
        if first_key not in bases:
            return route, False
        return f"{route} → {first}", True
    if "＋" in route:
        parts = [clean_node(x) for x in route.split("＋") if clean_node(x)]
        if 2 <= len(parts) <= 6 and all(len(x) <= 32 for x in parts):
            if semantic_key(parts[0]) in bases:
                return " → ".join(parts + [parts[0]]), True
    return route, False


def replace_route(text: str, route: str) -> str:
    m = re.search(r"(例[:：]\s*)(.+?)(。|$)", text)
    if not m:
        return text
    return text[:m.start(2)] + route + text[m.end(2):]


def rewrite_text(text: str, bases: set[str]) -> tuple[str, bool]:
    m = re.search(r"(例[:：]\s*)(.+?)(。|$)", text)
    if not m:
        return text, False
    route = m.group(2).strip()
    new_route, changed = make_loop(route, bases)
    if not changed:
        return text, False
    return text[:m.start(2)] + new_route + text[m.end(2):], True


def replace_json_string_once(raw: str, old: str, new: str, start: int) -> tuple[str, int]:
    old_token = json.dumps(old, ensure_ascii=False)
    new_token = json.dumps(new, ensure_ascii=False)
    idx = raw.find(old_token, start)
    if idx < 0:
        raise RuntimeError("Could not locate Travel Scale text token for targeted replacement")
    return raw[:idx] + new_token + raw[idx + len(old_token):], idx + len(new_token)


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    slugs = [row["slug"] for row in registry.get("destinations", []) if row.get("atlasPublished")]
    changed_files = 0
    changed_items = 0
    skipped = []

    for slug in slugs:
        path = COUNTRY_DIR / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        items = ((data.get("travelScale") or {}).get("items") or [])
        first_nodes = [first_route_node(item.get("text", "")) for item in items if isinstance(item, dict)]
        counts = Counter(node for node in first_nodes if node)
        bases = {node for node, count in counts.items() if count >= 2}
        capital = semantic_key(((data.get("capital") or {}).get("nameJa") or ""))
        if capital:
            bases.add(capital)

        replacements: list[tuple[str, str]] = []
        for index, item in enumerate(items, 1):
            old = item.get("text") if isinstance(item, dict) else None
            if not isinstance(old, str):
                continue
            key = (slug, index)
            if key in OVERRIDES:
                new = replace_route(old, OVERRIDES[key])
                if new != old:
                    replacements.append((old, new))
                continue
            if key in EXCEPTIONS:
                continue
            new, changed = rewrite_text(old, bases)
            if changed:
                replacements.append((old, new))
            else:
                m = re.search(r"例[:：]\s*(.+)$", old)
                if m:
                    route = m.group(1).strip()
                    first_sentence = route.split("。", 1)[0]
                    if re.search(r"[→➡➜]", first_sentence):
                        nodes = [clean_node(x) for x in ARROW_RE.split(first_sentence) if clean_node(x)]
                        if len(nodes) >= 2 and not returned_to_base(nodes[0], " ".join(nodes[1:])):
                            skipped.append((slug, index, route))
                    elif "＋" in first_sentence:
                        skipped.append((slug, index, route))
                    else:
                        skipped.append((slug, index, route))

        if not replacements:
            continue
        raw = path.read_text(encoding="utf-8")
        travel_pos = raw.find('"travelScale"')
        if travel_pos < 0:
            raise RuntimeError(f"{slug}: travelScale token missing")
        cursor = travel_pos
        for old, new in replacements:
            raw, cursor = replace_json_string_once(raw, old, new, cursor)
        path.write_text(raw, encoding="utf-8")
        changed_files += 1
        changed_items += len(replacements)

    print(f"TRAVEL_SCALE_REMEDIATION changed_files={changed_files} changed_items={changed_items}")
    print(f"TRAVEL_SCALE_REMEDIATION_REVIEW remaining={len(skipped)}")
    for row in skipped:
        print("REVIEW|" + "|".join(str(x).replace("\n", " ") for x in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
