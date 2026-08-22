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

### Map section
Before implementation, first create the actual map asset/UI specification that will be used in production. Once approved, implement that same map structure: **World → Region → Country**.

---

## Decision rule
If implementation requires a visual choice that was not decided in the approved design:
- make the smallest neutral technical choice if it does not alter the design;
- if it would visibly alter the design, resolve that one point before coding;
- do not create an unsolicited alternative design.
