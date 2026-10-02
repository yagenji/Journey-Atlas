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

### Generation contract — mandatory on every image call

Keep this contract short and repeat it on every Hero / Scene / Taste generation:

**ONE GENERATION = ONE TARGET = ONE IMAGE.**

- one standalone full-bleed frame only;
- never request or produce a collage, grid, contact sheet, split panel, inset, comparison layout or multiple variants inside one image;
- never include another Scene / FOOD target in the same generation prompt;
- never use, edit, vary, restage, crop or reference a previous generated image for a different target;
- each target starts from its own standalone text instruction.

If a result is a collage, wrong target, or the same / near-same visual as an earlier current-Country image, reject only that result and regenerate only that target with a fresh standalone prompt. Do not create State, ledger, reservation, reset workflow or extra user approval for this recovery.

## 2. Hero / Scene visual style

Hero and Scene imagery must use one shared JOURNEY ATLAS style.

The target is **photo 6 : quiet watercolor 4 in the visible result**.

Interpret the ratio as:
- **photo 6** = realistic composition, perspective, geography, architecture, scale, light and believable spatial depth;
- **watercolor 4** = clearly visible watercolor rendering across the image surface, not a barely perceptible filter.

The image should first feel like a credible real travel scene, while still being visibly painted. A viewer should not need to zoom in to notice the watercolor treatment.

The intended result is:
- photographic credibility in composition, perspective and real-world geography;
- clearly visible watercolor rendering across sky, water, vegetation, rock, architecture and atmospheric distance where appropriate;
- refined editorial travel illustration rather than stock photography;
- transparent watercolor tonal layering and gentle pigment variation that are visible at normal viewing size;
- smooth matte surface with almost no visible paper grain;
- softened micro-detail and simplified distant forms;
- controlled brush character without becoming a loose painting;
- clear main silhouettes and landmark forms;
- natural low-to-medium saturation.

Do **not** solve photographic drift by reducing geographic realism. Keep the real place accurate and increase visible watercolor rendering instead.

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

> ONE GENERATION = ONE TARGET = ONE IMAGE. ONE SINGLE FULL-BLEED FRAME. ONE CONTINUOUS REAL VIEW. Create a refined adult travel-atlas image with a visible balance of photo 6 : quiet watercolor 4. Keep composition, perspective, geography, architecture, vegetation, scale and natural light photographically credible. Render the image surface with clearly visible but controlled watercolor treatment: transparent tonal layering, softened micro-detail, simplified distant forms and gentle pigment transitions that remain visible at normal viewing size. The result must not read as a literal photograph or stock travel photo, and must not become a loose or decorative painting. Natural restrained color, low-to-medium saturation. No collage, grid, split panel, contact sheet, inset, comparison layout, multiple variants, text, flags, logos or watermark. Do not reuse, edit, restage, crop, vary or reference any previous generated image.

## 3. Style band / internal visual QA

Judge every Hero and Scene against the same style band before it reaches a user approval gate.

### PASS

- reads as a believable real travel scene with an obvious **photo 6 : watercolor 4** balance;
- watercolor rendering is visible immediately at normal viewing size, not only on close inspection;
- real place remains credible and recognizable;
- photographic composition and depth remain, but photographic micro-detail does not dominate;
- painterly simplification is controlled rather than loose or decorative;
- color and lighting remain natural and restrained.

### BORDERLINE

- first impression is essentially a photograph with only a light watercolor filter;
- watercolor treatment becomes clear only on closer inspection;
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

Generate S01→S08 independently: **one target, one image call, one output**. The current Scene prompt must not list the other Scene names/IDs or refer to any previous generated image.

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

Generate FOOD01→FOOD04 independently: **one named dish, one image call, one output**. The current FOOD prompt must not list the other dishes or refer to any previous generated image. Then review all four once.

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
