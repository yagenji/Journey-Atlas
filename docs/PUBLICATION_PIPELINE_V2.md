# JOURNEY ATLAS — Publication Pipeline v2

Updated: 2026-09-14

Publication Pipeline v2 shortens the path from the approved 13-raster handoff to live publication while preserving the existing user approval gates.

## Activation

The pipeline is opt-in and machine-readable:

```json
"publicationPipelineVersion": 2
```

`new_country.py` adds this field to newly scaffolded Countries.

Existing Countries without the field remain on the legacy Protocol 2 publication path. They are **not** auto-migrated. This allows Countries already in production to finish without a workflow change beneath them.

## User gates

Pipeline v2 does not remove editorial approval gates. The intended user gates remain:

1. Hero approval;
2. Scene Batch Review;
3. Taste Batch Review;
4. final canonical Country page approval.

There is no additional user continuation gate between the 13-raster handoff and the canonical review URL.

## After the 13-raster handoff

Once `assetHandoff.state=PASS` with 13 verified rasters:

1. `publication-pipeline-v2-review.yml` detects the v2 Country;
2. one reusable review/publication PR is created automatically if needed;
3. `publication-pipeline-v2-checks.yml` runs targeted Country validation, image audit and Desktop / Tablet / Mobile Browser QA once;
4. the validated source is packaged without running Browser QA a second time;
5. only the shared GitHub Pages deployment step is serialized;
6. the persistent `/reviews/{slug}/countries/{slug}/` page is deployed;
7. the successful preview result is reconciled into authoritative Production State automatically;
8. `NEXT` becomes `REVIEW_CANONICAL_URL`.

The expensive QA/build portion can run in parallel across Countries. Only the shared Pages deployment surface is serialized.

## Browser QA reuse

A passed review Browser QA is reusable during final publication when no shared rendering code changed after the validated review source.

Shared rendering changes include Country template, shared JS, shared CSS and the targeted build/browser QA implementation. If one of those changed while the Country waited for approval, Pipeline v2 runs targeted Browser QA again after syncing latest `main`.

State-only, registry-only, unrelated-Country and publication-metadata changes do not invalidate a passed Country review Browser QA.

## After final canonical approval

A single explicit `finalApproval.state=APPROVED` write triggers the finalization workflow. No additional ChatGPT polling or `進めて` message is part of the pipeline contract.

The workflow:

1. enters the shared `country-publication-main` serialization lane;
2. snapshots the target Country's shared registry/theme metadata;
3. syncs the latest `main`;
4. resolves only known shared Country metadata conflicts while preserving the target Country's intended row/assignments;
5. prepares terminal publication State and `atlasPublished:true` registry metadata;
6. runs v2 publish checks on the exact terminal branch SHA;
7. reuses review Browser QA when shared rendering is unchanged, otherwise runs one targeted Browser QA;
8. squash-merges the same reusable PR;
9. waits for Cloudflare to expose the merge SHA and smoke-tests the target Country route and JSON.

The merge lane is shared with the legacy publication queue, so legacy and v2 Countries cannot race each other into `main`.

## Failure behavior

Pipeline v2 stops only on a concrete blocking condition:

- validation or Browser QA failure;
- unexpected merge conflict outside the known shared Country metadata files;
- latest-main churn that cannot stabilize within the configured merge cycles;
- branch-protection/merge rejection after required checks;
- Cloudflare failing to expose the merged SHA within the smoke-verification window.

A successful external step must be reconciled into State by the workflow itself. ChatGPT is not the callback mechanism.

## Legacy coexistence

During migration, old and new Countries can run together:

- legacy Country: no `publicationPipelineVersion:2` → existing Protocol 2 workflows;
- new Country: `publicationPipelineVersion:2` → Publication Pipeline v2;
- final `main` integration for both uses the same serialization group.

Do not add `publicationPipelineVersion:2` to a Country already in flight unless an explicit migration is planned and reviewed.
