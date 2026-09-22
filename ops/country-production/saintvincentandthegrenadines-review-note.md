# Saint Vincent and the Grenadines — unpublished review evidence

## Canonical repository and status (checked 2026-09-22)

- Destination registry: `data/atlas-destinations.json`; slug `stvincentgrenadines`; `atlasPublished:false`. Branch `country/saintvincent-review-build` has 13 WebP assets under `assets/images/saint-vincent/` and their `IMAGE_MANIFEST.txt`.
- `HANDOFF_README.txt` explicitly calls these WebPs byte-identical to an *earlier candidate ZIP*, not verified copies of each approved image.
- The target `data/countries/stvincentgrenadines.json`, `ops/country-production/stvincentgrenadines.json` and complete, validated 1200×760 SVG map were absent when checked. There is no verified canonical preview deployment.

## Original scenic-place proposal independently recovered from prior production conversation

The September 19 production discussion named **eight distinct proposed sites**: (1) La Soufrière volcano, (2) Dark View Falls, (3) the view from Fort Charlotte above Kingstown, (4) Owia Salt Pond, (5) Bequia, (6) Mayreau and its surrounding islands, (7) Union Island, and (8) the St Vincent Botanical Gardens. **This is a recovered proposal, not evidence of final S01–S08 ordering, eight individually approved generated outputs or their association with `scene_01.webp`–`scene_08.webp`.** An earlier Hero candidate was Tobago Cays, but the current saved `hero.webp` visually shows a volcanic crater; do not replace an approved Hero or label its location based only on this early candidate.

Primary-source site verification: National Parks Authority https://nationalparks.gov.vc/nationalparks/index.php/visitors-sites and https://nationalparks.gov.vc/nationalparks/index.php/recreation/17-recreation-site-seeing/16-owia-salt-pond-recreational-site and https://nationalparks.gov.vc/nationalparks/index.php/sites/15-hiking-and-adventure/11-dark-view-falls ; Ministry of Tourism https://tourism.gov.vc/tourism/index.php/national-sites-of-svg ; checked 2026-09-22.

## Exact saved 13-image contact-sheet visual cross-check

The user’s saved `saint_vincent_13_image_review.jpg` (September 22) shows one crater Hero, **four bay/steep-green-mountain views** (`scene_01,02,03,06`), **three pale-sand/turquoise-cay views** (`scene_04,05,08`), **one forest waterfall** (`scene_07`), and four plated dishes. In particular `scene_02`, `scene_03` and `scene_06` depict highly similar mountain-and-bay settings, while `scene_04`, `scene_05` and `scene_08` depict reef-islet settings. No saved scene clearly depicts a botanical garden or Owia Salt Pond; neither can be truthfully identified by assigning those names to an arbitrary bay or cay image. The waterfall can be described generically but its identity as Dark View Falls is not established by visual appearance alone.

This establishes an actual **site-coverage/provenance blocker**, not merely a missing user-supplied list. Do not fabricate scene labels, coordinates, historical approval ledger, generated-image IDs or duplicate-site distinctness. The contact sheet is a visual audit, not a full WebP byte decode or hash comparison.

## Path to genuine, unpublished Country review

1. Independently cross-check the previously approved original image outputs or source prompt/approval log against the 13 delivered WebP hashes, preserving genuinely approved files. For image targets that cannot be attributed to their proposed sites, handle replacements via existing Scene batch approval procedure; do not re-generate good approved images simply to satisfy a filename convention.
2. Produce the canonical-slug Country JSON and geographically sourced common 1200×760 SVG, with factual references, actual scene coordinates, theme taxonomy and shared-template validation. Do not promote this audit into a new workflow or Country-specific UI.
3. Validate final image bytes, run target editorial/map and actual Desktop/Tablet/Mobile browser QA, and promote only via the normal unpublished-review process. During review keep `atlasPublished:false`, `noindex,follow`, no sitemap inclusion or normal navigation link. Final publication requires the user's separate approval.

**Status: review page not built; no claim of live canonical review or of completed QA.**
