#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("editorial_v2", HERE / "validate_country_editorial_v2.py")
assert SPEC and SPEC.loader
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)


def valid_data() -> dict:
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


def test_valid() -> None:
    errors = v2.validate_data(valid_data(), "valid.json")
    assert not errors, errors


def test_missing_example_fails() -> None:
    data = valid_data()
    data["travelScale"]["items"][1]["text"] = "二地域をつなぐ。"
    errors = v2.validate_data(data, "missing-example.json")
    assert any("concrete example" in error for error in errors), errors


def test_moderate_forest_share_fails() -> None:
    data = valid_data()
    data["signatureFacts"][0] = {
        "topicKey": "forest-share-52",
        "label": "森林・樹林地",
        "value": "約52%",
        "note": "国土のおよそ半分。",
        "exceptionalShare": True,
    }
    errors = v2.validate_data(data, "forest-52.json")
    assert any("not distinctive enough" in error for error in errors), errors


def test_extreme_forest_share_requires_flag() -> None:
    data = valid_data()
    data["signatureFacts"][0] = {
        "topicKey": "forest-share-75",
        "label": "森林",
        "value": "75%",
        "note": "国土の大半が森林。",
    }
    errors = v2.validate_data(data, "forest-flag.json")
    assert any("exceptionalShare:true" in error for error in errors), errors


def test_extreme_forest_share_passes_with_flag() -> None:
    for pct in (5, 75):
        data = valid_data()
        data["signatureFacts"][0] = {
            "topicKey": f"forest-share-{pct}",
            "label": "森林",
            "value": f"{pct}%",
            "note": "極端な森林率。",
            "exceptionalShare": True,
        }
        errors = v2.validate_data(data, f"forest-{pct}.json")
        assert not errors, errors


def test_non_forest_percentage_is_allowed() -> None:
    data = valid_data()
    data["signatureFacts"][0] = {
        "topicKey": "java-population-share",
        "label": "一つの島に住む人口",
        "value": "55.65%",
        "note": "人口集中を示す。",
    }
    errors = v2.validate_data(data, "population-share.json")
    assert not errors, errors


if __name__ == "__main__":
    test_valid()
    test_missing_example_fails()
    test_moderate_forest_share_fails()
    test_extreme_forest_share_requires_flag()
    test_extreme_forest_share_passes_with_flag()
    test_non_forest_percentage_is_allowed()
    print("Editorial Content QA v2 regression tests passed")
