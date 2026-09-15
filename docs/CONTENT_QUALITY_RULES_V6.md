# JOURNEY ATLAS — Content Quality Rules v6

Updated: 2026-09-15

Content QA v6 applies to new Country production with `contentQaVersion: 6`.
It inherits v4 Travel Scale rules and v5 Signature Facts / map-label rules.
The purpose of v6 is not to add repeated QA. It is to settle editorial selection **once before Hero production**, reduce later rewrites, and let production continue automatically until a real user gate.

## 1. One-pass editorial gate

Before Hero generation, the Country JSON must settle all of the following together:

- Signature Facts
- Beyond the Scenery
- Travel Trivia
- ENCOUNTERS
- Taste heading + four dishes
- NEXT ROUTES
- NEXT DESTINATIONS
- Travel Scale
- Map coordinates / capital label placement

After this gate passes, editorial rewriting is not repeated after image approval unless there is a blocking defect or the user explicitly requests a revision.

## 2. Signature Facts / Beyond / Trivia must use different subjects

The three sections have different jobs and must not reuse one subject from different angles.

- `signatureFacts`: a number whose numeric form materially changes how the reader imagines the Country.
- `atlasExtras`: deeper historical, social, cultural, geographic or everyday-life context.
- `travelTrivia`: a short separate discovery that makes travel more interesting.

Changing `count` to `history`, or rewriting a fact as a trivia sentence, does not create a new subject. `topicKey` must represent the actual canonical subject. v6 adds token-overlap checks on top of the existing exact/canonical key and copy-similarity checks.

## 3. Signature Facts must be distinctive and immediately understandable

There are only three slots.

A fact must pass both questions:

1. **Is the number genuinely distinctive for this Country?**
2. **Can a reader understand what the number means without specialist knowledge?**

The visible `label`, `value`, and `note` must explain the metric plainly. Internal `interestReason` must explain why it deserves one of three slots.

### Usually rejected

- ordinary population counts;
- ordinary area figures;
- ordinary population density;
- ordinary World Heritage counts;
- ordinary forest shares;
- technical indices whose meaning needs a separate explanation.

Population / area / density may be used only when the scale itself is genuinely exceptional and `exceptionalScale: true` is explicit.

World Heritage remains exception-only at 25 or more with `exceptionalHeritageCount: true`.
Forest / woodland share remains exception-only at 10% or less or 70% or more with `exceptionalShare: true`.

Passing an exception threshold does not automatically make a number a good choice; a more revealing number still takes priority.

## 4. Map capital label / Scene number

The capital name may not overlap or sit uncomfortably close to an S01–S08 numbered marker.

Resolve in this order:

1. `capital.labelPosition` left / right;
2. small `capital.labelOffset`;
3. minimal Scene `mapOffset` if necessary.

Never change true latitude / longitude to improve layout.

v6 adds an additional safety margin beyond the v5 geometric collision test so borderline placements are rejected before visual production.

## 5. NEXT ROUTES: route existence and current border status are separate

NEXT ROUTES answers: **Is this an established representative traveler continuation?**

Do not delete a route merely because the border is temporarily closed or restricted at the moment of production.

Each route uses:

- `travelerRoute: true` — confirms this is a genuine traveler route, not merely a shared border;
- `status`: `OPEN`, `TEMPORARILY_RESTRICTED`, `SEASONAL`, or `CHECK_CURRENT_CONDITIONS`;
- `statusNote` when status is not `OPEN`.

The visible text must clearly state temporary restrictions when relevant. Avoid unstable fares, timetables and service numbers.

## 6. Taste heading is fixed

Country-by-Country creative headings are forbidden.

- Kicker: `TASTE OF {COUNTRY ENGLISH NAME}`
- Title: `{日本語国名}で食べたいもの`

Country individuality belongs in the intro and the four selected dishes, not in the section heading.

## 7. NEXT DESTINATIONS means affinity, not proximity

The three recommendations answer:

> If someone likes this Country, which other Countries are they likely to enjoy?

Geographic closeness, a shared border, or being in the same region is not itself a recommendation reason.

Each item must carry an internal `affinityType` such as `LANDSCAPE`, `CULTURE`, `HISTORY`, `FOOD`, `TRAVEL_STYLE`, `MOUNTAIN`, `DESERT`, or `ISLAND`, and the visible `reason` must explain that affinity.

NEXT ROUTES and NEXT DESTINATIONS remain separate concepts even when the same Country appears in both.

## 8. ENCOUNTERS must stay broad and observable

ENCOUNTERS is not a glossary of local terms and not Scene 8 rewritten as nouns.

Each of the eight items must be something a traveler can directly see or experience and understand without prior specialist knowledge. Use broad, repeatable Country-level experiences rather than a single local object or explanation-heavy proper noun.

Each item carries an internal category. Eight items must span at least four categories among landscape, nature, city, architecture, daily life, movement, food, wildlife, season, faith, culture, language and work.

If a local term needs parentheses or a long explanation, it belongs in Beyond the Scenery or Travel Trivia instead.

## 9. Run-to-gate execution — do not make the user supervise production

A deterministic `NEXT ACTION` with `userGate:false` must execute without asking the user to reply `進めて`, `次へ`, or similar.

Production may stop only for:

- Hero approval;
- Scene batch approval;
- Taste batch approval;
- canonical page approval;
- a genuinely user-required asset handoff;
- a hard technical / authorization blocker that cannot be resolved automatically.

A runtime/tool/turn boundary is not an approval boundary. After a successful tool action, continue through the next deterministic actions until the next explicit gate.

Do not end a turn with a status-only message when an executable non-gate NEXT ACTION remains.

## 10. Required validation

New Countries remain on the existing commands; no extra CI cycle is added:

```bash
python3 scripts/validate_country_editorial_v2.py data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
```

The retained `validate_country_quality_v5.py` filename is intentional for workflow compatibility. It routes v5/v6 behavior using `contentQaVersion`.

The one-pass gate is run before Hero production. After that, targeted Preview Browser QA remains the single normal browser-validation cycle for Country-only changes.
