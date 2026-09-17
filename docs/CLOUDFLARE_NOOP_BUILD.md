# Cloudflare Pages: guarded no-op build skipping

Cloudflare Pages must deploy every change that can affect JOURNEY ATLAS production runtime, Country content, image delivery, publication state, or production QA. The `main` branch remains the production source. A missing Cloudflare check run is **not** proof that a deployment succeeded.

## Strictly non-runtime changes

`scripts/expected_cloudflare_commit.py` allows a previous deployed SHA only when **every commit since that SHA** changes exclusively the paths below:

- `docs/**`
- `ops/country-production/**` (Country authoring/QA State records, not `ops/country-production-policy.json`)
- `.github/workflows/audit-icons.yml`
- `.github/workflows/validate-visual-policy-waivers.yml`

Any other changed file, a mixed runtime/non-runtime commit, or an empty/unknown diff requires the current commit's exact SHA. Never skip `data/countries/**`, `data/atlas-destinations.json`, `data/theme-taxonomy.json`, approved images, build scripts, production-verification workflows, or policy files. User final approval and `atlasPublished` remain independent mandatory gates.

## One-off GitHub-only proof

1. Confirm the previous `main` Cloudflare deployment succeeded and the production verification workflow passed. Inspect the actual PR diff; it must contain **only** the allowlisted paths.
2. Merge the PR using squash, with `[CF-Pages-Skip]` as the **prefix** of the squash commit title. Cloudflare documents that this skips the Pages deployment without dashboard configuration; GitHub PR checks still run normally.
3. Confirm the merge commit's actual title and that Cloudflare did not create a new deployment/check run for that commit. Check the live `/build-meta.json` SHA using the production-verification workflow rather than inferring it from the missing check.
4. Dispatch `.github/workflows/verify-production.yml` on the latest `main` with no slug. Its SHA guard may accept only the latest SHA or a consecutive, proven non-runtime ancestor; the full published and unpublished QA checks must pass. If Cloudflare did build this safe commit despite the prefix, the latest SHA is equally valid.
5. Repeat with a mixed code/State change in an ordinary **non-skipped** PR: the SHA guard must require an exact deployed SHA; no commit-message skip is permitted. A true Country publication requires separate explicit user approval and cannot be used as a disposable skip test.

When **only this runbook** changes in a `[CF-Pages-Skip]`-prefixed `main` commit, `.github/workflows/verify-cloudflare-noop-skip.yml` automatically dispatches the existing full production verifier. Confirm that the dispatch job succeeds, its separate live-QA workflow finishes, and the live SHA matches a proven safe ancestor; never count a skipped Pages check alone as a QA pass.

## Optional project-wide Build watch paths

Cloudflare account authorization is required. **Do not assume** the Pages dashboard has any particular current setting. Once authorized, inspect `journey-atlas` Build settings, production branch, preview branch and existing watch paths before changes. Begin with a narrow allowlist of exclusions, not `.github/*` or every `ops/*`. Cloudflare's rule evaluates excludes first and builds when any remaining changed path matches the includes. Never disable automatic production branch deployment.

Official references: https://developers.cloudflare.com/pages/configuration/build-watch-paths/ and https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/ .

## 2026-09-17 permanent-watch verification

The account owner supplied a Cloudflare Pages `journey-atlas` Settings screenshot after saving: production branch `main`, automatic deploy enabled, Include `*`, and four separately listed Exclude paths: `docs/*`, `ops/country-production/*`, `.github/workflows/audit-icons.yml`, `.github/workflows/validate-visual-policy-waivers.yml`. This is a dashboard screenshot confirmation, **not** a Cloudflare API settings read. Do not change the publication flag or assume the skip works merely because the paths appear.

This docs-only change deliberately uses a **normal merge title without `[CF-Pages-Skip]`**. Its purpose is to test the saved project-wide Build watch paths. After merge, inspect the Cloudflare check/deployment record and use the existing production verifier to compare the deployed SHA with the source through the approved non-runtime guard. Next, test a mixed docs + non-excluded verification-workflow change with a normal merge title: it must create a real Pages deployment at the exact new SHA and pass live runtime/browser QA. Do not close issue #863 before actual results are recorded.
