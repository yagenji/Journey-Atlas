# JOURNEY ATLAS — CONTENT QUALITY

This document defines editorial quality for a finished Country JSON. Content QA is a finish-line check, not a step-by-step production controller.

## Editorial principles

A Country page should make a first-time visitor understand what is distinctive about the place and want to know it more deeply.

Required:
- factual claims verified from reliable sources;
- current numerical claims carry an appropriate source date;
- real locations and real coordinates;
- clear Japanese without tourism-advertising exaggeration;
- different sections provide different information value;
- Signature Facts are genuinely distinctive, not generic profile numbers;
- Encounters describe observable travel experiences;
- Beyond the Scenery adds deeper context;
- Travel Trivia stays light and non-duplicative;
- Taste items are authentic recognizable dishes;
- Travel Scale provides a concrete, internally consistent journey shape;
- next routes and related destinations are editorially meaningful, not filler.

Unknown facts remain unfilled until verified. Do not guess.

## Country Profile area comparison

For the `面積` fact, include a Japan comparison when a reliable area basis is available.
- If the country is smaller than Japan, express the comparison as a percentage: `日本の約○○%`.
- If the country is larger than Japan, express the comparison as a multiple: `日本の約○○倍`.
- Keep the same area basis for the country and Japan where practical, record the source/date, and avoid unnecessary decimal precision.
- Do not switch a value above 100% into percentage form or a value below 1.0 into multiplier form merely because the arithmetic is equivalent.

## Source discipline

Use reliable primary or authoritative secondary sources for:
- population and area;
- currency/language/religion where relevant;
- geography;
- history;
- transport;
- seasonal operation;
- protected/heritage status;
- other changing factual claims.

Use:
- `sourcesVerifiedAt` for when sources were checked;
- `sourceDates` for the date/period represented by changing values.

## Finish-line validators

For a new Country run:

```bash
python3 scripts/validate_country_editorial_v2.py --force data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
python3 scripts/validate_country.py --strict data/countries/{slug}.json
```

Validator failures identify defects in the finished content. They do not create production State transitions.
