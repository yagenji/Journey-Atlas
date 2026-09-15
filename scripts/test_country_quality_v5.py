#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("quality_v5", HERE / "validate_country_quality_v5.py")
assert SPEC and SPEC.loader
quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)


def signature_item(**overrides) -> dict:
    item = {
        "topicKey": "country-distinctive-number",
        "label": "特別な数字",
        "value": "123",
        "note": "この数字を見ると、その国の地理的な特徴を具体的に想像できる。",
        "icon": "map",
        "interestReason": "国の見え方を変える具体的な規模感が一目で伝わるため。",
    }
    item.update(overrides)
    return item


def base_data() -> dict:
    return {
        "contentQaVersion": 5,
        "map": {
            "bounds": {"north": 10.0, "south": 0.0, "west": 0.0, "east": 10.0},
        },
        "capital": {
            "nameJa": "首都",
            "nameEn": "Capital",
            "coordinates": {"latitude": 5.0, "longitude": 5.0},
            "labelPosition": "right",
        },
        "scenes": [
            {
                "coordinates": {"latitude": 5.0, "longitude": 5.65},
            }
        ],
        "signatureFacts": [
            signature_item(topicKey="country-number-a"),
            signature_item(topicKey="country-number-b"),
            signature_item(topicKey="country-number-c"),
        ],
    }


def test_capital_label_scene_collision_fails() -> None:
    data = base_data()
    errors = quality.validate_data(data, "collision.json")
    assert any("capital name label overlaps Scene 1" in error for error in errors), errors


def test_capital_label_side_change_resolves_collision() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    errors = quality.validate_data(data, "resolved.json")
    assert not errors, errors


def test_small_world_heritage_count_fails() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count",
        label="世界遺産",
        value="8件",
        note="国内に8件の世界遺産がある。",
        exceptionalHeritageCount=True,
    )
    errors = quality.validate_data(data, "heritage-small.json")
    assert any("exceptionally high" in error for error in errors), errors


def test_large_world_heritage_count_requires_explicit_exception() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count",
        label="世界遺産",
        value="30件",
        note="世界でも多い水準の30件が国土に分布する。",
    )
    errors = quality.validate_data(data, "heritage-flag.json")
    assert any("exceptionalHeritageCount:true" in error for error in errors), errors


def test_large_world_heritage_count_with_exception_passes() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count",
        label="世界遺産",
        value="30件",
        note="世界でも多い水準の30件が国土に分布し、歴史層の厚さが数字に表れる。",
        exceptionalHeritageCount=True,
        interestReason="世界でも突出した件数で、歴史層の厚さを一目で想像できるため。",
    )
    errors = quality.validate_data(data, "heritage-valid.json")
    assert not errors, errors


def test_moderate_forest_share_fails() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-forest-share",
        label="森林率",
        value="48%",
        note="国土の48%を森林が占める。",
        exceptionalShare=True,
    )
    errors = quality.validate_data(data, "forest-moderate.json")
    assert any("not extreme enough" in error for error in errors), errors


def test_extreme_forest_share_passes_with_exception() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-forest-share",
        label="森林率",
        value="82%",
        note="国土の82%を森林が占め、地図上の国土像そのものを特徴づける。",
        exceptionalShare=True,
        interestReason="国土の大半が森林という極端な土地利用が旅の景観を決めるため。",
    )
    errors = quality.validate_data(data, "forest-extreme.json")
    assert not errors, errors


def test_interest_reason_required() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][1].pop("interestReason")
    errors = quality.validate_data(data, "interest.json")
    assert any("interestReason is required" in error for error in errors), errors


def test_v4_is_not_retroactively_invalidated() -> None:
    data = base_data()
    data["contentQaVersion"] = 4
    assert not quality.validate_data(data, "legacy-v4.json")


if __name__ == "__main__":
    test_capital_label_scene_collision_fails()
    test_capital_label_side_change_resolves_collision()
    test_small_world_heritage_count_fails()
    test_large_world_heritage_count_requires_explicit_exception()
    test_large_world_heritage_count_with_exception_passes()
    test_moderate_forest_share_fails()
    test_extreme_forest_share_passes_with_exception()
    test_interest_reason_required()
    test_v4_is_not_retroactively_invalidated()
    print("Content QA v5 regression tests passed")
