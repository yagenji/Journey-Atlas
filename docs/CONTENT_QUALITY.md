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
- Travel Trivia gives the reader a small, genuinely surprising discovery rather than repeating profile or guidebook information;
- Taste items are authentic recognizable dishes;
- Travel Scale provides a concrete, internally consistent journey shape;
- next routes and related destinations are editorially meaningful, not filler.

Unknown facts remain unfilled until verified. Do not guess.

## Signature Facts

Signature Facts should change how a first-time reader imagines the Country. The three slots are scarce editorial space, so prefer numbers that reveal distinctive geography, history, culture, daily life, wildlife, movement, or scale over numbers that are merely easy to obtain.

Required:
- explain what the number means in enough Japanese context that a reader can understand it without already knowing the subject;
- avoid repeating generic Country Profile statistics unless the scale itself is genuinely exceptional;
- avoid using a World Heritage property merely as a convenient source of an area, component count, registration year, or other number when the number only explains that property;
- World Heritage site counts are exception-only. A current count of **30 or more** is rare enough to be a Signature Fact candidate, but it is not automatic: use it only when it is stronger than the available Country-specific alternatives;
- exceptional states can qualify even below 30 when the relationship itself is distinctive, such as all registered World Heritage properties being on the List of World Heritage in Danger;
- non-numeric values can qualify when the absence itself is a distinctive Country fact, such as no formal colonization by a European colonial power;
- prefer units familiar to Japanese readers. Convert or supplement hectares, acres, miles, feet, yards, gallons, Fahrenheit, knots, and similar units with `km²`, `km`, `m`, `L`, `℃`, or another immediately understandable metric form;
- do not repeat the same subject across Signature Facts, Beyond the Scenery, and Travel Trivia unless each section clearly adds a different information value.

Passing an exception threshold does not automatically make a fact a good choice. A more revealing Country-specific fact still takes priority.

## Travel Trivia

Travel Trivia is not a miniature guidebook or a second Country Profile. Each item should leave a first-time reader with a small **「へぇー」**: an unexpected fact, custom, historical detail, cultural quirk, geographic peculiarity, local invention, unusual practice, or other concise discovery that adds character to the Country.

Required:
- choose a fact that is interesting even if the reader is not currently planning logistics;
- prefer Country-specific or locally distinctive material over generic travel advice;
- keep it light enough to read quickly, while still being factually meaningful;
- avoid repeating the subject or information value of Country Profile, Signature Facts, Beyond the Scenery, Travel Notes, Transport, or another Trivia item;
- if an item mainly answers "what do I need to know to travel there?" rather than "what is interesting about this place?", it belongs in another section.

Do **not** use Travel Trivia for:
- Country Profile-style basics such as official or commonly used languages, currency or money, capital, population, area, religion, or equivalent profile facts;
- road-side rules or driving guidance such as left-hand / right-hand traffic, road-side conventions, licence requirements, fuel or rental-car advice;
- operational travel guidance such as tipping, payment methods, SIM/eSIM, plug types, opening hours, border procedures, transport tickets, or similar guidebook information;
- a Scene, Signature Fact, Beyond item, or Travel Note merely rewritten as a shorter sentence.

A historical or cultural fact that happens to involve language, money, transport, or another practical subject is still unsuitable when its main information value is the practical/basic fact itself. Choose a different topic whose value is discovery, not utility.

## Country Profile area comparison

For the `面積` fact, include a Japan comparison when a reliable area basis is available.
- If the country is smaller than Japan, express the comparison as a percentage: `日本の約○○%`.
- If the country is larger than Japan, express the comparison as a multiple: `日本の約○○倍`.
- Keep the same area basis for the country and Japan where practical, record the source/date, and avoid unnecessary decimal precision.
- Do not switch a value above 100% into percentage form or a value below 1.0 into multiplier form merely because the arithmetic is equivalent.

## Travel Scale route examples

`travelScale` の `例：` ルートは、**片道の地点列挙ではなく、旅として完結する周遊ルート**にする。

- 原則として、現実的な主要拠点から出発し、その拠点へ戻る形で組む。
- 地理・交通上、同じ拠点へ戻ることが不自然な場合だけ、別の現実的な出国・帰路拠点で完結させる。
- 観光地や地方都市で行きっぱなしにせず、帰路まで含めて一つの旅として読めること。

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
