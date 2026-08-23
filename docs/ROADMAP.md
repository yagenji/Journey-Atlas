# JOURNEY ATLAS Roadmap

Updated: 2026-08-23

## PM rule

The assistant acts as project manager and keeps production moving without stopping for routine implementation decisions. Ask the user only when a decision would materially change the brand, information architecture, destination definition, legal/privacy position, or an already approved visual direction.

## Production rule

JOURNEY ATLAS is currently in a **top visual completion phase**. Finish the visual system for the top page first while using Iceland as the single reference country page for template validation. Do not mass-produce other country pages until the top visual system and Iceland template are stable.

The destination scope is **201 destinations**:

- 193 UN Member States
- Vatican City, Kosovo, Cook Islands and Niue
- Taiwan
- Hong Kong
- Macao
- Antarctica

## Current state

- Top page structure / discovery UX: **production baseline**
- Top destination scope: **201 destinations**
- Top destination illustration production: **in progress**
- Hero production set: **5 production visuals planned**
- Iceland: structure and interaction implemented; production art / final QA remains
- GitHub Pages workflow: present
- Current JOURNEY LENS published set remains the default priority source after Iceland when country-page production starts

## Immediate priority

1. Finish Iceland as the reference country page using the newly locked ATLAS illustration direction.
2. Produce and lock the 5 top Hero visuals in the same JOURNEY ATLAS visual style.
3. Produce all 201 destination-card illustrations, in controlled batches with geographic and color-balance QA.
4. Lock the Iceland page structure as the reusable country-page template.
5. When the Hero set and 201-card visual system are stable, begin country-page production from the JOURNEY LENS published set.

## Top visual production sequence

### Phase A — Iceland benchmark

Finish Iceland first. The page already has its information architecture, map interaction and content structure; replace legacy visual assets with production illustrations and use the completed page as the reference for every later country page.

### Phase B — Hero benchmark

Create 5 real-place Hero visuals. These become the benchmark for light, editorial painting, crop quality and overall ATLAS identity.

### Phase C — destination cards

Produce 201 destination illustrations in batches. Every batch must preserve:

- regional variety;
- category variety;
- light / time-of-day variety;
- strong distinction between neighboring cards;
- real-place accuracy;
- consistent editorial painting language.

## First country-page production batch after Iceland

Use the JOURNEY LENS display order as the default sequence unless there is a clear visual/content reason to reorder:

1. Antarctica
2. Tajikistan
3. Kyrgyzstan
4. Uzbekistan
5. Kazakhstan

After that: India, Saudi Arabia, Oman, Cuba, Guatemala, Costa Rica, Bolivia, Argentina, Chile, Tanzania, Namibia, Lesotho, Australia.

## Visual rules already decided

- Adult visual travel atlas, not a conventional travel-information site.
- JOURNEY ATLAS must not feel like an illustrated version of JOURNEY LENS.
- JOURNEY LENS = photography, personal travel memory and narrative. JOURNEY ATLAS = illustrated world discovery, comparison and exploration.
- Destination illustration target is now approximately **photo 45 / illustration 55**: real-world plausibility remains essential, but the image should clearly read as an illustration at first glance.
- Every illustration is based on a real named landscape or place.
- Real geography, architecture, vegetation, coastlines, and landmark relationships take priority over decorative invention.
- Visible brushwork, simplified color planes and editorial composition should remain apparent; do not chase photographic micro-detail.
- Avoid stock-photo lighting, HDR, lens effects, excessive cinematic drama and travel-poster gloss.
- No landmark collage, no text, no flags, no UI, no watermark inside illustrations.
- One destination = one coherent real scene.
- Country maps may use illustration-only visual treatment while broadly preserving geography and place relationships.
- ATLAS copy is concise and atlas-like. It should help users discover where they may want to go, rather than reproduce the personal essay voice of JOURNEY LENS.
- JOURNEY ATLAS wordmark has no leading symbol.
- Related countries: small flag + English/Japanese country name + one short reason.
- Do not require a dedicated Hero/image asset for every related country before that country page exists.

## User decision gates

Ask the user only for decisions in these cases:

1. Changing the locked illustration style or overall visual identity.
2. Changing the 201-destination definition.
3. Changing top-level site structure or navigation.
4. Selecting between materially different Hero art directions after a benchmark is shown.
5. Legal / privacy wording that requires an owner decision.
6. A country-page template change that would propagate to all 201 destinations.

Routine scene selection, crop tuning, batching, filename conventions, accessibility fixes, responsive adjustments, metadata, QA and implementation should proceed without user approval.

## Release workflow

1. Implement safely on `main`.
2. Validate structured data.
3. GitHub Pages deploys from the configured workflow.
4. Review in browser when available.
5. Only stop for a material decision gate.

## Definition of done — top visual system

The top visual system is ready for country-page expansion when all of the following are true:

- 5 Hero visuals are production-ready and consistent;
- 201 destination-card illustrations exist and pass basic real-place / crop / style QA;
- cards remain readable on desktop and mobile;
- geographic and color variety across the set is acceptable;
- the ATLAS illustration identity is clearly distinct from JOURNEY LENS photography and does not invite a direct visual comparison with it.

## Definition of done — country page template

Iceland becomes the template when all of the following are true:

- Hero uses a real-place production illustration in the locked ATLAS style;
- 8 scene illustrations use the same style and represent real places;
- map markers and scene cards remain synchronized;
- navigation has no dead controls;
- responsive behavior is stable;
- wish-list behavior works;
- related-country section is usable even when related pages are not yet published;
- data validation passes.
