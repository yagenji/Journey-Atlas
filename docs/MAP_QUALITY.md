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
| Crimea | Ukraine; the de facto Crimea line is not drawn (Natural Earth `FCLASS_JP` "Claim boundary") |
| Golan Heights | Syria (occupied by Israel): the Israel–Syria border west of the Golan follows Natural Earth's Japan point of view; the 1974 ceasefire line is dashed |
| Taiwan, Hong Kong, Macao, Kosovo | separate destinations (editorial division; see README) |
| Western Sahara | neither Morocco nor independent (Japan recognises neither the annexation nor the SADR): neutral context land; its northern boundary at 27°40'N dashed; the Moroccan berm is not drawn |
| Somaliland | part of Somalia (not recognised by Japan): no Somaliland-Somalia line |
| Hala'ib, Abyei, Ilemi, Ethiopia-Somalia, Ethiopia-South Sudan, Lake Malawi, Morocco-Algeria (indefinite segment) | de facto geometry, boundary dashed (国境未確定) where Natural Earth's Japan point of view (`FCLASS_JP`) classes it disputed / indefinite |

Natural Earth Admin-0 is de facto: use `japan_boundary_standard.py build-admin0 --disputed-areas ne_10m_admin_0_disputed_areas.geojson` (Crimea and the Golan Heights are reassigned from the de facto country) to derive the dataset for maps that include these areas, `patch-russia` / `clean-japan-context` / `dash-undetermined` for existing maps, and keep the top-page explorer data (`assets/maps/world-states.svg`) consistent. Border linework comes from `build-boundary-lines` (Natural Earth land boundary lines plus the disputed-area lines Japan's point of view shows, e.g. 27°40'N); lines Japan does not recognise are excluded by `is_excluded_boundary_line`.

### Shared styling

- target land: `url(#land)` gradient, outline `#31576a` 1.5px, `url(#shadow)` drop shadow (a transformed path gets the shadow on a wrapper group);
- inland water: `#e5eceb` fill, `#6f8a92` stroke at opacity .35 / width .65;
- inset and region frames: `fill="none" stroke="#879b9b" stroke-width="1.5" stroke-dasharray="5 5"`;
- surrounding land: one `#e4e0ce` silhouette outlined `#b6bbaf` 1; foreign borders come only from `#context-national-borders` (`#b6bbaf` 1), never from per-country context polygon edges, which would draw each border twice;
- inland water sits above the target fill and below `#context-national-borders` and the target outline, so borders crossing or following lakes stay visible (`normalize_country_map_lakes.raise_borders_above_water`). The lifted border layer is clipped to everything outside the target (`#map-borders-target-negative`), so lines inside the country (leased areas such as Baikonur, lines slightly off the target edge) stay hidden as they were below the fill. This applies to every single-frame map in all regions;
- widths are in viewBox units *after* transforms, because the map is displayed scaled down as an `<img>`: never use `vector-effect="non-scaling-stroke"` (it renders about twice as thick as other maps), and divide the declared width by any scaling transform. `tests/test_map_stroke_widths.py` checks this.

### Inset notes

When a Country map uses a separate inset, explain it consistently on the Country page:
- detached territory shown at a non-geographic placement or different scale: `※ {地域名}は、実際の位置関係・縮尺と異なる別枠表示です。`
- a detail inset that enlarges the same geography: `※ {地域名}は、同じ地域を拡大した別枠表示です。`

Do not add directional wording such as “left/right”, or repeat implementation details that are already visible in the map.

## Construction

Use the shared map tooling where supported:
- `scripts/generate_country_map_with_context.py`;
- `scripts/add_country_map_context.py`;
- `scripts/normalize_country_map_lakes.py` for verified missing inland-water geometry on existing maps (`--include-context` also adds major border and neighbouring lakes, `--augment` adds still-missing lakes beside an existing layer, `--restore-islands` keeps islands inside lakes as land);
- `scripts/build_coastline_composite.py` when Natural Earth's coastline is visibly coarse at 1200×760 (long straight segments): keeps Natural Earth land borders and takes coast/islands from GSHHS `h`/`f`, then feed it to the generator with `--source natural-earth` (`--island-distance` also takes offshore islands whose nearest country is the target);
- `scripts/generate_multi_region_map.py` for Country maps with `map.regions` (mainland + insets); the primary region continues past its rect so surrounding land never ends at a hard edge;
- `scripts/drop_domestic_context.py` to remove context rings that duplicate the target's own coast or islets.
- `scripts/normalize_map_stroke_widths.py` to remove `non-scaling-stroke` and compensate widths/shadow under scaling transforms (anisotropic transforms are baked into the path data);
- `scripts/dissolve_context_land.py` to merge per-country context polygons into one silhouette so foreign borders are not doubled;
- `scripts/update_stale_lake.py` when GSHHS still carries a lake at its historic extent (e.g. the Aral Sea): replaces it with the current Natural Earth 1:10m lake outline;
- a drained reservoir (the Kakhovka Reservoir since June 2023) is not drawn as water: keep its footprint as an invisible `data-map-dried-lakebed="1"` path so the lake normalizer never re-adds it, including as part of a longer GSHHS reservoir chain;
- reservoirs that GSHHS lacks (Lac de Buyo, Gatun Lake) come from the Natural Earth 1:10m lakes outline.

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
