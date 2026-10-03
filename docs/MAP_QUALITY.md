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
- multi-region/inset layouts must preserve real region bounds and projection behavior;
- material inland waters that are visible at the 1200×760 product scale must be rendered consistently from a verified water/coast dataset rather than inferred from arbitrary polygon holes or omitted per Country.

Record the actual geometry/coast/inland-water source and license.

### Inset notes

When a Country map uses a separate inset, explain it consistently on the Country page:
- detached territory shown at a non-geographic placement or different scale: `※ {地域名}は、実際の位置関係・縮尺と異なる別枠表示です。`
- a detail inset that enlarges the same geography: `※ {地域名}は、同じ地域を拡大した別枠表示です。`

Do not add directional wording such as “left/right”, or repeat implementation details that are already visible in the map.

## Construction

Use the shared map tooling where supported:
- `scripts/generate_country_map_with_context.py`;
- `scripts/add_country_map_context.py`;
- `scripts/normalize_map_inland_water.py` for shared inland-water normalization across existing canonical SVGs.

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
- major lakes and border lakes that are material at the rendered scale;
- surrounding land;
- marker-on-land placement;
- capital/marker label collisions;
- canvas-edge clipping.

Map QA returns PASS/FAIL only. It does not mutate production state.