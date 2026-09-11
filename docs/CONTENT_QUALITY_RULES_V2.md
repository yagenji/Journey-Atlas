# JOURNEY ATLAS — Content Quality Rules v2

Updated: 2026-09-11

This specification applies to new Country JSON files with `contentQaVersion: 2`.
It strengthens editorial quality without retroactively invalidating older published v1 pages.

## 1. Travel Scale examples are mandatory

`travelScale` must contain exactly three items.

Every item must contain:

- `duration`
- `title`
- `text`
- the fixed icon sequence `city` / `map` / `compass`
- a concrete itinerary/example introduced by `例：`

A conceptual explanation without an example is incomplete.

Valid:

`例：東京 → 京都 → 広島・宮島 → 東京。`

Also valid when route arrows are inappropriate:

`例：平壌＋開城。`

The example must be concrete enough that a reader can picture how that duration would actually be used.

Duration notation remains days-based, and the third item must be open-ended: `○日以上`.

## 2. Signature Facts must be genuinely distinctive

`signatureFacts` contains exactly three numbers/facts that help a reader understand what is unusual about the Country.

Do not fill the three slots with generic statistical availability.
A number is not useful merely because it is easy to source.

Prefer:

- unusual physical scale;
- unusual concentration or distribution;
- strong geographic extremes;
- a distinctive transport/cultural system;
- a clearly meaningful heritage or settlement fact;
- a number that changes how the reader imagines the Country.

Avoid routine percentages whose only virtue is that they are measurable.

## 3. Forest / woodland percentage rule

Forest or woodland coverage is **not a default Signature Fact**.

A moderate share such as roughly half the Country being forested is normally too generic to occupy one of the three Signature Fact slots.

For Content QA v2, a forest/woodland percentage may be used only when both conditions are true:

1. the item explicitly declares `exceptionalShare: true`;
2. the percentage is operationally extreme: **10% or less, or 70% or more**.

The threshold is an editorial QA threshold, not a scientific definition of forest scarcity/abundance.
It exists to prevent routine 30–60% forest statistics from repeatedly displacing more distinctive Country facts.

Even when the threshold is met, use the forest fact only if it is one of the strongest three ways to explain the Country.

## 4. Validation

Run before Hero generation:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
```

New Country production must not leave the CONTENT / pre-visual stage until this validator passes.

Regression tests:

```bash
python3 scripts/test_country_editorial_v2.py
```
