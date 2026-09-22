# Saint Vincent and the Grenadines — unpublished review build

## Confirmed repository facts (2026-09-22)

- Canonical destination registry: `data/atlas-destinations.json`, ISO2 `VC`, slug **`stvincentgrenadines`**, `atlasPublished:false`. The older branch name `saintvincentandthegrenadines` is not the canonical page slug.
- Working branch: `country/saintvincent-review-build`, retaining the 13 WebP files in `assets/images/saint-vincent/` from `country/saintvincentandthegrenadines`. See `IMAGE_MANIFEST.txt` for all 13 filenames, reported dimensions, byte counts and SHA-256 values.
- `HANDOFF_README.txt` states these 13 assets match an earlier candidate ZIP byte-for-byte but **does not establish that each matches an individually or batch-approved image**. Neither image identity nor actual binary decode has been independently verified here.
- As of this check, `data/countries/stvincentgrenadines.json`, `ops/country-production/stvincentgrenadines.json`, and the target 1200×760 map SVG are absent. No rendered Country Page or canonical review deployment has been verified.

## Editorial groundwork from public primary sources — not a final Country JSON

The official tourism ministry describes Saint Vincent as the northernmost and largest island; its capital Kingstown lies on the southwestern coast. The Grenadines extend south, including Bequia, Mustique, Canouan, Union Island and smaller inhabited Mayreau. Tobago Cays lie east of Mayreau and comprise five small islands, lagoons and coral reefs. This north-to-south separation should be legible in the Hero lead and geographically accurate map rather than reduced to a single main-island view. Source: https://tourism.gov.vc/tourism/index.php/svg-facts/72-essentials (checked 2026-09-22).

Primary-source **scene-location candidates** for independent verification against the eight actual approved image files; these are **not an ordered scene list and are not assigned to `scene_01`–`scene_08`**: La Soufrière volcanic mountain; Dark View Falls; Fort Charlotte above Kingstown; Owia Salt Pond on the northeastern coast; Bequia; Mayreau and nearby southern Grenadines; Union Island; Saint Vincent Botanical Gardens. The Ministry of Tourism additionally documents the Tobago Cays, and the National Parks authority documents the volcanic trail, falls, gardens and salt pond. Sources: https://nationalparks.gov.vc/nationalparks/index.php/visitors-sites ; https://tourism.gov.vc/tourism/index.php/national-sites-of-svg (checked 2026-09-22). Never infer scene order or visual identity solely from these candidate names.

The government describes the national dish as **fried jackfish with roasted breadfruit**. The existing food filenames imply candidate categories `roasted_breadfruit_fish`, `bake_saltfish`, `callaloo`, and `ducana`, but the latter three must be visually inspected, researched against the country rather than conflated with other Caribbean islands, and checked against the original batch approval. Sources: https://www.gov.vc/index.php/visitors/culture-festivals ; https://tourism.gov.vc/tourism/index.php/festivals-a-events/65-breadfruit-festival (checked 2026-09-22).

## Required before an unpublished canonical review

1. Reconcile Hero / each of the eight scene identities and ordered filenames / each of the four Taste identities against their original visual approvals, without treating the candidate ZIP as proof of approval. Preserve the original approved images; verify complete decode, SHA-256, dimensions, and all paths.
2. Complete the canonical-slug Country JSON, source-supported editorial material, exact scene coordinates, and geographically sourced SVG using the existing common 1200×760 Map language; validate map labels, geographic coverage, taxonomy and the shared template. Do not guess an image's location from its generic filename.
3. Run targeted Country QA and actual Desktop / Tablet / Mobile rendering; only then follow the existing unpublished-review PR and canonical deployment process. Keep `atlasPublished:false`, `noindex,follow`, no normal navigation link and no sitemap inclusion, pending explicit final page approval.

**Status: not reviewable; do not claim the canonical page is live or authorized for publication.** This note records verified conditions and researched editorial groundwork, not an extra approval gate or a replacement production workflow.
