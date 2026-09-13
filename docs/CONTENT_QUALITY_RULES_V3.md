# JOURNEY ATLAS — Content Quality Rules v3

Updated: 2026-09-13

This specification applies to new Country JSON files with `contentQaVersion: 3`.
Existing v2 Countries remain valid under the v2 rules unless intentionally migrated.

## 1. Travel Scale uses day notation and route scope together

`travelScale` remains a three-step UI and the visible `duration` must use days.
The purpose is not to prescribe an exact trip, but to give the reader a practical stay-length reference while showing how the geographic scope changes.

Each item contains:

- `duration`
- `title`
- `text`
- fixed icon sequence `city` / `map` / `compass`
- a concrete itinerary/example introduced by `例：`

Day notation rules:

- use `日` rather than weeks or nights;
- the first two levels may be a single day count or a day range such as `2日` / `3〜4日`;
- the third level is open-ended and must use `○日以上`;
- do not mix `泊`, `週`, or `週間` into the duration labels;
- the route text should explain geography, sequence, regional contrast, transport burden, and thematic breadth rather than merely repeating the day count.

The example remains required because the reader should be able to picture a representative route.

## 2. Signature Facts / Beyond the Scenery / Travel Trivia must not repeat topics

These three sections have different editorial jobs:

- `signatureFacts` = 数値。A number/fact whose numeric form changes how the Country is imagined.
- `atlasExtras` = 景色の向こうへ。Deep context behind landscape, society, history, culture, daily life, food, cities, or movement.
- `travelTrivia` = トリビア。A short, light discovery that is useful or fun to notice while travelling.

The same subject must not be reused across these sections by changing wording or angle.

Examples of forbidden duplication:

- Signature Fact: number of UNESCO sites; Beyond the Scenery: history of the same UNESCO-site group.
- Signature Fact: number of islands; Trivia: "this Country has many islands".
- Beyond the Scenery: explanation of a festival; Trivia: a shortened version of the same festival fact.
- Signature Fact: rail-network length; Beyond the Scenery: the same rail system explained as a social fact, when no distinct information value is added.

## 3. `topicKey` is the canonical subject key

Under Content QA v3, `topicKey` is not just an internal ID. It is the canonical subject identifier used for duplication control.

For `signatureFacts`, `atlasExtras`, and `travelTrivia`:

- every item must have a non-empty `topicKey`;
- the same `topicKey` may not appear across different sections;
- adding generic suffixes such as `-count`, `-history`, `-trivia`, `-share`, or `-fact` does not make the topic different;
- if two items are about the same underlying subject, use the same canonical root and move one of them to a different subject rather than renaming the key.

The validator also performs a conservative near-duplicate copy check across the three sections.
This is a backstop, not permission to bypass the editorial rule with rewritten wording.

## 4. Signature Facts quality remains strict

`signatureFacts` contains exactly three distinctive numbers/facts.

Avoid generic statistics selected only because data is available.
Every Signature Fact should also carry an explicit icon when the default label mapping would not provide a distinctive icon.

Forest/woodland coverage remains non-default and may be used only when:

1. `exceptionalShare: true` is explicit; and
2. the share is operationally extreme: 10% or less, or 70% or more.

Even then, use it only if it is one of the strongest three numerical ways to explain the Country.

## 5. Validation

Run before Hero generation and again after any explicit editorial revision during final review:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
```

The filename is retained for workflow compatibility, but the script routes rules by `contentQaVersion`:

- v2 Country → v2 rules
- v3 Country → v3 rules with day-notation Travel Scale plus cross-section duplication controls

New Country scaffolds created by `scripts/new_country.py` use `contentQaVersion: 3`.

Regression tests:

```bash
python3 scripts/test_country_editorial_v2.py
```
