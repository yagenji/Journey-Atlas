# JOURNEY ATLAS Roadmap

Updated: 2026-08-23

## Production rule

JOURNEY ATLAS country pages are created from countries/regions currently published in JOURNEY LENS first. The source of truth for the current publication state is `yagenji/Journey-Lens/content/top_countries.json`; entries with `show: true` are eligible for priority production.

The synchronized snapshot for ATLAS is `data/journey-lens-published.json`.

## Current state

- Top page: **locked / production baseline**
- Iceland: structure and interaction implemented; final visual replacement / final QA next
- 199 destination registry: complete
- 199 destination illustration production: parallel workstream; not a top-page release blocker
- GitHub Pages workflow: present
- Current JOURNEY LENS published set: 19 countries/regions

## Immediate priority

1. Keep the top page locked. Fix only bugs, responsive defects, accessibility issues, and approved-art replacements.
2. Finish Iceland as the reference country page.
3. Lock the Iceland page structure as the reusable country-page template.
4. Start country-page production from the current JOURNEY LENS published set.
5. Continue 199 destination card illustrations in parallel without blocking country pages.

## Next country-page production batch

Use the JOURNEY LENS display order as the default sequence unless there is a clear visual/content reason to reorder:

1. Antarctica
2. Tajikistan
3. Kyrgyzstan
4. Uzbekistan
5. Kazakhstan

After that: India, Saudi Arabia, Oman, Cuba, Guatemala, Costa Rica, Bolivia, Argentina, Chile, Tanzania, Namibia, Lesotho, Australia.

## Visual rules already decided

- Adult visual travel atlas, not a conventional travel-information site.
- JOURNEY ATLAS and JOURNEY LENS must look clearly different: ATLAS = illustration; LENS = photography and personal travel stories.
- Country/destination illustration target is approximately **photo 60 / illustration 40**.
- Every illustration is based on a real named landscape or place.
- Real geography, architecture, vegetation, coastlines, and landmark relationships take priority over decorative invention.
- Painterly simplification should remain visible so the image does not read as stock photography.
- No landmark collage, no text, no flags, no UI, no watermark inside illustrations.
- Country maps may use illustration-only visual treatment while broadly preserving geography and place relationships.
- JOURNEY ATLAS wordmark has no leading symbol.
- Related countries: small flag + English/Japanese country name + one short reason.
- Current Unicode symbols/icons are temporary and must not be treated as the final icon system.
- Do not require a dedicated hero/image asset for every related country before that country page exists.

## Release workflow

1. Implement safely on `main`.
2. Validate country JSON.
3. GitHub Pages deploys from the configured workflow.
4. Review in browser.
5. Only stop for material design/content decisions.

## Definition of done — country page template

Iceland becomes the template when all of the following are true:

- hero uses a real-place production illustration in the locked ATLAS style;
- 8 scene illustrations use the same style and represent real places;
- map markers and scene cards remain synchronized;
- navigation has no dead controls;
- responsive behavior is stable;
- wish-list behavior works;
- related-country section is usable even when related pages are not yet published;
- data validation passes.
