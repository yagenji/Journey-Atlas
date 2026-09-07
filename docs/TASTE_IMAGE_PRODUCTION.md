# JOURNEY ATLAS — Taste Image Production Hard Rule

Updated: 2026-09-08

This file is the Single Source of Truth for Country-page Taste image generation.

## Purpose

Taste images are not food photography scenes, restaurant-table scenes, lifestyle still lifes, or multi-dish layouts.

They are **single-dish atlas cuts** whose job is to let the viewer recognize one representative food immediately.

## Non-negotiable generation unit

- **1 image = 1 dish only.**
- **1 generation request = 1 dish only.**
- Never ask the image generator to place FOOD01–FOOD04, multiple dishes, multiple plates, or multiple panels in one image.
- “Generate all four Taste images in one batch” means: generate four independent images consecutively without waiting for user approval between them.
- It never means one four-dish image, a 2×2 grid, split screen, montage, diptych, triptych, contact sheet, comparison plate, or collage.
- If a tool call can return multiple candidates, every candidate must still depict the same single dish. Do not use one call to request different dishes.

## Composition lock

Every Taste image must use the Spain Taste visual language:

- final target: 1200×800
- exact 3:2
- one clearly recognizable dish
- one simple plate, bowl, cup, or serving vessel only when appropriate to that dish
- dish is the dominant subject and occupies the visual center
- restrained photo 6 : quiet watercolor 4 treatment
- natural, appetizing, realistic food structure
- clean pale beige / warm ivory / very light neutral background
- background should read as a quiet plain surface, not a location
- no text, labels, flags, logos, packaging, watermarks, frames, or UI

## Background hard rule

The background must remain visually empty.

Do **not** add decorative or contextual props unless they are literally part of the dish itself.

Explicitly prohibited in the background or around the dish:

- extra plates or bowls
- second dishes, side dishes, tasting portions
- cutlery
- chopsticks
- napkins or tablecloth styling
- cups, glasses, bottles, carafes
- condiments or sauce dishes
- loose herbs placed for styling
- raw ingredients
- fruit or vegetables used as props
- bread baskets
- flowers, candles, books, menus
- cookware, pans, pots, boards
- hands or people
- restaurant interiors
- kitchen interiors
- windows, streets, scenery, landscapes
- shelves, counters, decorative objects
- national motifs or souvenirs
- depth-of-field restaurant backgrounds
- shadows or reflections that imply unrelated objects outside the frame

A small garnish is allowed only when it is a normal, integral part of the dish and remains **on the same plate/bowl**. Do not invent garnish for visual interest.

## Dish identity rule

Before generation, define the dish identity in concrete visual terms:

- vessel
- main shape / silhouette
- key ingredients visible from the chosen angle
- texture
- surface color
- traditional arrangement
- any truly integral accompaniment

Do not compensate for weak dish identity by adding props or scenery.

If the dish cannot be recognized without explanatory background objects, improve the dish depiction itself.

## Generation-state rule

For four Taste items:

1. FOOD01 independent generation
2. FOOD02 independent generation
3. FOOD03 independent generation
4. FOOD04 independent generation
5. batch review after all four are complete
6. regenerate only the user-specified NG item(s)

APPROVED Taste images are immutable unless the user explicitly asks for regeneration.

Do not edit the previous dish image into the next dish image. Each dish starts from an independent generation state.

## Hard reject conditions

Reject and regenerate the affected dish if any of the following appears:

- collage / multi-panel / grid
- more than one dish
- more than one meaningful serving vessel
- unrelated food or side dish
- decorative background props
- restaurant / kitchen / lifestyle background
- ingredients scattered around the plate
- cutlery / napkin / glass / bottle added for styling
- text / logo / flag / packaging
- dish is too small because background dominates
- wrong food structure or unrecognizable dish
- photographic style is materially stronger than the JOURNEY ATLAS Taste reference
- watercolor is materially stronger than the Spain Taste reference
- low resolution, decode failure, wrong aspect ratio, or other technical failure

A rejected image must never be moved into the approved production folder.

## Prompt minimum

Every Taste generation prompt must explicitly state all of the following:

- ONE specific named dish only
- single independent image
- no collage / no multi-panel / no grid
- one plate/bowl/vessel only
- plain pale beige or warm ivory background
- no props, no cutlery, no napkin, no drink, no ingredients around the dish
- no restaurant or kitchen background
- no people or hands
- no text / logo / flag / packaging
- Spain Taste visual language
- photo 6 : quiet watercolor 4
- exact 3:2 composition

The specific dish identity is then added after these fixed constraints.
