# JOURNEY ATLAS — Content Quality Rules v4

Updated: 2026-09-13

This specification applies to new Country JSON files with `contentQaVersion: 4`.
Existing v3 Countries remain valid under the v3 route-scope/no-day-count rules unless intentionally migrated.

## 1. Travel Scale keeps day notation; `例：` shows route only

`travelScale` remains a three-step UI and the visible `duration` must use days.
The purpose is to give the reader a practical stay-length reference while showing how the geographic scope changes.

Each item contains:

- `duration`
- `title`
- `text`
- fixed icon sequence `city` / `map` / `compass`
- a concrete itinerary/example introduced by `例：`

Day notation rules:

- use `日` for the visible duration rather than weeks or nights;
- the first two levels may be a single day count or a day range such as `2日` / `3〜4日`;
- the third level is open-ended and must use `○日以上`;
- do not mix `泊`, `週`, or `週間` into the duration labels;
- the route text should explain geography, sequence, regional contrast, transport burden, and thematic breadth rather than merely repeating the day count.

The `例：` portion has a separate rule: **it is a route example, so it must not contain a number of days, nights, or weeks.**

Correct:

- `duration: 5〜7日`
- `text: 主要地域をつなぐ。例：A → B → C。`

Incorrect:

- `text: 主要地域をつなぐ。例：Aを2日 → Bを3日 → C。`
- `text: 広域を巡る。例：A → B → Cを1週間。`

The prohibition applies only to the content after `例：`. It does **not** remove day guidance from `duration`, and it does not prohibit explanatory text before `例：` from referring to the tier's duration when editorially useful.

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

For `signatureFacts`, `atlasExtras`, and `travelTrivia`:

- every item must have a non-empty `topicKey`;
- the same `topicKey` may not appear across different sections;
- adding generic suffixes such as `-count`, `-history`, `-trivia`, `-share`, or `-fact` does not make the topic different;
- if two items are about the same underlying subject, move one of them to a genuinely different subject rather than renaming the key.

The validator also performs a conservative near-duplicate copy check across the three sections.

## 4. Signature Facts quality and icons

`signatureFacts` contains exactly three distinctive numbers/facts.

Avoid generic statistics selected only because data is available. A number should materially change how the Country is imagined.

Use an explicit `icon` when the label does not map cleanly to a suitable common icon. The three Signature Facts should not accidentally collapse to the same fallback icon when distinct icons are available.

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

- v2 Country → v2 day-notation rules
- v3 Country → legacy v3 route-scope/no-day-count rules
- v4 Country → day-notation rules + route-only `例：` + cross-section duplication controls

New Country scaffolds created by `scripts/new_country.py` use `contentQaVersion: 4`.

Regression tests:

```bash
python3 scripts/test_country_editorial_v2.py
```
