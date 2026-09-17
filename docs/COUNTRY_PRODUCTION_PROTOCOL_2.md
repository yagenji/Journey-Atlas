# JOURNEY ATLAS — Country Production Protocol 2.0

Updated: 2026-09-17. This document is the **short operational guide**, not a parallel machine policy.

## Authority and compatibility

- PROJECT MASTER INSTRUCTIONS preserve the project purpose, visual language, map quality, common UI, review and publication approval.
- `ops/country-production-policy.json` is the new-Country lifecycle and interaction authority; `ops/image-generation-policy.json` is the image-generation authority. Read the current files on `main` rather than copying their version numbers or every rule into prompts.
- `docs/CONTENT_QUALITY_RULES_V6.md` and `docs/MAP_SYSTEM.md` define editorial/map quality; `docs/PUBLICATION_PIPELINE_V2.md` and `docs/CANONICAL_UNPUBLISHED_REVIEW.md` define the **current** review and publication sequence. Where older descriptions of one reusable PR or Pages-only review conflict, the canonical-review amendment and current machine policy prevail.
- New Countries use Protocol 2, Content QA v6 and Publication Pipeline v2. Existing in-flight legacy Countries retain their recorded contracts unless a migration is explicitly reviewed.

## Production sequence

```text
Check latest main + existing Country State
→ complete editorial content, sources, coordinates and Map QA
→ validate Content / preVisualBuild
→ Hero generation + individual approval
→ eight independent Scene generations + one batch approval
→ four independent Taste generations + one batch approval
→ hand off all 13 approved raster images once; verify complete decode and paths once
→ target-only checks and staging Pages QA
→ integrate still-unpublished Country on latest main; verify canonical URL live
→ user final page approval on canonical URL
→ separate formal publication integration; verify deployed SHA and live route
```

The sequence does not create new user gates: Hero, Scene Batch, Taste Batch and final canonical Country page are the editorial approval points; the user must additionally store approved raster assets at the required handoff. Never equate a queued workflow, successful CI, or file existence with a completed visual or production QA.

## Content and image work

1. Check existing `data/countries/{slug}.json`, `ops/country-production/{slug}.json` and Country branch before initializing. For a truly new Country, use `python3 scripts/country_production_protocol_v2.py init {slug}` on its Country branch.
2. Before Hero, complete all non-raster editorial content, sources/source dates, approved Map, real coordinates, taxonomy, routes, related destinations and image paths. Run the current editorial and Country quality validators required by the policy. The machine-readable `preVisualBuild` gate decides readiness.
3. Follow `python3 scripts/country_production_protocol_v2.py next {slug}` and its `interaction.userGate`. Continue deterministic next actions without asking the user to type `next` or approve each individual Scene/Taste. A tool or turn boundary is not an approval gate.
4. Generate **one target and one image per independent call**. Use only the current target's location/identity/composition in the image prompt; do not send this protocol or all other Scene names to image generation. Keep valid approved outputs; reject wrong-target, repeated, collage or otherwise failed outputs according to the current image policy. Do not retry a failed Taste target before completing the initial batch.
5. After the Hero, eight Scenes and four Taste images have user approval, run `python3 scripts/country_production_protocol_v2.py handoff {slug}`. User handoff is one batch; assistant-side raster materialization is not the standard route. Verify the 13 repository assets' identity, complete decoding, size and final paths before downstream integration.

## Review and publication — canonical production URL

1. For a Country-only change, use targeted validation, image QA and Desktop / Tablet / Mobile Browser QA. A shared template/CSS/JS/build change requires broader regression. Do not repeatedly validate unrelated Countries for an unchanged Country-only build.
2. Pipeline v2 creates a staging review PR and deploys a persistent GitHub Pages preview for technical QA. Pages is **not** the user's final Country review URL. Build review candidates from latest `main` plus the target Country overlay; do not merge main into a long-running Country branch merely to synchronize it.
3. After staging QA passes, the review PR is integrated while `atlasPublished:false`. Verify the exact Cloudflare SHA and `https://atlas.yagenji.com/countries/{slug}/` live on Desktop / Tablet / Mobile. The page must remain `noindex,follow`, unlinked from regular discovery, and absent from the sitemap. Only then offer the canonical URL for user review.
4. User final approval permits a **separate publication PR** after the unpublished review PR was merged. Publication uses latest-main overlay, sets `atlasPublished:true` only after authorization, runs publish checks on the terminal SHA, integrates through the serialized queue, and verifies the Cloudflare deployed SHA, URL and published discovery/sitemap state. Do not create a separate production-verification PR.
5. Country fixes during review must preserve approved images unless the user expressly requests their replacement or a blocking quality defect is found. Revalidate affected content and the actual canonical page before final approval.

The authoritative Production State records actual completed work. Preserve the publication queue and legacy compatibility; do not convert an operational failure into a workaround for a single Country.
