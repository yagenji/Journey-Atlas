# JOURNEY ATLAS — Hero / Scene image production

Updated: 2026-09-17. This is a **visual-generation guide**, not a second copy of the image State machine. For reservation, renderPacket fields, approval provenance, contamination/reset and round transitions, follow the **current main** `ops/image-generation-policy.json`, `ops/country-production-policy.json`, and `scripts/country_production_protocol_v2.py next {slug}`. They take precedence over any older examples.

## One image, one real place

- Hero and S01–S08 are **independent** images. Each generation call receives only the current target's real place, viewpoint, distinguishing geography/architecture, season/light and composition from its validated Render Packet.
- One full-bleed horizontal 3:2 frame, one continuous view, natural restrained colors, recognizable real geography and built features, photo 6 : quiet watercolor 4, Iceland/Norway visual language.
- Never ask one image call for a Scene set, collage, split panels, poster, typography, map or UI. Do not use an earlier image as the next generation's input or reference.
- A Scene batch means **separate image calls followed by one user review**, not one combined image or approval after each Scene. Preserve previously APPROVED assets.

## Mandatory Scene-generation instruction

Build the prompt from the **current** Render Packet only. Keep its location-specific identity precise. Append the following negative block; do not replace it with a vague “no text”:

```text
ONE SINGLE FULL-BLEED 3:2 LANDSCAPE FRAME. ONE PLACE. ONE CONTINUOUS CAMERA VIEW.
PURE SCENIC IMAGE ONLY.
No added text anywhere in the image.
No title, place name, country name, caption, letters, typography, labels, badges, logo, flag, map, UI, infographic, poster layout, border, frame, collage, grid, split panel, contact sheet, or decorative wording.
Do not invent readable signage. If real-world signage is unavoidable, keep it incidental, small, subordinate, and not legible as generated text.
Generate only the specified real place and viewpoint. Do not reuse, restage, crop, or vary any previous Hero or Scene. Do not substitute another landmark.
Single standalone landscape image only.
```

Do not list other Scene IDs or names, the complete batch, previous failed images or review layouts in the image-generation instruction.

## Quality check and execution

Before using an image credit, confirm the exact NEXT target and complete Render Packet; the machine policy controls reservation and the authoritative State. Reuse unchanged in-turn State and packet data where current policy allows instead of repeatedly rereading all documents.

After each generation check real-place identity, plausible geography/architecture, required season/light, 3:2 composition and crop, no text/collage/UI, restrained watercolor style, and novelty against **all** prior Country Hero/Scene images. Incorrect, duplicated, collaged or other failed output is rejected, not handed to the user as an approved asset. Reconcile the generation and follow the current contamination/reset/retry policy; never skip the required no-image reset when it applies.

Continue valid S01–S08 generations without requesting per-image user input. At the batch boundary present the separate candidates for one review; regenerate only rejected targets. After approved files are stored, run the current complete-decode/dimensions and machine duplicate gates (`scripts/validate_images.py --duplicates-only --slug {slug}`), then verify the actual Country page. CI PASS alone does not establish visual quality.
