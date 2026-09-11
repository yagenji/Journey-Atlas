# JOURNEY ATLAS — Country Production Protocol 2.0

Updated: 2026-09-11

Machine-readable authority: `ops/country-production-policy.json`.
Image-generation authority remains `ops/image-generation-policy.json`.

Protocol 2.0 is the default for **new Country production**. It is based on the Japan / Indonesia / Cambodia / North Korea production review and addresses five separate bottlenecks:

1. Scene/Taste generation could still be interpreted as one-image-one-user-approval despite Revision 7/7.1.
2. Generated-image repository materialization followed two different paths.
3. Most Country implementation work still happened after image approval, leaving a long post-image critical path.
4. Country-only changes still triggered all-Country validation/build/package work before targeted Browser QA.
5. Canonical review previously required a main integration first, causing an unnecessary production build before final user approval.

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
→ targeted Country-only preview build on country/{slug}
→ one targeted Browser QA cycle
→ targeted GitHub Pages review URL
→ final Country-page user approval
→ one terminal publication PR / main integration
→ one production deployment + targeted production verification
```

**Main must not be used as the preview environment for a normal new Country.**

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
For Hero, Scene Batch, Taste Batch and final Country-page review, it is `true` at the appropriate boundary.

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

After the user handoff, do not resume broad editorial work and do not rebuild unrelated Country pages.

For a normal Country-only change, the allowed path is:

1. verify the 13 approved assets once;
2. perform target-Country conversion/size/path/hygiene checks if necessary;
3. confirm the target Country JSON points to the verified assets;
4. run strict validation for the target Country only;
5. build a **targeted Country preview package** containing only the requested Country page, target Country JSON, referenced Country images and shared runtime assets;
6. run targeted Desktop / Tablet / Mobile Browser QA once;
7. deploy that targeted package from `country/{slug}` to the shared GitHub Pages review surface;
8. present the review URL to the user;
9. only after explicit final page approval, create the one terminal publication PR and integrate to `main` once;
10. allow the normal full production build once, then run targeted production verification for the published Country.

Use:

```bash
python3 scripts/build_country_preview_targeted.py --slugs {slug}
```

The Country branch remains the authoritative content/state source through the final page-review gate. `main` becomes authoritative only when the approved terminal publication change is integrated.

A normal Country-only review must **not** run:

- all reviewable Country JSON validation;
- all published Country image audit/hard gate;
- all reviewable Country static-page generation;
- all Country package assembly;
- all published Country Browser QA;
- a production Cloudflare build before the user has approved the final Country page.

Those full-scope operations are reserved for:

- shared Country template changes;
- shared CSS / JavaScript changes;
- production build-system changes;
- explicit manual Full QA;
- the one real production deployment after final approval.

The production Cloudflare builder remains unchanged and continues to perform the full production build when a real production deployment requires it. The targeted builder is a review/CI fast path, not a replacement for production packaging.

Do not rebuild the Map, rewrite content, revisit taxonomy, reselect Signature Facts, or redesign Travel Scale after image approval unless a genuine blocking defect is discovered.

The normal target is one targeted review deployment, one targeted Browser QA cycle, zero pre-approval main integrations, and one final production integration. A real defect may require another targeted review cycle; routine progress must not.

## 5. Content QA v2

See `docs/CONTENT_QUALITY_RULES_V2.md`.

Two new hard rules:

- every Travel Scale item includes a concrete `例：`;
- forest/woodland percentage is not a routine Signature Fact. It requires `exceptionalShare:true` and must be <=10% or >=70% to pass the v2 machine gate.

For a normal Country-only change, Content QA v2 runs against the target Country only. Full Content QA is reserved for shared/full-scope changes.

## 6. State initialization and pre-main review gate

For a genuinely new Country:

```bash
python3 scripts/country_production_protocol_v2.py init {slug}
```

This builds on Revision 7 State and adds:

- `productionProtocolId: 2.0`;
- machine-readable interaction rules;
- pre-visual checklist;
- fixed USER_HANDOFF asset path;
- `reviewPreview` for the targeted Country-branch review deployment;
- production metrics.

Before leaving CONTENT, mark `preVisualBuild.state = PASS` and every required check `PASS` only after the work actually exists.

Protocol 2 intentionally does **not** enter the legacy `REVIEW` phase before final approval, because legacy `REVIEW` resolves authority to `main`.

Instead, after target QA passes:

- keep `phase: QA`;
- keep `contentRef: country/{slug}`;
- keep `stateRef: country/{slug}`;
- set `reviewPreview.mode = TARGETED_COUNTRY_BRANCH_PREVIEW`;
- after the targeted GitHub Pages deployment and Desktop / Tablet / Mobile QA pass, set `reviewPreview.state = DONE`, `reviewPreview.browserQa = PASS`, and record the actual review URL;
- Protocol 2 NEXT then returns `REVIEW_CANONICAL_URL` as the user gate without moving content to `main`;
- after explicit final approval, Protocol 2 NEXT returns `CREATE_TERMINAL_PUBLICATION_PR`;
- the terminal publication PR moves content/state authority to `main`, publishes the Country, and completes the State.

Existing legacy or already-integrated States are not migrated and remain valid under their existing `REVIEW/main` representation.

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
- pre-canonical main integrations: 0;
- normal targeted review deployments: 1;
- normal targeted Browser QA cycles: 1;
- production integrations after final approval: 1;
- Country-only post-visual full-Country builds before approval: 0;
- Country-only post-visual full-Country Browser QA cycles: 0;
- measure Taste batch approval → final review URL ready time.

A regeneration round may add a batch review, but never one approval per regenerated image.

GitHub Pages remains a shared review surface and therefore its deployment queue stays serialized to avoid preview overwrite races. The productivity improvement comes from each queued deployment being target-only rather than a full-Country production build.

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
