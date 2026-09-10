# JOURNEY ATLAS — Country Image Delivery Contract

Updated: 2026-09-11

This document is the canonical delivery-size and file-format contract for approved Country visual assets. It governs **delivery optimization only**; it does not authorize changing an approved image's place, viewpoint, composition, visual style, crop intent, or subject.

## Scope

Applies to reviewable and published Country Pages using `schemaVersion: 2`:

- Hero
- S01–S08 scenic images
- Taste images

It does **not** alter Country map SVGs or unrelated site assets.

## Delivery standard

### Hero

- direct WebP delivery;
- keep the approved aspect ratio;
- never upscale;
- cap width at 1536 px when that resize still satisfies the existing Hero minimum of 1200×760;
- if the approved source is already within the cap and is WebP, leave it byte-for-byte unchanged;
- use the static Country entry page to preload the Hero with high fetch priority.

Hero remains the highest-quality visual on the page. The 1536 px cap is a delivery ceiling, not a target that permits enlarging a smaller approved source.

### S01–S08 scenic images

For an approved 3:2 image that is at least 1200×800:

- final delivery geometry: exactly 1200×800;
- format: WebP;
- high-quality conversion;
- never replace the approved visual with a different image merely to satisfy the delivery contract.

### Taste

Taste uses the same delivery geometry and format as Scenes:

- exactly 1200×800;
- exact 3:2;
- WebP;
- approved visual content remains unchanged.

## Production command

After approved Hero / Scene / Taste assets have been placed in the Country production folder **and the Country JSON references them**, normalize delivery assets before final image QA:

```bash
python3 scripts/normalize_country_image_delivery.py --apply
```

The script:

- scans reviewable `schemaVersion: 2` Country JSON;
- converts only assets that exceed the delivery contract or use a non-WebP delivery format;
- updates only literal Country JSON image-path references when an extension changes;
- keeps every published destination registry `image` reference aligned with the corresponding Country `hero.image`;
- preserves Country JSON and registry formatting/order by using literal path replacement rather than reserialization;
- fully decodes every generated WebP before accepting it;
- leaves compliant WebP assets untouched;
- never processes map assets;
- never changes `atlasPublished` state.

Then run the normal image QA, including duplicate checks for the Country being produced.

## CI gate

The permanent CI gate is:

```bash
python3 scripts/normalize_country_image_delivery.py --audit
```

A reviewable Country may not proceed through the normal validation/deployment path while this audit reports an oversized eligible Hero/Scene/Taste asset, an eligible non-WebP delivery asset, or a published registry Hero reference that no longer matches the Country JSON.

This gate exists so future Country production does not reintroduce multi-megabyte PNG delivery, oversized Scene/Taste files, or stale published Hero references.

## Quality rule

File-size reduction is not a reason to lower visual quality below the Iceland / Norway benchmark. Delivery normalization must preserve the approved visual and use high-quality WebP encoding. If a source cannot be normalized without violating the existing Hero minimum or required Scene/Taste geometry, treat that as an asset-production issue rather than forcing a destructive conversion.
