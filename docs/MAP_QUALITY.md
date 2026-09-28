# JOURNEY ATLAS — MAP QUALITY

Country Map quality remains a hard product requirement, independent of production-state machinery.

## Visual system

Preserve the established Country Map language:
- 1200×760 canvas;
- common sea/land palette;
- common typography and marker language;
- target Country remains visually primary;
- real surrounding land is shown where geographically relevant.

## Geography

Required:
- verified administrative/national geometry;
- real coastlines/islands/exclaves;
- real Scene coordinates;
- no fictional land, coast, border, road or river;
- map labels may move for collision avoidance, real coordinates may not;
- multi-region/inset layouts must preserve real region bounds and projection behavior.

Record the actual geometry/coast source and license.

## Construction

Use the shared map tooling where supported:
- `scripts/generate_country_map_with_context.py`;
- `scripts/add_country_map_context.py`.

Do not create Country-specific geometry shortcuts merely to pass QA.

## Finish-line QA

For a new Country run:

```bash
python3 scripts/validate_country_map_v6.py data/countries/{slug}.json
python3 scripts/validate_country_quality_v5.py data/countries/{slug}.json
```

Also inspect the rendered 1200×760 SVG visually for:
- coastline alignment;
- islands/exclaves;
- surrounding land;
- marker-on-land placement;
- capital/marker label collisions;
- canvas-edge clipping.

Map QA returns PASS/FAIL only. It does not mutate production state.
