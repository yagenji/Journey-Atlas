> **STATUS — COMPLETED (2026-09-05)**  
> This file is retained as a historical execution/plan record. The current authoritative renewal status is `data/country-renewal-status.json`: content / visual / map / sources = `DONE`, QA = `PASS`, production = `LIVE_CURRENT`. Any `PENDING`, `Still pending`, or pre-publish notes below describe an earlier checkpoint and are not current tasks.

# Norway — Published Country Renewal Audit

Date: 2026-09-03  
Wave: 1 / Reference v3  
Classification: **C — rebuild-level renewal**

## Decision summary

- Hero concept: **KEEP / REBUILD asset**
- 8-scene selection: **BROADLY KEEP**
- Scene production assets: **REBUILD 8**
- Map: **KEEP**
- Country Profile: **KEEP**
- Signature Facts: **REWRITE 1**
- Encounters: **KEEP**
- Beyond the Scenery: **REWRITE 1 when Taste is added**
- Travel Trivia: **KEEP / source-check**
- Taste: **ADD**
- Travel Scale: **ADD**
- Themes: **KEEP pending final country review**
- Sources: **CURRENT BASE + ADD sources for new sections**
- Hard image gate: **OFF until renewal is complete**

## Visual audit

### Hero
Geirangerfjord remains a strong Norway entrance and should not be replaced merely because the file is old. The current file is 960×540, below the renewed Hero minimum. Rebuild the asset at current production quality while preserving the approved visual direction unless the later candidate review finds a materially better Hero.

### 8 scenes
Current set is editorially broad:
- Nærøyfjord
- Preikestolen
- Trolltunga
- Bryggen
- Atlantic Road
- Vøringsfossen
- Reine
- North Cape

It already mixes fjord, mountain, hike, urban/history, road, waterfall, fishing village and far-north landscape. Keep the selection as the default; only change a Scene if the 12–16 candidate review demonstrates a stronger discovery.

### Asset gate
All nine key visual files fully decode, but the current files are legacy-resolution:
- Hero: 960×540
- Scenes: 320–360×240–270
- all Scene rasters are 4:3

All eight Scene assets require renewed production files.

## Content audit

Norway is missing the current shared content additions:
- `contentQaVersion`
- `taste`
- `travelScale`

Signature Facts:
- Coastline 100,000 km+: keep candidate
- Hydropower about 90%: keep candidate
- Built-up / constructed land 1.8%: **replace** — factually descriptive but weak as a travel-curiosity number

The FOOD Beyond topic will overlap the new dedicated Taste section and should be replaced with a different Norway-specific layer.

Encounters are already concise eight-tag content and can remain.

## Map

Technical map validation passes. Keep unless visual QA during implementation finds a specific issue.

## Why C

The editorial structure and current Scene choices are not a total redesign, but every major visual asset must be rebuilt to current production quality. That makes the renewal visual workload rebuild-level even if many content decisions can be retained.
