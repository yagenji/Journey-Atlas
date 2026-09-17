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

## Permanent project-wide Build watch paths

The production Pages project `journey-atlas` uses production branch `main`, automatic production deployment remains enabled, Include paths is `*`, and these four Exclude paths are configured:

- `docs/*`
- `ops/country-production/*`
- `.github/workflows/audit-icons.yml`
- `.github/workflows/validate-visual-policy-waivers.yml`

Do not broaden these exclusions to all `.github/*`, `ops/*`, `data/*`, or `scripts/*`. Cloudflare evaluates excludes first, while any remaining included path in the same change must still trigger a build. These rules intentionally mirror the SHA-equivalence safe allowlist.

## 2026-09-17 permanent-setting proof

The account owner confirmed the saved `journey-atlas` dashboard settings above. Real production behavior was then tested without changing any Country approval or publication state:

- **Excluded-only:** ordinary, unprefixed docs-only PR #868 merged as `447ad4df6c647abedc21fad12bc0c5c804659878` and did not create a Cloudflare Pages deployment for that commit. A subsequent production verifier confirmed the live runtime remained on the proven deployable ancestor while the non-runtime SHA guard accepted only the documented safe chain.
- **Mixed excluded + runtime:** PR #873 changed this excluded runbook together with a harmless comment-only change to non-excluded `404.html`. Cloudflare created and successfully deployed exact merge SHA `0e092597b53ada90324648fd933970bdeb78c94b`. Production verification run `35172868131` passed; the live `/build-meta.json` SHA was exactly `0e092597b53ada90324648fd933970bdeb78c94b`, so the strict runtime gate did not rely on ancestor equivalence.
- **Cleanup:** PR #874 removed the temporary `404.html` test comment, restoring its pre-test content. Cloudflare successfully deployed cleanup SHA `ee0afc601743631c8ad695dfdc3af4bca5608269`, and the production runtime verification passed against that cleanup commit.

The final docs-only proof in #875 triggered full production QA against the safely equivalent deployed cleanup SHA; production runtime, published browser QA, and unpublished-reviewable browser QA succeeded in run `35173403625`.

## Published Country QA productivity acceptance

PR #876 adds a bounded four-worker wrapper for **full published** Country browser QA while retaining the existing Country, Desktop/Tablet/Mobile, accessibility, image and map checks. Targeted and unpublished-reviewable QA retain the original runner. The PR's targeted smoke check does not exercise the full four-worker path. This docs-only `[CF-Pages-Skip]` proof triggers a separate full production verifier after #876's exact-SHA deployment to verify that all published Countries pass using the parallel runner, the merged report contains no failures, and unpublished-reviewable QA remains green. Do not call the parallel optimization completed until the full run finishes successfully.

Official references: https://developers.cloudflare.com/pages/configuration/build-watch-paths/ and https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/ .
