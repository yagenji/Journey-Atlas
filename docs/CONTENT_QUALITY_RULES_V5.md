# JOURNEY ATLAS — Content Quality Rules v5

Updated: 2026-09-14

Content QA v5 applies to new Country production with `contentQaVersion: 5`.
It inherits all v4 rules and adds two production gates:

1. **Signature Facts must be selected for reader interest, not because a statistic is easy to obtain.**
2. **The capital-name label must not cover any numbered Scene marker on the Country map.**

Existing v2–v4 Countries remain valid unless intentionally migrated.

## 1. Signature Facts — reader interest first

`signatureFacts` still contains exactly three numerical facts, but the selection question changes from “is this measurable?” to:

> **Does knowing this number materially change how the reader imagines the Country?**

Good candidates usually reveal one of the following:

- an extreme physical scale or proportion;
- a world-leading or unusually concentrated activity;
- a surprising relationship between geography and everyday life;
- a numerical fact that explains why travel in the Country feels different;
- a measurable characteristic that is genuinely difficult to guess without seeing the number.

Weak candidates are generic profile statistics or counts that could be substituted into many Countries without changing the reader’s mental picture.

Every v5 Signature Fact must include an internal `interestReason` explaining why the number deserves one of only three positions. `interestReason` is editorial metadata and is not rendered on the page.

Example:

```json
{
  "topicKey": "country-extreme-example",
  "label": "...",
  "value": "...",
  "note": "...",
  "icon": "...",
  "interestReason": "この数字を知ることで、国土や旅の感覚がどう変わって見えるか。"
}
```

## 2. World Heritage counts are exception-only

The number of UNESCO World Heritage properties is **not a default Signature Fact**.

Do not use a count merely because the Country has several properties. Counts such as 3, 7, 10, or 15 are usually not strong enough to occupy one of the three numerical slots.

A World Heritage count may be used only when both conditions are met:

1. the count is exceptionally high: **25 or more**; and
2. `exceptionalHeritageCount: true` is explicit.

Even above 25, it should still be replaced when another number explains the Country more vividly.

The machine threshold is an exception gate, not an automatic recommendation.

Correct exceptional form:

```json
{
  "topicKey": "country-world-heritage-count",
  "label": "世界遺産",
  "value": "30件",
  "exceptionalHeritageCount": true,
  "interestReason": "世界でも突出した件数で、歴史層の厚さを一目で想像できるため。"
}
```

A smaller World Heritage count can still appear in Travel Trivia or Beyond the Scenery when the heritage itself is editorially interesting. It simply does not qualify as one of the three Signature Facts.

## 3. Forest share is also exception-only

Forest / woodland percentage is not a routine Signature Fact.

It may be used only when:

1. `exceptionalShare: true` is explicit; and
2. the percentage is operationally extreme: **10% or less, or 70% or more**; and
3. the number genuinely explains the Country’s landscape or travel experience.

A forest share of 35%, 48%, 55%, or 63% is not distinctive enough merely because the data exists.

As with World Heritage counts, passing the machine threshold does not mean the number should automatically be selected. It must still beat alternative numbers on reader interest.

## 4. Capital-name / Scene-number map collision gate

The capital marker and capital name remain part of the map, but the capital **name label may never cover a numbered Scene marker**.

The validator projects the capital and Scenes onto the same 1200×760 map canvas used by the page and evaluates the capital label box against every numbered Scene marker.

If a collision occurs, resolve it in this order:

1. switch `capital.labelPosition` between `left` and `right`;
2. use a small `capital.labelOffset: {x, y}` adjustment;
3. only if still necessary, use the smallest practical `mapOffset` adjustment.

Never change the real latitude / longitude to make the map look cleaner.

`capital.labelOffset` is limited to ±80px per axis. The label must also remain inside the map canvas.

## 5. Required validation

Before Hero generation, run both validators:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
```

The second validator enforces:

- `interestReason` on all three Signature Facts;
- World Heritage count exception rules;
- forest-share exception rules;
- capital-name / Scene-number collision prevention.

Regression tests:

```bash
python3 scripts/test_country_editorial_v2.py
python3 scripts/test_country_quality_v5.py
```
