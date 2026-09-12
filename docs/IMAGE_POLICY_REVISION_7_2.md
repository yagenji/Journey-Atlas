# JOURNEY ATLAS — Image Policy Revision 7.2

Updated: 2026-09-12
Policy: Revision 7 / Patch 2 (`policyId: 7.2`)

Revision 7.2 is a corrective patch based on production regressions observed in the Philippines, Singapore, Thailand, Vietnam and Brunei rounds.

It keeps the Revision 7 reservation, contamination, batch-ledger and same-turn continuation model. It changes four things that are now machine-enforced.

## 1. Taste composition: integral vs decorative

Taste imagery is still a clean atlas cut, not a restaurant or lifestyle scene.

The rule is **not** “one vessel only” and it is **not** “all sauces or side components are forbidden.”

A component may appear when it is required to constitute, serve or recognize the dish itself. Examples include an integral dipping sauce, broth, wrapper or serving element that is genuinely part of the traditional dish presentation.

Such components must be named in the exact FOOD Render Packet before generation.

Elements added only for styling, atmosphere or visual richness are forbidden. This includes decorative herbs outside the dish, loose raw ingredients, cutlery, napkins, flowers, drinks, unrelated bowls, kitchen or restaurant backgrounds, scenery and other contextual props.

Every active Taste Render Packet must therefore declare:

```json
{
  "integralAccompanimentsOnly": true,
  "integralAccompaniments": [],
  "integralServingElements": [],
  "decorativePropsForbidden": true,
  "decorativeProps": [],
  "plainBackgroundRequired": true,
  "backgroundStyle": "PLAIN_PALE_BEIGE_OR_WARM_IVORY"
}
```

`integralAccompaniments` and `integralServingElements` may be non-empty when the dish genuinely requires them. `decorativeProps` must always be empty.

Example: Brunei ambuyat may include its integral cacah dipping sauce and the small vessel needed to hold that sauce. A decorative feast spread, unrelated fish or vegetables, table styling or tropical scenery may not be added.

## 2. Taste candidate QA is explicit

A Taste image may become `REVIEW_CANDIDATE` only when all of these checks are `PASS`:

- `targetIdentity`
- `dishIdentity`
- `singleDish`
- `integralComponentsOnly`
- `plainBackground`
- `decorativePropsAbsent`
- `previousAssetRepeat`
- `collageTypography`

The previous three-field QA was insufficient because it could mark a dish candidate valid even when background props were present.

## 3. Initial Taste round finishes its first pass before retry

During `TASTE_INITIAL`, each FOOD target is attempted once before a failed target is regenerated.

If FOOD02 fails while FOOD03 or FOOD04 remains unattempted:

1. FOOD02 is parked as `REGENERATE`;
2. the round continues to the next `NOT_STARTED` FOOD target;
3. after every target has been attempted, NEXT becomes the Taste batch-review boundary;
4. the batch review approves valid candidates and records the failed target(s) in `regenerate`;
5. only then may phase become `TASTE_REGEN`.

Entering `TASTE_REGEN` before an initial Taste batch-review ledger round is invalid.

This prevents the one-image-at-a-time review/regeneration loop observed in current production.

## 4. Repeat / wrong-target failures refresh immediately

`PREVIOUS_ASSET_REPEAT` and `WRONG_TARGET_CARRYOVER` are different from an ordinary composition miss.

After either failure:

1. reject the candidate;
2. contaminate/reset according to Revision 7;
3. do not retry from the same prompt series;
4. refresh the Render Packet / prompt family;
5. increment `promptSeries`;
6. only then regenerate.

The old two-failures-before-refresh threshold remains available for ordinary hard failures, but it no longer applies to repeats or wrong-target carryover.

## Interaction rule

Scene and Taste rounds still run to their batch boundary without voluntary user stops.

A runtime-imposed assistant turn boundary is not an approval gate. On resumption, the assistant reconciles State and continues from Protocol 2 NEXT without asking the user to type `approve`, `進めて`, `next`, `生成` or an equivalent continuation nudge.

Protocol 2 Patch 3 records:

- `productionMetrics.perImageApprovalPrompts` — target `0`;
- `productionMetrics.userContinuationNudges` — target `0`;
- `productionMetrics.runtimeForcedImageTurnBoundaries` — measured separately and allowed.

This distinction prevents platform turn boundaries from being confused with user approval gates.

## Validation

Revision 7.2 adds `scripts/image_policy_v72.py`.

Current-state validation:

```bash
python3 scripts/image_policy_v72.py validate
```

Transition validation:

```bash
python3 scripts/image_policy_v72.py validate-range <base> <head>
```

Regression tests remain in:

```bash
python3 scripts/test_image_policy_v7.py
```

Country-branch pushes must run both Revision 7 transition validation and Revision 7.2 transition validation.
