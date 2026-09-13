#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("editorial", HERE / "validate_country_editorial_v2.py")
assert SPEC and SPEC.loader
editorial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(editorial)


def signature() -> list[dict]:
    return [
        {"topicKey":"island-archipelago-scale","label":"島","value":"1,000","note":"国土の広がりを数字で示す。"},
        {"topicKey":"volcanic-peaks","label":"活火山","value":"100","note":"火山地形の規模を示す。"},
        {"topicKey":"rail-network-length","label":"鉄道網","value":"9,000km","note":"移動網の規模を示す。"},
    ]


def contextual() -> tuple[list[dict], list[dict]]:
    extras = [
        {"topicKey":"water-temple-ritual","title":"水辺の祈り","text":"水と信仰が暮らしの中で結びついている。","points":["共同体の儀礼","水辺の空間"]},
        {"topicKey":"market-daily-life","title":"市場が暮らしを映す","text":"朝の市場では地域ごとの食材と商いが見える。","points":["朝の時間帯","地域差"]},
        {"topicKey":"textile-village-craft","title":"織物の村","text":"手仕事が家族と地域の生業として続く。","points":["手織り","村の仕事"]},
    ]
    trivia = [
        {"topicKey":"street-address-colors","categoryJa":"街角","title":"住所表示の色に注目","text":"地区ごとに表示の見え方が少し違う。"},
        {"topicKey":"coffee-order-words","categoryJa":"言葉","title":"コーヒーの頼み方","text":"注文語を知ると朝の店が少し楽しくなる。"},
        {"topicKey":"bus-stop-hand-signals","categoryJa":"移動","title":"バス停の合図","text":"地域によって乗車時の合図に癖がある。"},
    ]
    return extras, trivia


def travel(version: int, durations: tuple[str,str,str]) -> dict:
    return {
        "contentQaVersion": version,
        "travelScale": {
            "kicker":"DURATION","title":"旅の目安日程","intro":"",
            "items":[
                {"duration":durations[0],"title":"街を深く見る","text":"拠点を絞る。例：A → B。","icon":"city"},
                {"duration":durations[1],"title":"主要地域を巡る","text":"地域を結ぶ。例：A → B → C。","icon":"map"},
                {"duration":durations[2],"title":"国の幅を見る","text":"広域を巡る。例：A → B → C → D。","icon":"compass"},
            ],
        },
        "signatureFacts": signature(),
    }


def v3() -> dict:
    data = travel(3, ("一都市中心","地域をつなぐ","広域周遊"))
    data["atlasExtras"], data["travelTrivia"] = contextual()
    return data


def v4() -> dict:
    data = travel(4, ("3日","5〜7日","10日以上"))
    data["atlasExtras"], data["travelTrivia"] = contextual()
    return data


def test_v2_day_notation() -> None:
    data = travel(2, ("3〜4日","7〜10日","14日以上"))
    assert not editorial.validate_data(data, "v2.json")


def test_v3_legacy_qualitative_still_valid() -> None:
    assert not editorial.validate_data(v3(), "v3.json")


def test_v3_day_count_still_fails() -> None:
    data = v3(); data["travelScale"]["items"][0]["duration"] = "3日"
    errors = editorial.validate_data(data, "v3-day.json")
    assert any("forbids numeric stay/day/week counts" in e for e in errors), errors


def test_v4_day_notation_valid() -> None:
    assert not editorial.validate_data(v4(), "v4.json")


def test_v4_qualitative_fails() -> None:
    data = v4(); data["travelScale"]["items"][0]["duration"] = "一都市中心"
    errors = editorial.validate_data(data, "v4-qualitative.json")
    assert any("must use day notation only" in e for e in errors), errors


def test_v4_bad_units_fail() -> None:
    for value in ("1週間", "2泊3日"):
        data = v4(); data["travelScale"]["items"][1]["duration"] = value
        errors = editorial.validate_data(data, "v4-unit.json")
        assert any("must use day notation only" in e for e in errors), errors


def test_v4_final_open_ended() -> None:
    data = v4(); data["travelScale"]["items"][2]["duration"] = "8〜10日"
    errors = editorial.validate_data(data, "v4-final.json")
    assert any("final travelScale duration" in e for e in errors), errors


def test_forest_rule() -> None:
    data = travel(2, ("3日","5日","8日以上"))
    data["signatureFacts"][0] = {"topicKey":"forest-share-52","label":"森林","value":"52%","note":"国土の約半分。","exceptionalShare":True}
    errors = editorial.validate_data(data, "forest.json")
    assert any("not distinctive enough" in e for e in errors), errors


def test_cross_section_duplication() -> None:
    data = v4(); data["travelTrivia"][0]["topicKey"] = "island-archipelago-scale"
    errors = editorial.validate_data(data, "dup.json")
    assert any("duplicate topicKey" in e for e in errors), errors


if __name__ == "__main__":
    test_v2_day_notation()
    test_v3_legacy_qualitative_still_valid()
    test_v3_day_count_still_fails()
    test_v4_day_notation_valid()
    test_v4_qualitative_fails()
    test_v4_bad_units_fail()
    test_v4_final_open_ended()
    test_forest_rule()
    test_cross_section_duplication()
    print("Editorial Content QA regression tests passed for v2/v3/v4 routing")
