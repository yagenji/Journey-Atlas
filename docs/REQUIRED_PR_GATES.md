# Required PR quality gates

JOURNEY ATLAS protects `main` with pull-request-only, squash-only merges.

## Required checks

The repository ruleset requires these status contexts on every pull request:

- `validate`
- `browser-qa`

Both workflows therefore start on **every PR** so the required status always resolves.

### validate

For an affected Country, it runs the finish-line checks that matter to the changed artifact:
- Country schema/data QA;
- editorial/content QA;
- Map geometry/coordinate/label QA;
- image path/decode/dimension/duplicate QA;
- shared registry audits.

A publication-metadata-only PR does not repeat unchanged Country content/image/map QA. It validates publication/registry consistency and reuses the already-reviewed Country result.

Unrelated PRs resolve the required status without starting a Country production process.

### browser-qa

The workflow first inspects the PR diff.

- target Country rendering change → build and test only the affected Country at Desktop / Tablet / Mobile;
- shared rendering/build change → broader browser regression;
- unrelated or publication-metadata-only change → return success without the expensive browser suite.

## Post-merge production verification

`.github/workflows/verify-production.yml` is not a pre-merge required check.

After a runtime-affecting change reaches `main`, it verifies:
- Cloudflare serves the merged SHA;
- shared runtime assets load;
- changed Country routes/payloads exist;
- live Browser QA runs only for the relevant target or shared scope.

## Ruleset

Keep:
- pull request required;
- required checks: `validate`, `browser-qa`;
- strict up-to-date branch requirement;
- branch deletion blocked;
- force pushes blocked;
- squash merge only;
- review conversations resolved before merge.
