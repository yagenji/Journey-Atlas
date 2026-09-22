# Saint Vincent and the Grenadines — unpublished review build

## Confirmed repository facts (2026-09-22)

- Canonical destination registry: `data/atlas-destinations.json`, ISO2 `VC`, slug **`stvincentgrenadines`**, `atlasPublished:false`. The older branch name `saintvincentandthegrenadines` is not the canonical page slug.
- Working branch: `country/saintvincent-review-build`, retaining the 13 WebP files in `assets/images/saint-vincent/` from `country/saintvincentandthegrenadines`. See `IMAGE_MANIFEST.txt` for all 13 filenames, reported dimensions, byte counts and SHA-256 values.
- `HANDOFF_README.txt` states these 13 assets match an earlier candidate ZIP byte-for-byte but **does not establish that each matches an individually or batch-approved image**. Neither image identity nor actual binary decode has been independently verified here.
- As of this check, `data/countries/stvincentgrenadines.json`, `ops/country-production/stvincentgrenadines.json`, and the target 1200×760 map SVG are absent. No rendered Country Page or canonical review deployment has been verified.

## Required before an unpublished canonical review

1. Reconcile Hero / each of the eight scene identities and ordered filenames / each of the four Taste identities against their original visual approvals, without treating the candidate ZIP as proof of approval. Preserve the original approved images; verify complete decode, SHA-256, dimensions, and all paths.
2. Complete the canonical-slug Country JSON, source-supported editorial material, exact scene coordinates, and geographically sourced SVG using the existing common 1200×760 Map language; validate map labels, geographic coverage, taxonomy and the shared template. Do not guess an image's location from its generic filename.
3. Run targeted Country QA and actual Desktop / Tablet / Mobile rendering; only then follow the existing unpublished-review PR and canonical deployment process. Keep `atlasPublished:false`, `noindex,follow`, no normal navigation link and no sitemap inclusion, pending explicit final page approval.

**Status: not reviewable; do not claim the canonical page is live or authorized for publication.** This note records verified conditions, not an extra approval gate or a replacement production workflow.
