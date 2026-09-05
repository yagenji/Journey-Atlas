# Required PR quality gates

JOURNEY ATLAS protects `main` with pull-request-only merges. The following GitHub Actions checks are designed to be safe as required status checks.

## Pre-merge required checks

- `validate` — runs on every pull request and performs source syntax checks, renewal registry audit, published image audit and hard gate, Country JSON validation, JOURNEY LENS slug validation, and Cloudflare package build validation.
- `browser-qa` — runs on every pull request so the status context always resolves. For Country-page-impacting changes it builds the production package and runs all published Countries at Desktop, Tablet, and Mobile viewports. For unrelated changes it returns success without spending the full browser suite.

Do not make the production verification workflow a pre-merge required check. It intentionally runs after changes reach `main` and verifies the actual Cloudflare production deployment.

## Ruleset

The repository ruleset should require `validate` and `browser-qa` to pass before merging to `main`.

Keep the existing protections:

- pull request required
- branch deletion blocked
- force pushes blocked
- squash merge only
- review conversations resolved before merge

