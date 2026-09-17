# Cloudflare Pages Build watch paths: mixed-change proof

This record accompanies issue #863 and `docs/CLOUDFLARE_NOOP_BUILD.md`. The account owner confirmed the `journey-atlas` dashboard shows production `main`, Include `*`, and the four narrowly scoped exclusions described in that runbook.

The unprefixed docs-only PR #868 merged as `447ad4df6c647abedc21fad12bc0c5c804659878` and received no Cloudflare Pages commit check. Following docs-only PR #869 merged as `24e0eb16a7ad83216d74275ea735ec19e4b53522` with a `[CF-Pages-Skip]` title only to trigger a fresh full production verifier. Its runtime logs confirmed that production still served `c77f5d8606e56bba716f82e27d9e4a9c774ddeb7`, proving #868 had not caused a Cloudflare deployment. Only consecutive docs-only commits were accepted as SHA-equivalent.

## Mixed-change test

This document (an excluded `docs/*` path) and a comment in `scripts/build_cloudflare.py` (a **non-excluded** production build script) are changed together and squash-merged as a single ordinary commit without `[CF-Pages-Skip]`. The script's behavior is unchanged; its comment explains why production metadata must retain the exact deployed SHA. Cloudflare must create a Pages deployment for the mixed commit and emit that exact commit SHA in `/build-meta.json`; the production verifier must not accept the preceding deployed ancestor. The published and unpublished-reviewable site/browser QA must remain green.

This is a source/build-system verification only, not a Country publication or a substitute for user approval. No Country JSON, images, `atlasPublished`, robots, sitemap, or discovery link is changed. Verify actual Cloudflare deployment and the exact live SHA before marking the mixed-case test complete.
