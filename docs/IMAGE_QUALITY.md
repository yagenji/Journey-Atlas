# JOURNEY ATLAS — IMAGE QUALITY

This document defines what good Country imagery is. It does **not** define a production State machine.

## Common rules

Every generated image is one independent visual target.

Required:
- real identifiable place/dish;
- plausible geography, architecture, vegetation, season and light;
- single continuous frame;
- restrained natural color;
- roughly photo 6 : quiet watercolor 4;
- no baked-in text or UI;
- no collage, grid, montage, inset or multi-panel;
- no invented landmark or impossible geography;
- no accidental reuse of another Country/Scene/Taste image.

Rejected candidates are simply regenerated. Rejection history is not stored in Git.

## Hero

The Hero is the highest-quality Country image:
- one real place;
- strong Country identity;
- horizontal composition;
- safe text/crop space;
- legible on mobile.

One explicit user approval is required.

## Scenes

Eight Scenes must explain the Country's geographic and visual breadth.

For each Scene define:
- exact place;
- viewpoint;
- season/light;
- 3–6 identifying visual features;
- 3:2 landscape composition.

Generate S01→S08 independently, then review all eight once. Regenerate only rejected Scenes.

## Taste

Taste follows the established Spain visual language:
- one authentic dish only;
- complete dish/vessel visible;
- centered composition;
- pale beige/ivory matte tabletop/background;
- soft diffused daylight;
- consistent visual weight;
- decorative props forbidden unless integral to the dish;
- 3:2 landscape composition.

Generate FOOD01→FOOD04 independently, then review all four once.

## Final asset QA

The repository checks the finished 13-image set for:
- file existence;
- complete raster decode;
- expected dimensions/aspect ratio;
- Country JSON references;
- duplicate/near-duplicate imagery;
- unreferenced production files.

Generation IDs, reservation epochs and approval ledgers are not quality requirements.
