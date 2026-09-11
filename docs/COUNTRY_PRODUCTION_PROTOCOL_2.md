# JOURNEY ATLAS — Country Production Protocol 2.0

Updated: 2026-09-11

Machine-readable authority: `ops/country-production-policy.json`.
Image-generation authority remains `ops/image-generation-policy.json`.

Protocol 2.0 is the default for **new Country production**. It is based on the Japan / Indonesia / Cambodia / North Korea production review and addresses three separate bottlenecks:

1. Scene/Taste generation could still be interpreted as one-image-one-user-approval despite Revision 7/7.1.
2. Generated-image repository materialization followed two different paths.
3. Most Country implementation work still happened after image approval, leaving a long post-image critical path.

## Production shape

The critical path becomes:

```text
CONTENT + PRE-VISUAL BUILD
→ Hero generation/review
→ Scene round to batch boundary
→ Scene batch review
→ Taste round to batch boundary
→ Taste batch review
→ one 13-image user handoff
→ one batch asset verification
→ one review-package integration
→ one targeted Browser QA cycle
→ canonical review
→ publication
```

## 1. Pre-visual build is mandatory

Before Hero generation, finish everything that does not require the final raster bytes.

Required before leaving CONTENT:

- Country JSON editorial content complete;
- final expected Hero / S01–S08 / FOOD01–04 paths declared;
- Scene coordinates final;
- Map built and QA passed;
- theme taxonomy complete;
- Related Countries complete;
- Next Routes resolved or intentionally empty;
- Travel Scale complete;
- Signature Facts complete;
- sources / source dates complete;
- Content QA v2 passed.

The Map therefore must be `APPROVED` before Hero production starts under Protocol 2.

This front-loads work that previously remained after Taste approval. Post-image work must not become a second content-production phase.

## 2. One image is not one user gate

The image generator still receives one target per request.

Scene round:

```text
S01 → S02 → S03 → S04 → S05 → S06 → S07 → S08 → one Batch Review
```

Taste round:

```text
FOOD01 → FOOD02 → FOOD03 → FOOD04 → one Batch Review
```

There is no user approval request between valid targets.

A runtime/card/turn boundary after one generated image is transport behavior, not an approval boundary. The round intent survives the boundary. On the next user message, reconcile the current reservation and continue toward the same batch boundary. Do not ask whether the previous valid image is approved.

Use:

```bash
python3 scripts/country_production_protocol_v2.py next {slug}
```

The command returns both deterministic NEXT and an `interaction` object. `interaction.userGate` is the machine-readable answer to whether the user may be asked for approval.

For Scene/Food generation and reconciliation, `userGate` must be `false`.
For Hero, Scene Batch, Taste Batch and canonical-page review, it is `true` at the appropriate boundary.

## 3. Image handoff is one fixed path

Protocol 2 does not alternate between assistant-side repository recovery and user-side storage.

The fixed rule is:

- generated images are shown/delivered to the user through the image-generation UI;
- after Hero + 8 Scenes + 4 Taste images are approved, create one manifest for all 13 approved raster assets;
- the user stores/uploads those 13 files to their declared repository paths in one batch;
- the user reports completion once;
- verify all 13 repository assets once as one batch;
- do not separately attempt assistant-side image materialization/recovery.

This is an operational handoff, **not an additional approval gate**.

Production State uses:

```json
"assetHandoff": {
  "mode": "USER_HANDOFF",
  "state": "PENDING",
  "expectedRasterCount": 13
}
```

After repository verification, set `state: PASS`, `verifiedRasterCount: 13`, and `verifiedAt`.

## 4. Post-visual fast path

After the user handoff, do not resume broad editorial work.

Allowed normal work:

1. verify 13 assets once;
2. perform batch conversion/size/path/hygiene checks if necessary;
3. confirm Country JSON points to the verified assets;
4. run strict Country validation;
5. build one review package;
6. integrate to `main` once;
7. run targeted Desktop / Tablet / Mobile Browser QA once;
8. present canonical URL.

Do not rebuild the Map, rewrite content, revisit taxonomy, reselect Signature Facts, or redesign Travel Scale after image approval unless a genuine blocking defect is discovered.

The target is one Review Package integration and one targeted Browser QA cycle. A real defect may require another cycle; routine progress must not.

## 5. Content QA v2

See `docs/CONTENT_QUALITY_RULES_V2.md`.

Two new hard rules:

- every Travel Scale item includes a concrete `例：`;
- forest/woodland percentage is not a routine Signature Fact. It requires `exceptionalShare:true` and must be <=10% or >=70% to pass the v2 machine gate.

## 6. State initialization

For a genuinely new Country:

```bash
python3 scripts/country_production_protocol_v2.py init {slug}
```

This builds on Revision 7 State and adds:

- `productionProtocolId: 2.0`;
- machine-readable interaction rules;
- pre-visual checklist;
- fixed USER_HANDOFF asset path;
- production metrics.

Before leaving CONTENT, mark `preVisualBuild.state = PASS` and every required check `PASS` only after the work actually exists.

Validate:

```bash
python3 scripts/country_production_protocol_v2.py validate
```

## 7. Productivity metrics

For each new Country, record enough State timing/count data to evaluate the process rather than relying on impressions.

Targets:

- per-image approval prompts: 0;
- Scene Batch reviews: normally 1;
- Taste Batch reviews: normally 1;
- image handoffs: 1;
- normal review-package integrations: 1;
- normal targeted Browser QA cycles: 1;
- measure Taste batch approval → canonical review ready time.

A regeneration round may add a batch review, but never one approval per regenerated image.

## 8. Authority

When Protocol 2 applies, use this order:

1. PROJECT MASTER INSTRUCTIONS
2. `ops/country-production-policy.json`
3. `ops/image-generation-policy.json`
4. `docs/COUNTRY_PRODUCTION_PROTOCOL_2.md`
5. current image-policy revision docs
6. authoritative Country Production State
7. image/content/map specifications
8. chat history

The production protocol controls user interaction and stage timing. The image policy controls the safety and identity of each generated image.
