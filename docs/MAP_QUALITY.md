# JOURNEY ATLAS — MAP QUALITY

Country Map quality remains a hard product requirement, independent of production-state machinery.

## Visual system

Preserve the established Country Map language:
- 1200×760 canvas;
- common sea/land palette;
- common typography and marker language;
- target Country remains visually primary;
- real surrounding land is shown where geographically relevant;
- materially visible inland water uses the shared inland-water treatment rather than being filled as land.

## Geography

Required:
- verified administrative/national geometry;
- real coastlines/islands/exclaves;
- real Scene coordinates;
- no fictional land, coast, border, road, river or lake;
- major lakes and border lakes that are visibly meaningful at the product scale must remain water consistently across Country maps;
- tiny inland-water bodies that are not legible at 1200×760 do not need to be forced into the map;
- administrative borders crossing or adjoining lakes must remain visible above the water layer;
- map labels may move for collision avoidance, real coordinates may not;
- multi-region/inset layouts must preserve real region bounds and projection behavior.

Use verified inland-water geometry from the shared geographic source/tooling. Do not infer a lake from an administrative polygon hole alone, because holes can also represent enclaves or other non-water geometry.

Record the actual geometry/coast/water source and license when inland-water geometry is introduced or replaced.

### Boundary standard (Japanese map conventions)

JOURNEY ATLAS is a Japanese-language atlas. Territorial depiction follows the Government of Japan and Japanese school atlases, applied through `scripts/japan_boundary_standard.py`:

| Area | Depiction |
| --- | --- |
| Northern Territories (択捉島・国後島・色丹島・歯舞群島) | Japan; no border line between Hokkaido and Kunashiri |
| 竹島 | Japan |
| 尖閣諸島 | Japan |
| South Sakhalin (south of 50°N) and the Kuril Islands from Urup northward | 帰属未定: neither Japan nor Russia (neutral context land) |
| Kashmir and the China–India border | de facto control areas, with the disputed / line-of-control / indefinite segments dashed (国境未確定) |
| Crimea | Ukraine |
| Taiwan, Hong Kong, Macao, Kosovo | separate destinations (editorial division; see README) |

Natural Earth Admin-0 is de facto: use `japan_boundary_standard.py build-admin0` to derive the dataset for maps that include these areas, `patch-russia` / `clean-japan-context` / `dash-undetermined` for existing maps, and keep the top-page explorer data (`assets/maps/world-states.svg`) consistent.

### Inset notes

When a Country map uses a separate inset, explain it consistently on the Country page:
- detached territory shown at a non-geographic placement or different scale: `※ {地域名}は、実際の位置関係・縮尺と異なる別枠表示です。`
- a detail inset that enlarges the same geography: `※ {地域名}は、同じ地域を拡大した別枠表示です。`

Do not add directional wording such as “left/right”, or repeat implementation details that are already visible in the map.

## Construction

Use the shared map tooling where supported:
- `scripts/generate_country_map_with_context.py`;
- `scripts/add_country_map_context.py`;
- `scripts/normalize_country_map_lakes.py` for verified missing inland-water geometry on existing maps.
- `scripts/build_coastline_composite.py` when Natural Earth's coastline is visibly coarse at 1200×760 (long straight segments): keeps Natural Earth land borders and takes coast/islands from GSHHS `h`/`f`, then feed it to the generator with `--source natural-earth`;
- `scripts/generate_multi_region_map.py` for Country maps with `map.regions` (mainland + insets); the primary region continues past its rect so surrounding land never ends at a hard edge;
- `scripts/drop_domestic_context.py` to remove context rings that duplicate the target's own coast or islets.

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
- materially visible inland water, especially major lakes and border lakes;
- national-border visibility where a border crosses or follows inland water;
- marker-on-land placement;
- capital/marker label collisions;
- canvas-edge clipping.

Map QA returns PASS/FAIL only. It does not mutate production state.
