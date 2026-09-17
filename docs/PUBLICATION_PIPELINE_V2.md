# JOURNEY ATLAS — Publication Pipeline v2

Updated: 2026-09-16. Canonical review amendment: `docs/CANONICAL_UNPUBLISHED_REVIEW.md` and `ops/country-production-policy.json` (`canonicalReviewAmendment:1`).

Publication Pipeline v2 retains all approval gates and the verified 13-raster handoff. The GitHub Pages review is a staging QA surface, **not** the final Country review URL. The final page review takes place on the unpublished canonical production URL, with `atlasPublished:false`, `noindex,follow`, no normal discovery links, and no sitemap entry. Formal publication remains a separate post-approval action.

## Activation and compatibility

A new Country opts into v2 via `publicationPipelineVersion:2` in its Country JSON. Existing Countries without this field remain on their legacy path and are not automatically migrated. Do not add v2 to an in-flight legacy Country without an explicitly reviewed migration.

## User gates

The only editorial approval gates are Hero, the eight-scene batch, the four-Taste batch, and the final canonical Country page. The 13-image repository handoff is a distinct required operational action, not a request to approve each image again. No `進めて` or additional ChatGPT polling is required between deterministic steps.

## After the 13-raster handoff

1. `publication-pipeline-v2-review.yml` ensures one staging review PR, runs targeted Country/asset validation and Desktop / Tablet / Mobile Browser QA, deploys its persistent GitHub Pages staging preview, and reconciles successful staging QA into the Country branch State.
2. `canonical-country-review.yml` takes only a reviewed, unchanged, still-unpublished v2 Country. In the `country-publication-main` serialization lane it applies its Country-only overlay to latest main, corrects only validated mechanical metadata defects, and runs strict editorial, map, image, icon, State and targeted Browser QA. Approved rasters are not regenerated or changed.
3. Once required PR checks pass, the staging review PR is merged while `atlasPublished:false` and final approval remains pending. The production build includes that Country at `https://atlas.yagenji.com/countries/{slug}/`, but excludes it from discovery and sitemap and emits `noindex,follow`.
4. The canonical review workflow verifies the exact Cloudflare deployed SHA, the actual Country route, runtime registry, noindex and sitemap exclusion, and performs live Desktop / Tablet / Mobile Browser QA. Only successful verification is recorded in the Country branch State; a CI success or queued deploy alone does not count as reviewed.
5. The user reviews the real canonical Country URL and can request fixes there.

The staging preview Browser QA can be reused only when reviewed Country content and shared rendering remain unchanged. The canonical integration checks and live Browser QA are separate required gates because they verify the actual production host. The workflow stops on changed approved content, failed validation, unexpected branch/main movement, deployment mismatch, or failed live QA.

## After final canonical approval

Only an explicit `finalApproval.state=APPROVED` on the Country branch permits final publication. Because the unpublished review PR was already merged, the serialized v2 finalizer opens a publication PR as needed, rebuilds a Country-only overlay on latest main, applies terminal State and `atlasPublished:true`, runs publish checks on the exact terminal head, and squash-merges. Cloudflare must expose the merged SHA and pass the target-route and JSON smoke test. Only then may the Country be reported as published.

Browser QA may be reused during final publication only if the reviewed source and shared rendering remain eligible. Changes to shared Country template, CSS, JS, build, or QA code invalidate that reuse. State-only changes do not.

## Failure and legacy coexistence

A failed step is a hard blocker with its actual error and run ID; no tool or assistant may report completion in its place. Review integration does not grant publication permission. The `country-publication-main` queue serializes canonical review integration and formal publication so simultaneous Countries do not overwrite shared metadata. Legacy Countries continue through their existing workflows and use the same final merge lane.