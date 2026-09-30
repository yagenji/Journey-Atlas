# JOURNEY ATLAS — IMAGE QUALITY

This document defines what good Country imagery is. It does **not** define a production State machine.

## 1. Common rules

Every generated image is one independent visual target.

Required for every image:
- real identifiable place/dish;
- plausible geography, architecture, vegetation, season and light;
- single continuous frame;
- restrained natural color;
- no baked-in text or UI;
- no collage, grid, montage, inset or multi-panel;
- no invented landmark or impossible geography;
- no accidental reuse of another Country/Scene/Taste image.

Rejected candidates are simply regenerated. Rejection history is not stored in Git.

## 2. Hero / Scene visual style

Hero and Scene imagery must use one shared JOURNEY ATLAS style.

The shorthand `photo 6 : quiet watercolor 4` describes the balance of spatial realism to illustration. It does **not** permit a result that reads as a literal photograph.

The intended result is:
- photographic credibility in composition, perspective and real-world geography;
- clearly illustrated rendering at first glance;
- refined editorial travel illustration rather than stock photography;
- subtle watercolor transparency and tonal layering;
- smooth matte surface with almost no visible paper grain;
- softened micro-detail and simplified distant forms;
- restrained broad brush character mainly in sky, water and atmospheric distance;
- clear main silhouettes and landmark forms;
- natural low-to-medium saturation.

The governing principle is:

**Keep the place accurate; simplify the rendering.**

Do not make a scene less real by inventing or distorting geography. Reduce photographic surface detail instead.

### Photorealism ceiling

Hero / Scene images must not read as:
- photorealistic or hyperrealistic;
- DSLR / stock travel photography;
- glossy tourism advertising;
- HDR or cinematic concept art;
- 3D render / CG;
- over-sharpened generative-AI imagery.

Hard warning signs:
- leaf, skin, stone, fabric or building surfaces rendered with photographic micro-texture;
- strong lens bokeh, shallow depth of field or obvious lens flare;
- highly photographic reflections in water or glass;
- identical sharpness from foreground through distant background;
- excessive local contrast, clarity or HDR glow;
- dramatic commercial-lighting treatment that overwhelms the atlas tone.

### Positive rendering cues

At least several of these should remain visible in a good Hero / Scene image:
- slightly softened edges outside the key subject;
- reduced texture density in background and distance;
- broad tonal grouping instead of pixel-level surface detail;
- gently simplified cloud, water, vegetation and rock texture;
- subtle transparent color transitions associated with watercolor;
- controlled, quiet atmospheric depth;
- illustration-level visual organization that remains believable as a real place.

### Shared generation instruction

Use the following visual direction as the common style instruction for Hero / Scene generation. Country-specific prompts add only the real place, viewpoint, light/season, identifying features, composition and forbidden elements.

> A refined clean editorial watercolor travel illustration for an adult travel atlas. Accurate real-world geography, architecture, vegetation and natural lighting. Use photographic spatial credibility without photographic surface rendering. Preserve transparent luminosity and gentle watercolor tonal layering on a smooth matte surface with almost no visible paper grain. Soften micro-detail, simplify distant forms, and use subtle broad brush character mainly in sky, water and atmospheric distance. Keep key landforms, buildings, coastlines and silhouettes clear and recognizable. Clearly illustrated at first glance, not photorealistic, not hyperrealistic, not a photo filter, not stock photography, not hyper-detailed. Natural restrained color, low-to-medium saturation, one coherent real scene. No HDR, no strong lens effects, no shallow-depth-of-field glamour look, no over-sharpened AI micro-detail, no 3D render, no heavy gouache, no oil painting, no collage, no text, no flags, no logos, no watermark.

## 3. Style band / internal visual QA

Judge every Hero and Scene against the same style band before it reaches a user approval gate.

### PASS

- unmistakably a JOURNEY ATLAS illustration at first glance;
- real place remains credible and recognizable;
- photographic composition may be present, but photographic micro-detail is not;
- painterly simplification is visible without becoming loose or decorative;
- color and lighting remain natural and restrained.

### BORDERLINE

- first impression is ambiguous between photograph and illustration;
- painterly treatment becomes visible only on closer inspection;
- some surfaces or reflections are too photographically detailed;
- the image is otherwise geographically and compositionally correct.

A BORDERLINE Hero / Scene is **not** presented for approval. Regenerate that image with stronger simplification and lower photographic surface detail.

### FAIL

- reads as a photograph or AI-generated photograph;
- hyperrealistic / stock-photo / HDR / cinematic-advertising appearance;
- strong lens effects or photographic depth-of-field treatment;
- generated micro-detail dominates the image;
- style is obviously outside the shared JOURNEY ATLAS family.

Regenerate only that failed image.

## 4. Hero

The Hero is the highest-quality Country image:
- one real identifiable place;
- strong Country identity;
- horizontal composition;
- safe text/crop space;
- legible on mobile;
- PASS under the Hero / Scene style band.

Before requesting Hero approval, perform the internal style-band check. BORDERLINE or FAIL candidates are regenerated first.

One explicit user approval is required.

## 5. Scenes

Eight Scenes must explain the Country's geographic and visual breadth.

For each Scene define:
- exact place;
- viewpoint;
- season/light;
- 3–6 identifying visual features;
- 3:2 landscape composition;
- forbidden elements.

Generate S01→S08 independently.

Each Scene must PASS the Hero / Scene style band before the eight-image batch is presented. Do not ask for per-image approval. After all eight passing candidates are ready, present one batch review. Regenerate only rejected Scenes.

## 6. Taste

Taste follows the established Spain visual language. It is intentionally more food-photography-like than Hero / Scene imagery, but must remain quiet, restrained and consistent.

Required:
- one authentic recognizable dish only;
- complete dish/vessel visible;
- centered composition;
- pale beige/ivory matte tabletop/background;
- soft diffused daylight;
- consistent visual weight;
- restrained natural color;
- decorative props forbidden unless integral to the dish;
- no text, collage or multi-panel;
- 3:2 landscape composition.

Generate FOOD01→FOOD04 independently, then review all four once.

Do not apply the Hero / Scene photorealism ceiling mechanically to Taste. Taste is judged against the established Spain food-image language.

## 7. Final asset QA

The finished 13-image set must be checked for:
- file existence;
- complete raster decode;
- expected dimensions/aspect ratio;
- Country JSON references;
- duplicate/near-duplicate imagery;
- unreferenced production files;
- Hero / Scene consistency with the shared style band;
- visible drift toward photorealism, HDR, stock-photo or cinematic-advertising treatment;
- visual consistency across the nine Hero / Scene images without forcing identical composition or color.

Generation IDs, reservation epochs and approval ledgers are not quality requirements.
