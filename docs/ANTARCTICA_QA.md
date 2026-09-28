# ANTARCTICA QA

Updated: 2026-08-23

## Implemented

- Country JSON registered as `antarctica`.
- 8 scenes implemented from the current JOURNEY LENS Antarctic stories.
- Hero uses Lemaire Channel as the real-place source scene.
- Illustrated Antarctic Peninsula route map added.
- Related destinations use small flags + country names + one-line reasons.
- No extra logo mark before `JOURNEY ATLAS`.
- Page renders through the shared `country.html` template.

## 8 scenes

1. Hydrurga Rocks
2. Portal Point
3. Flandres Bay
4. Lemaire Channel
5. Orcas
6. Neumayer Channel
7. Graham Passage
8. Palaver Point

## Visual QA direction

- Current SVG scene art is an integrated first-pass illustration set, not final production art.
- Final art must use the locked JOURNEY ATLAS style: **photo 60 / illustration 40**.
- Every scene must remain tied to a real place or verified voyage encounter; do not invent scenery for drama.
- Keep painterly simplification visible enough to distinguish ATLAS from JOURNEY LENS photography.
- Avoid both extremes: photoreal stock-photo look and obvious watercolor/gouache poster look.
- Avoid turning Antarctica into a monochrome blue-grey page. Use pale turquoise water, dark rock, snow white, soft sky blue and small restrained warm accents from wildlife/equipment.
- Wildlife remains part of the landscape rather than becoming character art.
- Lemaire Channel hero must stay luminous and spacious, not dark or threatening.

## Data QA

- [x] All 8 scene coordinates are inside the page map bounds.
- [x] No permanent capital, common official language or common currency is shown.
- [x] Permanent population is shown as zero; seasonal researchers are described separately.
- [x] Travel timing is expressed as Antarctic summer / winter rather than implying year-round general tourism.
- [ ] Orca scene final pin should be refined against voyage log / route record before publish.
- [ ] Final place-coordinate pass before `atlasPublished=true`.

## Remaining work without changing page structure

1. Replace first-pass SVG art with production painterly-realism assets.
2. Refine the illustrated Peninsula coastline and route shape against voyage geography where needed.
3. Review mobile cropping of Lemaire hero and map labels.
4. Verify final place coordinates.
5. Run shared country JSON validation.
6. Only then set `atlasPublished=true` and activate the top-page link.
