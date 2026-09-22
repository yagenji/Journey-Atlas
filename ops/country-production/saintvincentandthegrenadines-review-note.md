# Saint Vincent and the Grenadines — unpublished review build

## Confirmed repository facts (2026-09-22)

- Canonical registry `data/atlas-destinations.json`: ISO2 `VC`; slug **`stvincentgrenadines`**; `atlasPublished:false`. Old branch name `saintvincentandthegrenadines` is not the canonical page slug.
- Working branch `country/saintvincent-review-build` retains 13 WebP files under `assets/images/saint-vincent/`. `IMAGE_MANIFEST.txt` records filenames, reported sizes and SHA-256. The prior `HANDOFF_README.txt` says these are byte-identical to an earlier candidate ZIP, **not** that each is an approved output.
- No `data/countries/stvincentgrenadines.json`, `ops/country-production/stvincentgrenadines.json`, or corresponding verified 1200×760 map SVG has been found on this branch. Canonical review deployment remains unverified.

## Visual audit of the exact 13-image review sheet

Inspected the saved `saint_vincent_13_image_review.jpg` contact sheet dated 2026-09-22 (see user's JOURNEY ATLAS Library). This is a visual review of the contact sheet, **not** a full decode of the GitHub WebP bytes or an approval ledger check.

| Existing asset | What is directly visible in the contact sheet | What is still unverified |
|---|---|---|
| `hero.webp` | Rugged green volcanic crater / summit | Exact location and approved original image identity; not a Tobago Cays coastal Hero |
| `scene_01.webp` | Mountainous populated bay with yachts | Named bay and location |
| `scene_02.webp` | Steep conical mountain above coastal town and bay | Exact mountain / town |
| `scene_03.webp` | Very similar conical mountain and bay | Whether distinct from scene 02 or geographically attributable |
| `scene_04.webp` | White sand, islets and shallow turquoise reef | Exact cay and photo viewpoint |
| `scene_05.webp` | Islets and turquoise lagoon | Whether distinct from scene 04 and exact viewpoint |
| `scene_06.webp` | Same broad conical-mountain / populated-bay visual family as scenes 02–03 | Distinct geographical site and identity |
| `scene_07.webp` | Waterfall in dense green forest | Exact waterfall (Dark View cannot be inferred solely from appearance) |
| `scene_08.webp` | Sandy cay and turquoise water | Exact cay and distinctness from scenes 04–05 |
| Four `taste_*.webp` | Fish with breadfruit; bakes and saltfish mixture; leafy green soup; filled/leaf-wrapped preparation | Original batch approval provenance and precise dish identity |

**Blocking content-quality observation:** 02, 03 and 06 have strikingly similar high conical mountain/coastal-bay compositions; 04, 05 and 08 repeat reef-islet imagery. The original ordered scene targets and their approval ledger must be recovered and checked before claiming these eight files represent eight geographically distinct, accurate places. In particular, do not attach guessed location names or coordinates to these generic filenames.

## Primary-source editorial groundwork — not an approved scene/image mapping

The tourism ministry places Kingstown on Saint Vincent's southwest coast and the Grenadines to its south; Bequia, Mustique, Canouan and Union Island are among the larger islands. Tobago Cays lie east of Mayreau and include five islets, lagoons and reefs. Source https://tourism.gov.vc/tourism/index.php/svg-facts/72-essentials (checked 2026-09-22). The National Parks authority documents La Soufrière, Dark View Falls, the Botanical Gardens and Owia Salt Pond, while the ministry documents Fort Charlotte above Kingstown. Sources https://nationalparks.gov.vc/nationalparks/index.php/visitors-sites ; https://tourism.gov.vc/tourism/index.php/national-sites-of-svg (checked 2026-09-22). These are *research leads*, not a verified order of the saved scene images. Government describes the national dish as roasted breadfruit and fried jackfish: https://www.gov.vc/index.php/visitors/culture-festivals (checked 2026-09-22).

## Required next work before a genuine review page

1. Recover original approved images / prompt-specific site identities, ordered scene list and Taste batch approval records; verify all 13 GitHub WebP files by hash and complete decode against their actual approved targets. If the 8 scenes do not meet eight-site diversity, follow the established image approval procedure rather than silently assigning false captions.
2. Build canonical-slug Country JSON with sourced copy, coordinates, taxonomy and common 1200×760 accurate SVG, without copying shared UI per country. Complete required editorial and geographic QA.
3. Only after verification, run targeted preview and real Desktop / Tablet / Mobile QA, merge unpublished review according to current main production rules, and verify `https://atlas.yagenji.com/countries/stvincentgrenadines/`. Keep `atlasPublished:false`, `noindex,follow`, no links in ordinary navigation and no sitemap entry until explicit final page approval.

**Current status: assets staged; canonical Country review page is NOT complete or verified live.** This audit is not an additional approval gate or a substitute for the production workflow.
