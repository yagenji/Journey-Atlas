# JOURNEY ATLAS — Design lock and branch discipline

Scope: This document retains **approved cross-site design decisions** and branch discipline. It is **not** an alternative Country production, image-generation, QA or publication protocol.

For a **new Country**, use `docs/COUNTRY_PRODUCTION_RULES.md` as the sole human production authority. Production progress is not stored in a GitHub State machine. For a published Country renewal, use `docs/PUBLISHED_COUNTRY_RENEWAL.md`. Do not read retired production protocols from Git history as startup guidance.

## Design lock

**Approved = locked.** Once the user approves a design, implementation reproduces it; do not reinterpret the motif, composition, crop, colors, labels, or interaction. Change a locked design only when the user requests it.

1. Create a wireframe/mockup only when layout or information architecture is unresolved; otherwise make the production asset directly. Do not design the same approved visual twice.
2. Confirm that approved, implementation-ready individual assets and the exact labels/copy exist before coding. A composite concept image is not a substitute for production assets.
3. Keep the source visual/specification, approved copy, asset list, and target component identifiable.
4. Make only neutral technical adjustments necessary for responsive behavior or accessibility. Do not replace artwork with easier-to-code symbols or introduce another visual direction.
5. Compare the implemented result with the approved design on the affected viewports, including crop, hierarchy, type, spacing and interaction; correct actual mismatches, not speculative redesigns. Country pages additionally follow the full Desktop/Tablet/Mobile and canonical-review gates in their own authority.

**Fast path:** need → production-ready visual → user approval → lock → implement the same asset → compare. Avoid concept → approval → new design → repeated reimplementation.

## Approved top page — LOCKED 2026-08-23

The top page is the production baseline; do not initiate another visual redesign cycle. Its section order is:

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
- `201の国・地域を、イラストとともに`
- `めぐる世界図鑑です。`

The 201-destination registry is present from the beginning, but all 201 final illustrations are **not** a top-page release blocker. The existing neutral fallback may be used until approved art replaces it. Top-page changes are limited to verified bugs, broken links/controls, accessibility, responsive defects and approved-art replacement unless the user requests a redesign.

## Approved theme section

Keep the illustrated eight-theme language and motifs; do not replace them with abstract symbols. `data/theme-taxonomy.json` remains the authority for Country assignments.

| Theme | Approved motif |
| --- | --- |
| 地球の風景 | Mountain / lake |
| 街を歩く | Town / architecture |
| 時をたどる | Ruins |
| 暮らしに出会う | Market |
| 野生に会う | Elephant / wildlife |
| 海の世界へ | Tropical island / sea |
| 食をめぐる | Food dish |
| 道の先へ | Mountain road |

## Approved map discovery baseline

Preserve the current map interaction and framing: **World → Region → optional Subregion → Country**. Country geometry is the primary spatial target; the right-side country list may support hover, selection and accessibility but must not replace the map as the core discovery experience. Do not create a second framing script; map framing belongs in `assets/js/map-regions.js` only.

## Country and image production — pointer only

- New Country production: `docs/COUNTRY_PRODUCTION_RULES.md`.
- Image quality: `docs/IMAGE_QUALITY.md`.
- Content quality: `docs/CONTENT_QUALITY.md`.
- Map quality: `docs/MAP_QUALITY.md`.
- GitHub stores finished Country assets and runs finish-line QA; it does not track generation history, approval ledgers or intermediate production State.
- Canonical unpublished review and formal publication remain distinct. Final publication requires explicit user approval.

Do **not** recreate State machines, per-image Git commits, provenance ledgers, or extra approval/verification PRs as a workaround for one-off failures.

## Branch lifecycle

- Use one working branch per active Country, plus a short-lived shared branch for a proven common-system fix where necessary.
- Do not create ad hoc Country-specific QA/deployment workflows or derivative branches merely to work around a problem. A normal new Country uses one review PR and, after final approval, one small publication PR.
- Preserve others' changes and approved assets. After merge and verification, retire obsolete work branches through the normal authorized GitHub process; retain unique history when necessary.
- `main` is the shared implementation baseline. Never treat a review deployment as formal publication or change an unapproved Country to `atlasPublished:true`.

## Published Country renewal

Already-published Country Pages use `docs/PUBLISHED_COUNTRY_RENEWAL.md`; status lives in `data/country-renewal-status.json`. Run the current renewal audit and image hard gate appropriate to that Country. A legacy published page does not meet the current production standard merely because it is live.

Iceland / Norway remain the visual-series references; Spain supplies the approved Taste-series reference and current shared page-structure comparison where applicable. `docs/IMAGE_QUALITY.md`, not legacy low-resolution assets, defines current production image quality.
