# JOURNEY ATLAS — Design & Implementation Workflow

## Purpose
Reduce rework. Once a design is approved, implementation must reproduce that approved design rather than reinterpret it.

## Core rule
**Approved = locked.**

After the user approves a design, do not change its visual direction, motif, composition, crop, color balance, or interaction model during implementation unless the user explicitly asks for a change.

---

## Standard process

### 1. Decide whether a mockup is actually needed
Use the cheapest artifact that can answer the current question.

- Layout / information architecture uncertain → create a simple wireframe or UI mockup.
- Visual asset itself is needed → create the production asset directly.
- Existing approved design already answers the question → do not create another concept.

**Avoid:** creating a polished composite mockup and then separately redesigning the same visual again for implementation.

### 2. Create implementation-ready assets
Before coding, confirm that every approved visual needed by the component exists in a form that can actually be used in the site.

For illustration/icon work:
- create individual assets, not only one combined presentation sheet;
- keep one master visual style;
- use consistent framing, crop, background treatment, and dimensions;
- name files by final theme / component id.

If the approved design exists only inside a composite mockup, derive/crop/export the required assets first. Do not reinterpret them in code.

### 3. Design lock
When the user says OK / good / use this / implement this, record the design as locked.

A locked component has four items:
1. source-of-truth visual or specification;
2. exact labels/copy;
3. exact asset list;
4. target page/component.

From this point, implementation is reproduction, not design exploration.

### 4. Implement without redesign
Implementation may change only what is technically necessary for responsive behavior or accessibility.

Allowed:
- responsive resizing;
- spacing adjustments required by viewport size;
- semantic HTML / accessibility labels;
- file optimization that does not visibly alter the asset.

Not allowed without user instruction:
- changing motifs;
- replacing illustrations with symbols;
- changing card proportions or visual hierarchy;
- changing colors because they are easier to code;
- generating a new stylistic version during implementation.

### 5. Compare once, then ship
After implementation, compare the result against the locked design on the main desktop view and one mobile view.

Check only:
- visual hierarchy;
- asset identity/crop;
- typography scale;
- spacing;
- intended interaction.

If they match, finish. Do not start another design iteration automatically.

---

## Fast path for JOURNEY ATLAS

For future visual components, use this sequence:

**Need → production-ready visual → user approval → lock → implement same asset → one comparison**

Not:

**Need → concept image → user approval → new implementation design → correction → reimplementation**

---

## Current application

### Top page — LOCKED 2026-08-23
The top page is now the production baseline. Do not start another visual redesign cycle.

Locked order:
1. Header
2. Hero
3. Three discovery entrances
4. Country search
5. Map search
6. Theme search
7. JOURNEY LENS
8. About
9. Footer

Locked Hero copy:
- `次に行きたい世界を、`
- `見つける。`
- `まだ知らない景色、心に残る出会い。`
- `文化や人々の暮らし。`
- `199の国・地域を、イラストとともに`
- `めぐる世界図鑑です。`

The 199 destination registry is part of the top page from the beginning, but completion of 199 final illustrations is **not** a release blocker for the top page. Missing destination art may use the existing neutral fallback and be replaced progressively as approved illustrations are completed.

From this point, top-page work is limited to:
- clear bugs;
- broken links or controls;
- accessibility fixes;
- responsive defects;
- replacement of fallback art with approved production art.

### Theme section
The approved visual direction is the illustrated eight-theme set:
- 地球の風景
- 街を歩く
- 時をたどる
- 暮らしに出会う
- 野生に会う
- 海の世界へ
- 食をめぐる
- 道の先へ

The approved motifs are:
- mountain/lake;
- town/architecture;
- ruins;
- market;
- elephant/wildlife;
- tropical island/sea;
- food dish;
- mountain road.

Implementation must use these motifs and the same illustrated/editorial visual language rather than replacing them with abstract symbols.

### Map section — LOCKED BASELINE
Use the current production interaction and framing as the baseline. Future changes must be bug fixes or explicit user requests.

Interaction hierarchy:
**World → Region → optional Subregion → Country**

Country geometry remains the primary spatial target. The right-side country list may support hover/selection and accessibility, but must not replace the map itself as the core discovery experience.

Do not reintroduce a second framing script. Map framing belongs in `assets/js/map-regions.js` only.

### Country / destination illustrations — LOCKED STYLE
JOURNEY ATLAS artwork must be visibly different from JOURNEY LENS photography.

Production target:
- approximately **photo 60 / illustration 40**;
- real, named landscapes or places;
- real geography / architecture / vegetation relationships;
- painterly simplification that is clearly visible on inspection;
- no photoreal stock-photo look;
- no watercolor wash or child-oriented picture-book look;
- no landmark collage;
- no text, flags, labels, frames, UI, or watermarks inside the image.

One destination = one coherent real-world scene for country-card artwork.

Country-page scene artwork follows the same visual language. A country page may contain multiple scene illustrations, but every individual scene must still represent one real place rather than a synthetic collage.

---

## Branch lifecycle

Keep the repository branch list intentionally small.

- Use **one working branch per active country**.
- Continue review fixes, QA fixes, and publish preparation on that same country branch.
- Do not create derivative branches such as `*-review-fix`, `*-publish`, `publish-*`, or `qa-*`.
- Shared fixes may use one clearly named common branch only while the work is active.
- After the work is merged into `main` and no further country-specific work remains, delete the working branch.
- If an old branch contains unique history that should be preserved, create an archive tag first, then delete the branch.
- Deployment and validation must use the shared workflows on `main`; do not add country-specific deployment or QA workflows.
- Normal steady state should be: `main` + only currently active country/common work branches.


## Decision rule
If implementation requires a visual choice that was not decided in the approved design:
- make the smallest neutral technical choice if it does not alter the design;
- if it would visibly alter the design, resolve that one point before coding;
- do not create an unsolicited alternative design.
