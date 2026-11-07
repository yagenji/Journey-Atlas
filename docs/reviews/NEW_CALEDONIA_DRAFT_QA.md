# New Caledonia Region — Draft QA (2026-11-07)

Status: **DRAFT / NO MERGE / NO PUBLICATION**.

## Prepared on this branch
- `data/regions/france/new-caledonia.json`: parent=france, slug=new-caledonia, `regionPublished: false`.
- `assets/images/france/new-caledonia/map-new-caledonia.svg`: 1200×760 main map and geographic position overview inset in upper left.
- 1 Hero + 8 scenes + 4 Taste metadata, plus basic facts, parent relation, map, culture, trivia, travel itinerary, seasons, references.
- The 200-country registry and its denominator are **unchanged**.

## Local reviewer QA (standalone HTML, not production template)
Tested 1440×900 desktop, 834×1112 tablet, 390×844 smartphone:
- 13 image files decoded successfully; 0 missing;
- horizontal overflow: none on all 3 widths;
- all 8 numbered scene markers exist, and no scene 6/Nouméa capital overlap after label-only offset + callout;
- 8 positions + Hero match the SVG map's WGS84 anchor metadata;
- `wish` toggle changed its aria-pressed state correctly on all 3 widths;
- uncaught JS errors: 0;
- reference image names and scene paths unique.

## Geography and caveats
- The larger main map is a geographic detail of Grande Terre, Île des Pins, Loyalty Islands and Bélep group.
- The upper-left separate panel is an overview to include geographically distant reefs/islands (Chesterfield, Bellona, Huon, Surprise, Astrolabe, Walpole, Matthew, Hunter). Dots denote coordinates **only**, not inferred land outlines.
- The disputed status of Matthew/Hunter (France and Vanuatu) is noted outside the map. See French law Loi n° 99-209 (art.1) and Vanuatu PMO (2026-09-02).
- Population: 264,596 (2025 census). Area: 18,575 km² (UN 2026 report).
- Fine coastline rendering and point geography must be re-verified on the canonical page as a separate Map QA.

## BLOCKERS before main merge
1. **13 approved WebP image binaries are NOT committed to GitHub**. They are available in local transfer archive `JOURNEY_ATLAS_New_Caledonia_13_APPROVED_IMAGES.zip`; see `ops/upload_new_caledonia_images.sh`.
2. Without those binaries, `scripts/build_region_pages.py` should fail approved-image existence checking. **Do not bypass** that check using placeholders or alternate images.
3. Canonical generated page and actual deployed browser QA are **NOT yet passed**.
4. User final page approval is required **before** publication or adding general navigation.
