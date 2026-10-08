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
        "value": "123km",
        "note": "この数字を見ると、その国の地理的な特徴を具体的に想像できる。",
        "icon": "map",
        "interestReason": "国の見え方を変える具体的な規模感が一目で伝わるため。",
    }
    item.update(overrides)
    return item


def base_data() -> dict:
    return {
        "contentQaVersion": 5,
        "nameEn": "Example",
        "nameJa": "例国",
        "map": {"bounds": {"north": 10.0, "south": 0.0, "west": 0.0, "east": 10.0}},
        "capital": {"nameJa": "首都", "nameEn": "Capital", "coordinates": {"latitude": 5.0, "longitude": 5.0}, "labelPosition": "right"},
        "scenes": [{"coordinates": {"latitude": 5.0, "longitude": 5.65}}],
        "signatureFacts": [
            signature_item(topicKey="country-number-a"),
            signature_item(topicKey="country-number-b"),
            signature_item(topicKey="country-number-c"),
        ],
    }


def v6_data() -> dict:
    data = base_data()
    data["contentQaVersion"] = 6
    data["capital"]["labelPosition"] = "left"
    data["taste"] = {"kicker": "TASTE OF EXAMPLE", "title": "例国で食べたいもの", "intro": "", "items": []}
    data["nextRoutes"] = []
    data["relatedCountries"] = [
        {"slug": "a", "nameEn": "A", "nameJa": "A", "flag": "", "reason": "山岳景観と長距離移動を楽しむ旅の感覚が近い。", "affinityType": "LANDSCAPE"},
        {"slug": "b", "nameEn": "B", "nameJa": "B", "flag": "", "reason": "歴史都市を歩きながら地域文化を追う旅が好きな人に合う。", "affinityType": "HISTORY"},
        {"slug": "c", "nameEn": "C", "nameJa": "C", "flag": "", "reason": "市場や日常の食文化を旅の中心に置く人に相性がよい。", "affinityType": "FOOD"},
    ]
    categories = ["LANDSCAPE", "CITY", "DAILY_LIFE", "MOVEMENT", "FOOD", "WILDLIFE", "FAITH", "CULTURE"]
    data["encounters"] = [{"title": f"出会い{index}", "category": category} for index, category in enumerate(categories, 1)]
    data["atlasExtras"] = [{"topicKey": "river-delta-life", "title": "川と暮らし", "text": "", "points": []}]
    data["travelTrivia"] = [{"topicKey": "market-opening-custom", "title": "市場の習慣", "text": ""}]
    return data


def test_capital_label_scene_collision_fails() -> None:
    data = base_data()
    errors = quality.validate_data(data, "collision.json")
    assert any("capital name label overlaps Scene 1" in error for error in errors), errors


def test_capital_label_side_change_resolves_collision() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    assert not quality.validate_data(data, "resolved.json")


def test_world_heritage_29_fails_even_with_count_exception() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count", label="世界遺産", value="29件",
        note="国内に29件の世界遺産がある。", exceptionalHeritageCount=True,
    )
    errors = quality.validate_data(data, "heritage-29.json")
    assert any(">= 30" in error for error in errors), errors


def test_world_heritage_30_requires_explicit_exception() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count", label="世界遺産", value="30件",
        note="世界でも多い水準の30件が国土に分布する。",
    )
    errors = quality.validate_data(data, "heritage-flag.json")
    assert any("exceptionalHeritageCount:true" in error for error in errors), errors


def test_world_heritage_30_with_exception_passes() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-world-heritage-count", label="世界遺産", value="30件",
        note="世界でも多い水準の30件が国土に分布し、歴史層の厚さが数字に表れる。",
        exceptionalHeritageCount=True,
        interestReason="世界でも突出した件数で、歴史層の厚さを一目で想像できるため。",
    )
    assert not quality.validate_data(data, "heritage-valid.json")


def test_exceptional_heritage_condition_below_30_passes() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="all-world-heritage-in-danger", label="危機遺産", value="2件 / 2件とも危機遺産",
        note="国内の世界遺産2件が、いずれも危機遺産リストに掲載されている。",
        exceptionalHeritageCondition=True,
        interestReason="単なる登録件数ではなく、文化遺産全体が危機下にある例外的状況を示すため。",
    )
    assert not quality.validate_data(data, "heritage-danger.json")


def test_moderate_forest_share_fails() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-forest-share", label="森林率", value="48%", note="国土の48%を森林が占める。", exceptionalShare=True,
    )
    errors = quality.validate_data(data, "forest-moderate.json")
    assert any("not extreme enough" in error for error in errors), errors


def test_extreme_forest_share_passes_with_exception() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][0] = signature_item(
        topicKey="country-forest-share", label="森林率", value="82%",
        note="国土の82%を森林が占め、地図上の国土像そのものを特徴づける。",
        exceptionalShare=True,
        interestReason="国土の大半が森林という極端な土地利用が旅の景観を決めるため。",
    )
    assert not quality.validate_data(data, "forest-extreme.json")


def test_interest_reason_required() -> None:
    data = base_data()
    data["capital"]["labelPosition"] = "left"
    data["signatureFacts"][1].pop("interestReason")
    errors = quality.validate_data(data, "interest.json")
    assert any("interestReason is required" in error for error in errors), errors


def test_v4_is_not_retroactively_invalidated() -> None:
    data = base_data(); data["contentQaVersion"] = 4
    assert not quality.validate_data(data, "legacy-v4.json")


def test_v5_is_not_retroactively_subjected_to_v6() -> None:
    data = base_data(); data["capital"]["labelPosition"] = "left"
    assert not quality.validate_data(data, "legacy-v5.json")


def test_v6_fixed_taste_heading() -> None:
    data = v6_data(); data["taste"]["title"] = "例国の食文化"
    errors = quality.validate_data(data, "taste-title.json")
    assert any("taste.title is fixed" in error for error in errors), errors


def test_v6_cross_section_subject_overlap() -> None:
    data = v6_data(); data["signatureFacts"][0]["topicKey"] = "silk-road-count"; data["atlasExtras"][0]["topicKey"] = "silk-road-history"
    errors = quality.validate_data(data, "subject-overlap.json")
    assert any("likely subject reuse" in error for error in errors), errors


def test_v6_temporarily_restricted_route_is_kept_with_note() -> None:
    data = v6_data()
    data["nextRoutes"] = [{"countryJa":"隣国","path":"A → Border → B","description":"旅行者が通常使う代表的な越境ルート。","travelerRoute":True,"status":"TEMPORARILY_RESTRICTED","statusNote":"2026年9月現在、旅行者の越境は一時的に制限されている。"}]
    assert not quality.validate_data(data, "restricted-route.json")


def test_v6_restricted_route_requires_status_note() -> None:
    data = v6_data(); data["nextRoutes"] = [{"travelerRoute": True, "status": "TEMPORARILY_RESTRICTED"}]
    errors = quality.validate_data(data, "route-note.json")
    assert any("statusNote is required" in error for error in errors), errors


def test_v6_air_next_route_is_rejected() -> None:
    data = v6_data(); data["nextRoutes"] = [{"countryJa":"隣国","path":"City → Neighbor (air)","description":"隣国への航空接続。","travelerRoute":True,"status":"OPEN"}]
    errors = quality.validate_data(data, "air-route.json")
    assert any("must not use air travel" in error for error in errors), errors


def test_v6_related_country_requires_affinity() -> None:
    data = v6_data(); data["relatedCountries"][0]["affinityType"] = ""
    errors = quality.validate_data(data, "affinity.json")
    assert any("affinityType" in error for error in errors), errors


def test_v6_encounters_require_breadth() -> None:
    data = v6_data()
    for item in data["encounters"]: item["category"] = "LANDSCAPE"
    errors = quality.validate_data(data, "encounters.json")
    assert any("at least 4 distinct categories" in error for error in errors), errors


def test_v6_generic_population_requires_exceptional_scale() -> None:
    data = v6_data()
    data["signatureFacts"][0] = signature_item(topicKey="population-total",label="人口",value="500万人",note="人口は約500万人で、国内の都市と地方に分布して暮らしている。",interestReason="単に取得できる人口統計ではなく国の規模を理解するために選んだ。")
    errors = quality.validate_data(data, "population.json")
    assert any("exceptionalScale:true" in error for error in errors), errors


def test_v6_generic_population_can_pass_when_truly_exceptional() -> None:
    data = v6_data()
    data["signatureFacts"][0] = signature_item(topicKey="population-extreme",label="人口",value="1,400,000,000人",note="人口規模そのものが都市、交通、市場の大きさを理解する入口になる。",interestReason="世界でも突出した人口規模で、旅先の都市と移動のスケール感が変わるため。",exceptionalScale=True)
    assert not quality.validate_data(data, "population-exception.json")


def test_v6_qualitative_zero_can_pass_when_explicit() -> None:
    data = v6_data()
    data["signatureFacts"][0] = signature_item(topicKey="formal-colonization-none",label="正式な植民地化",value="なし",note="欧州列強による正式な植民地化を受けなかったことが、周辺国との近代史の違いをつくる。",interestReason="近隣地域との歴史的な違いを一語で理解できる例外的条件のため。",qualitativeZero=True)
    assert not quality.validate_data(data, "qualitative-zero.json")


def test_v6_unfamiliar_unit_alone_fails() -> None:
    data = v6_data()
    data["signatureFacts"][0] = signature_item(value="1,200 ha",note="保護地域が1,200 haに及び、国土の自然景観を特徴づける。")
    errors = quality.validate_data(data, "hectare-only.json")
    assert any("unfamiliar unit" in error for error in errors), errors


def test_v6_unfamiliar_unit_with_metric_equivalent_passes() -> None:
    data = v6_data()
    data["signatureFacts"][0] = signature_item(value="12 km²",note="1,200 haに相当する12 km²の保護地域が、国土の自然景観を特徴づける。")
    assert not quality.validate_data(data, "hectare-converted.json")


if __name__ == "__main__":
    test_capital_label_scene_collision_fails()
    test_capital_label_side_change_resolves_collision()
    test_world_heritage_29_fails_even_with_count_exception()
    test_world_heritage_30_requires_explicit_exception()
    test_world_heritage_30_with_exception_passes()
    test_exceptional_heritage_condition_below_30_passes()
    test_moderate_forest_share_fails()
    test_extreme_forest_share_passes_with_exception()
    test_interest_reason_required()
    test_v4_is_not_retroactively_invalidated()
    test_v5_is_not_retroactively_subjected_to_v6()
    test_v6_fixed_taste_heading()
    test_v6_cross_section_subject_overlap()
    test_v6_temporarily_restricted_route_is_kept_with_note()
    test_v6_restricted_route_requires_status_note()
    test_v6_air_next_route_is_rejected()
    test_v6_related_country_requires_affinity()
    test_v6_encounters_require_breadth()
    test_v6_generic_population_requires_exceptional_scale()
    test_v6_generic_population_can_pass_when_truly_exceptional()
    test_v6_qualitative_zero_can_pass_when_explicit()
    test_v6_unfamiliar_unit_alone_fails()
    test_v6_unfamiliar_unit_with_metric_equivalent_passes()
    print("Content QA v5/v6 regression tests passed")
