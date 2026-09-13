# JOURNEY ATLAS — Content Quality Rules v3

Updated: 2026-09-13

This specification applies to new Country JSON files with `contentQaVersion: 3`.
Existing v2 Countries remain valid under the v2 rules unless intentionally migrated.

## 1. Travel Scale keeps day ranges; only the route example excludes day counts

`travelScale` remains a three-step UI for **旅の目安日程**. The duration/day guidance is part of the section and must remain visible.

Each item contains:

- `duration`
- `title`
- `text`
- fixed icon sequence `city` / `map` / `compass`
- a concrete itinerary/example introduced by `例：`

For v3:

- `duration` uses Country-specific day notation such as `3〜4日` or `7〜10日`;
- the third item remains open-ended and must use `○日以上`;
- the actual ranges are editorially flexible by Country size, dispersal, transport burden and realistic trip composition;
- **only the content after `例：` is forbidden from containing day/stay/week counts.**

Correct:

- `duration: 3〜4日`
- `text: 首都と近郊に絞る。例：A → B → A。`

Incorrect:

- `text: 首都と近郊に絞る。例：Aを2日 → Bを1日 → A。`
- `text: 広域を巡る。例：A → B → Cを1週間。`

The `例：` portion exists to show a representative **route**, not to repeat or prescribe the number of days at each stop.
Do not remove the duration/day guidance from the Travel Scale itself.

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
Forest/woodland coverage remains non-default and may be used only when:

1. `exceptionalShare: true` is explicit; and
2. the share is operationally extreme: 10% or less, or 70% or more.

Even then, use it only if it is one of the strongest three numerical ways to explain the Country.

## 5. Validation

Run before Hero generation:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
```

The filename is retained for workflow compatibility, but the script routes rules by `contentQaVersion`:

- v2 Country → v2 rules
- v3 Country → v3 rules, including the example-only day-count ban

New Country scaffolds created by `scripts/new_country.py` use `contentQaVersion: 3`.

Regression tests:

```bash
python3 scripts/test_country_editorial_v2.py
```

A new Country must not leave the CONTENT / pre-visual stage until the current editorial validator passes.
