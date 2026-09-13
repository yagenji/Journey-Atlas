#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one exact match, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def regex_once(path: str, pattern: str, replacement: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{path}: expected one regex match, found {count}")
    p.write_text(new_text, encoding="utf-8")


# Content QA v3: retain topic-separation rules, restore day-based Travel Scale.
regex_once(
    "docs/CONTENT_QUALITY_RULES_V3.md",
    r"## 1\. Travel Scale uses travel scope, not day counts\n.*?\n## 2\.",
    """## 1. Travel Scale keeps country-specific day ranges

`travelScale` remains a three-step UI and must show a concrete day range for each stage.
Content QA v3 keeps the established Travel Scale duration contract; v3 adds cross-section topic separation, not removal of duration guidance.

Each item contains:

- `duration`
- `title`
- `text`
- fixed icon sequence `city` / `map` / `compass`
- a concrete itinerary/example introduced by `例：`

Rules:

- all three `duration` values use **days (`日`)**; do not mix weeks and days;
- the first and second stages may use a single day count or a range such as `3〜4日` / `5〜7日`;
- the third stage is always open-ended in the form `○日以上`;
- day ranges are country-specific and should reflect geographic scale, attraction dispersion, domestic transport burden, and realistic routing;
- small countries may use shorter ranges; large countries may use longer ranges;
- do not inflate or compress durations merely to fit a fixed template;
- every stage still requires a representative route introduced by `例：`.

The section should explain both **how long** and **how to compose** the trip. The example route should remain representative rather than exhaustive.

## 2.""",
)

# Shared Country Page template: restore the previously locked day-based contract.
regex_once(
    "docs/COUNTRY_PAGE_TEMPLATE.md",
    r"### travelScale\n\n.*?\n### seasons",
    """### travelScale

旅の目安日程は3段階のUI構造を共通化するが、日数の閾値は国ごとに可変とする。

- 固定：3項目、`DURATION`、`旅の目安日程`、`city / map / compass` の順。
- **日程表記は全3段階とも「日」に統一し、第3段階は必ず上限を置かず `○日以上` とする。**
- 例：`3〜4日 / 5〜7日 / 8日以上`。
- 小国なら `半日〜1日 / 2日 / 3日以上` のように短縮してよい。
- 広域国なら `3〜4日 / 7〜10日 / 12日以上` のように拡張してよい。
- 第3段階は「その日数で旅が終わる」という上限ではなく、地域やテーマをさらに広げられる長期滞在の入口として扱う。
- 各段階の `例：` は必須。網羅リストではなく、旅の流れを理解するための代表ルートに絞る。原則3〜6地点程度とし、8景や主要スポットをすべて詰め込まない。
- 面積だけでなく、見どころの分散、地域差、島嶼・山岳、国内移動負荷、実際に成立する旅程で決める。
- テンプレートを埋めるための日数水増し、または大国を固定日数へ圧縮することを禁止する。

### seasons""",
)
replace_once(
    "docs/COUNTRY_PAGE_TEMPLATE.md",
    "8. Content QA v3では、Travel Scaleの日数表記がなく、`signatureFacts / atlasExtras / travelTrivia` にtopic duplicationがない。",
    "8. Content QA v3では、Travel Scaleが全3段階とも日表記で、第3段階が `○日以上` となり、`signatureFacts / atlasExtras / travelTrivia` にtopic duplicationがない。",
)

# New Country start guide.
replace_once(
    "docs/NEW_COUNTRY_START.md",
    "- 旅の目安日程に具体的な日数・泊数・週数を入れてはいけません。`3日` / `4〜5日` / `7日以上` / `2泊3日` / `1週間` / `日帰り` 等は禁止です。\n- Travel Scaleは日数ではなく、旅の広がり・地域の組み合わせ・移動の組み立て方で表現してください。基本ラベルは `一都市中心 / 地域をつなぐ / 広域周遊` とします。",
    "- Travel Scaleは全3段階とも日数を表示し、単位は `日` に統一してください。週・泊との混在は避けます。\n- 第3段階は必ず上限を置かない `○日以上` とします。小国は短縮、大国は拡張し、国土・見どころの分散・移動負荷に合わせて日数を決めてください。",
)

# Protocol patch 5 records the restoration as a shared rule correction.
replace_once(
    "docs/COUNTRY_PRODUCTION_PROTOCOL_2.md",
    "Current policy patch: 4",
    "Current policy patch: 5",
)
replace_once(
    "docs/COUNTRY_PRODUCTION_PROTOCOL_2.md",
    "Protocol 2.0 is the default for **new Country production**. Patch 4 preserves the post-image fast path and Image Policy 7.2 controls, and advances new Country editorial production to Content QA v3.",
    "Protocol 2.0 is the default for **new Country production**. Patch 5 preserves the post-image fast path and Image Policy 7.2 controls, keeps Content QA v3 topic-separation rules, and restores the shared day-based Travel Scale contract.",
)
replace_once(
    "docs/COUNTRY_PRODUCTION_PROTOCOL_2.md",
    "New Countries created under policy patch 4 use `contentQaVersion: 3` and must follow `docs/CONTENT_QUALITY_RULES_V3.md`.",
    "New Countries created under policy patch 5 use `contentQaVersion: 3` and must follow `docs/CONTENT_QUALITY_RULES_V3.md`.",
)

# Editorial validator: v3 uses the same day-format rules as v2, plus v3 topic rules elsewhere.
replace_once(
    "scripts/validate_country_editorial_v2.py",
    "- no numeric stay/day/week counts in Travel Scale;",
    "- the established day-based Travel Scale contract;",
)
regex_once(
    "scripts/validate_country_editorial_v2.py",
    r"def validate_travel_scale_v3\(errors: list\[str\], filename: str, data: dict\[str, Any\]\) -> None:\n.*?\n\ndef forest_related",
    """def validate_travel_scale_v3(errors: list[str], filename: str, data: dict[str, Any]) -> None:
    # Content QA v3 adds semantic topic-separation rules but keeps the shared
    # day-based Travel Scale duration contract used across JOURNEY ATLAS.
    validate_travel_scale_v2(errors, filename, data)


def forest_related""",
)

# Published strict validator applies the day rule to every content QA version.
replace_once(
    "scripts/validate_country.py",
    "            elif data.get(\"contentQaVersion\", 1) < 3:\n                # Content QA v3 intentionally uses qualitative travel-scope labels.\n                # Its no-duration-count rule is enforced by validate_country_editorial_v2.py.\n                # Keep the legacy published day-format gate only for v1/v2 Countries.\n",
    "            else:\n",
)

# New Country scaffold restores visible day ranges.
replace_once(
    "scripts/new_country.py",
    "        \"intro\": \"日数ではなく、旅の広がりと組み合わせ方で選ぶ。\",\n        \"items\": [\n            {\"duration\": \"一都市中心\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"city\"},\n            {\"duration\": \"地域をつなぐ\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"map\"},\n            {\"duration\": \"広域周遊\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"compass\"},\n        ],",
    "        \"intro\": \"\",\n        \"items\": [\n            {\"duration\": \"3〜4日\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"city\"},\n            {\"duration\": \"5〜7日\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"map\"},\n            {\"duration\": \"8日以上\", \"title\": \"\", \"text\": \"例：\", \"icon\": \"compass\"},\n        ],",
)

# Regression fixture: v3 keeps day durations while preserving semantic v3 checks.
p = ROOT / "scripts/test_country_editorial_v2.py"
text = p.read_text(encoding="utf-8")
text = text.replace('"intro": "日数ではなく旅の広がりで選ぶ。"', '"intro": ""', 1)
text = text.replace('{"duration": "一都市中心", "title": "街を深く見る"', '{"duration": "3〜4日", "title": "街を深く見る"', 1)
text = text.replace('{"duration": "地域をつなぐ", "title": "主要地域を巡る"', '{"duration": "5〜7日", "title": "主要地域を巡る"', 1)
text = text.replace('{"duration": "広域周遊", "title": "国の幅を見る"', '{"duration": "8日以上", "title": "国の幅を見る"', 1)
text, count = re.subn(
    r"def test_v3_day_count_in_duration_fails\(\) -> None:\n.*?\n\ndef test_v3_duplicate_topic_across_sections_fails",
    """def test_v3_day_ranges_are_valid() -> None:
    data = valid_v3_data()
    errors = editorial.validate_data(data, "v3-day-ranges.json")
    assert not any("duration must use day notation" in error for error in errors), errors
    assert not any("final travelScale duration" in error for error in errors), errors


def test_v3_non_day_duration_fails() -> None:
    data = valid_v3_data()
    data["travelScale"]["items"][0]["duration"] = "一都市中心"
    errors = editorial.validate_data(data, "v3-non-day-duration.json")
    assert any("duration must use day notation" in error for error in errors), errors


def test_v3_final_duration_must_be_open_ended() -> None:
    data = valid_v3_data()
    data["travelScale"]["items"][2]["duration"] = "8〜10日"
    errors = editorial.validate_data(data, "v3-final-closed.json")
    assert any("final travelScale duration must be '○日以上'" in error for error in errors), errors


def test_v3_duplicate_topic_across_sections_fails""",
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit(f"scripts/test_country_editorial_v2.py: v3 test block match count {count}")
text = text.replace("    test_v3_day_count_in_duration_fails()\n    test_v3_day_count_in_body_fails()\n    test_v3_week_count_fails()", "    test_v3_day_ranges_are_valid()\n    test_v3_non_day_duration_fails()\n    test_v3_final_duration_must_be_open_ended()", 1)
p.write_text(text, encoding="utf-8")

# Machine-readable policy patch 5.
p = ROOT / "ops/country-production-policy.json"
policy = json.loads(p.read_text(encoding="utf-8"))
policy["policyPatch"] = 5
policy["updatedAt"] = "2026-09-13T22:14:00+09:00"
cq = policy["contentQuality"]
cq["travelScaleNumericDurationForbidden"] = False
cq["travelScaleDayCountForbidden"] = False
cq["travelScaleDurationUnitsForbidden"] = ["泊", "週", "週間"]
cq["travelScaleThirdItemOpenEndedDayRule"] = True
cq["travelScaleDayNotationRequired"] = True
p.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Kazakhstan: restore country-appropriate durations without changing routes/content.
p = ROOT / "data/countries/kazakhstan.json"
data = json.loads(p.read_text(encoding="utf-8"))
items = data["travelScale"]["items"]
if len(items) != 3:
    raise SystemExit("Kazakhstan travelScale must have exactly 3 items")
for item, duration in zip(items, ["4〜5日", "7〜9日", "12日以上"]):
    item["duration"] = duration
p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

print("Restored day-based Travel Scale contract and Kazakhstan durations")
