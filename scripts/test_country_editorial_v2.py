#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("editorial", HERE / "validate_country_editorial_v2.py")
assert SPEC and SPEC.loader
editorial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(editorial)


def valid_v2_data() -> dict:
    return {
        "contentQaVersion": 2,
        "travelScale": {
            "kicker": "DURATION",
            "title": "旅の目安日程",
            "intro": "",
            "items": [
                {"duration": "3〜4日", "title": "短く見る", "text": "一地域に絞る。例：A → B → A。", "icon": "city"},
                {"duration": "7〜10日", "title": "二地域を見る", "text": "二地域をつなぐ。例：A → B → C。", "icon": "map"},
                {"duration": "14日以上", "title": "広く見る", "text": "遠い地域を加える。例：A → B → C → D。", "icon": "compass"},
            ],
        },
        "signatureFacts": [
            {"topicKey": "island-count", "label": "島", "value": "1,000", "note": "多くの島がある。"},
            {"topicKey": "volcano-count", "label": "活火山", "value": "100", "note": "火山景観が多い。"},
            {"topicKey": "heritage-count", "label": "世界遺産", "value": "10件", "note": "複数の遺産がある。"},
        ],
    }


def valid_v3_data() -> dict:
    return {
        "contentQaVersion": 3,
        "travelScale": {
            "kicker": "DURATION",
            "title": "旅の目安日程",
            "intro": "日数ではなく旅の広がりで選ぶ。",
            "items": [
                {"duration": "一都市中心", "title": "街を深く見る", "text": "拠点を絞る。例：Aを歩き、近郊Bを加える。", "icon": "city"},
                {"duration": "地域をつなぐ", "title": "主要地域を巡る", "text": "性格の違う地域を結ぶ。例：A → B → C。", "icon": "map"},
                {"duration": "広域周遊", "title": "国の幅を見る", "text": "遠い地域やテーマを組み合わせる。例：A → B → C → D。", "icon": "compass"},
            ],
        },
        "signatureFacts": [
            {"topicKey": "island-archipelago-scale", "label": "島", "value": "1,000", "note": "国土の広がりを数字で示す。"},
            {"topicKey": "volcanic-peaks", "label": "活火山", "value": "100", "note": "火山地形の規模を示す。"},
            {"topicKey": "rail-network-length", "label": "鉄道網", "value": "9,000km", "note": "移動網の規模を示す。"},
        ],
        "atlasExtras": [
            {"topicKey": "water-temple-ritual", "title": "水辺の祈り", "text": "水と信仰が暮らしの中で結びついている。", "points": ["共同体の儀礼", "水辺の空間"]},
            {"topicKey": "market-daily-life", "title": "市場が暮らしを映す", "text": "朝の市場では地域ごとの食材と商いが見える。", "points": ["朝の時間帯", "地域差"]},
            {"topicKey": "textile-village-craft", "title": "織物の村", "text": "手仕事が家族と地域の生業として続く。", "points": ["手織り", "村の仕事"]},
        ],
        "travelTrivia": [
            {"topicKey": "street-address-colors", "categoryJa": "街角", "title": "住所表示の色に注目", "text": "地区ごとに表示の見え方が少し違う。"},
            {"topicKey": "coffee-order-words", "categoryJa": "言葉", "title": "コーヒーの頼み方", "text": "注文語を知ると朝の店が少し楽しくなる。"},
            {"topicKey": "bus-stop-hand-signals", "categoryJa": "移動", "title": "バス停の合図", "text": "地域によって乗車時の合図に癖がある。"},
        ],
    }


def test_v2_valid() -> None:
    errors = editorial.validate_data(valid_v2_data(), "valid-v2.json")
    assert not errors, errors


def test_v2_missing_example_fails() -> None:
    data = valid_v2_data()
    data["travelScale"]["items"][1]["text"] = "二地域をつなぐ。"
    errors = editorial.validate_data(data, "missing-example.json")
    assert any("concrete example" in error for error in errors), errors


def test_moderate_forest_share_fails() -> None:
    data = valid_v2_data()
    data["signatureFacts"][0] = {
        "topicKey": "forest-share-52",
        "label": "森林・樹林地",
        "value": "約52%",
        "note": "国土のおよそ半分。",
        "exceptionalShare": True,
    }
    errors = editorial.validate_data(data, "forest-52.json")
    assert any("not distinctive enough" in error for error in errors), errors


def test_extreme_forest_share_requires_flag() -> None:
    data = valid_v2_data()
    data["signatureFacts"][0] = {
        "topicKey": "forest-share-75",
        "label": "森林",
        "value": "75%",
        "note": "国土の大半が森林。",
    }
    errors = editorial.validate_data(data, "forest-flag.json")
    assert any("exceptionalShare:true" in error for error in errors), errors


def test_extreme_forest_share_passes_with_flag() -> None:
    for pct in (5, 75):
        data = valid_v2_data()
        data["signatureFacts"][0] = {
            "topicKey": f"forest-share-{pct}",
            "label": "森林",
            "value": f"{pct}%",
            "note": "極端な森林率。",
            "exceptionalShare": True,
        }
        errors = editorial.validate_data(data, f"forest-{pct}.json")
        assert not errors, errors


def test_v3_valid() -> None:
    errors = editorial.validate_data(valid_v3_data(), "valid-v3.json")
    assert not errors, errors


def test_v3_day_count_in_duration_fails() -> None:
    data = valid_v3_data()
    data["travelScale"]["items"][0]["duration"] = "3日"
    errors = editorial.validate_data(data, "v3-day-duration.json")
    assert any("forbids numeric stay/day/week counts" in error for error in errors), errors


def test_v3_day_count_in_body_fails() -> None:
    data = valid_v3_data()
    data["travelScale"]["items"][1]["text"] = "5〜7日で主要地域をつなぐ。例：A → B → C。"
    errors = editorial.validate_data(data, "v3-day-body.json")
    assert any("forbids numeric stay/day/week counts" in error for error in errors), errors


def test_v3_duplicate_topic_across_sections_fails() -> None:
    data = valid_v3_data()
    data["travelTrivia"][0]["topicKey"] = "island-archipelago-scale"
    errors = editorial.validate_data(data, "v3-topic-duplicate.json")
    assert any("duplicate topicKey" in error for error in errors), errors


def test_v3_renamed_same_topic_fails() -> None:
    data = valid_v3_data()
    data["signatureFacts"][0]["topicKey"] = "heritage-count"
    data["atlasExtras"][0]["topicKey"] = "heritage-history"
    errors = editorial.validate_data(data, "v3-topic-canonical.json")
    assert any("semantic topic collision" in error for error in errors), errors


def test_v3_near_duplicate_copy_fails() -> None:
    data = valid_v3_data()
    data["signatureFacts"][0].update({
        "topicKey": "archipelago-scale",
        "label": "島の数",
        "value": "1,000",
        "note": "多くの島が連なり、国土の広がりをつくっている。",
    })
    data["atlasExtras"][0].update({
        "topicKey": "island-geography",
        "title": "多くの島が連なる国",
        "text": "多くの島が連なり、国土の広がりをつくっている。",
        "points": ["島が連なる", "国土が広がる"],
    })
    errors = editorial.validate_data(data, "v3-copy-duplicate.json")
    assert any("near-duplicate copy" in error for error in errors), errors


def test_protocol2_pilot_countries_stay_v2_compatible() -> None:
    for slug in ("japan", "indonesia", "cambodia", "northkorea"):
        path = ROOT / "data" / "countries" / f"{slug}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = editorial.validate_data(data, path.name, force=True)
        assert not errors, f"{slug}: {errors}"


if __name__ == "__main__":
    test_v2_valid()
    test_v2_missing_example_fails()
    test_moderate_forest_share_fails()
    test_extreme_forest_share_requires_flag()
    test_extreme_forest_share_passes_with_flag()
    test_v3_valid()
    test_v3_day_count_in_duration_fails()
    test_v3_day_count_in_body_fails()
    test_v3_duplicate_topic_across_sections_fails()
    test_v3_renamed_same_topic_fails()
    test_v3_near_duplicate_copy_fails()
    test_protocol2_pilot_countries_stay_v2_compatible()
    print("Editorial Content QA regression tests passed for v2 compatibility and v3 rules")
