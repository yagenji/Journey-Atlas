# JOURNEY ATLAS Roadmap

Updated: 2026-08-22

## Production rule

JOURNEY ATLAS country pages are created from countries/regions currently published in JOURNEY LENS first. The source of truth for the current publication state is `yagenji/Journey-Lens/content/top_countries.json`; entries with `show: true` are eligible for priority production.

The synchronized snapshot for ATLAS is `data/journey-lens-published.json`.

## Current state

- Iceland: implemented / review in progress
- Top page: implemented / review in progress
- GitHub Pages workflow: added; repository Pages must be enabled once in GitHub Settings before public preview works
- Current JOURNEY LENS published set: 19 countries/regions

## Next production batch

Use the JOURNEY LENS display order as the default sequence unless there is a clear visual/content reason to reorder:

1. Antarctica
2. Tajikistan
3. Kyrgyzstan
4. Uzbekistan
5. Kazakhstan

After that: India, Saudi Arabia, Oman, Cuba, Guatemala, Costa Rica, Bolivia, Argentina, Chile, Tanzania, Namibia, Lesotho, Australia.

## Visual rules already decided

- Adult visual travel atlas, not a conventional travel-information site
- Bright, beautiful watercolor/gouache illustration; the illustration should make the viewer want to go
- Real landscape identity remains recognizable, but illustration quality is more important than photographic imitation
- Country maps should use illustration-only possibilities while broadly preserving geography and place relationships
- JOURNEY ATLAS wordmark has no leading symbol
- Related countries: small flag + English/Japanese country name + one short reason
- Current Unicode symbols/icons are temporary and must not be treated as the final icon system
- Do not require a dedicated hero/photo asset for every related country before that country page exists

## Release workflow

1. Implement safely on `main`
2. Validate country JSON
3. GitHub Pages automatically deploys after Pages is enabled
4. Review in browser without local terminal
5. Only stop for material design/content decisions
