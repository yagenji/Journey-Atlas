# Cloudflare Pages deployment

JOURNEY ATLAS uses GitHub as the source of truth and Cloudflare Pages as the production host.

## Production architecture

- Source repository: `yagenji/Journey-Atlas`
- Production branch: `main`
- Production domain: `https://atlas.yagenji.com/`
- Build command: `python3 scripts/build_cloudflare.py`
- Build output: `dist/`
- Country route: `/countries/{slug}/`
- `data/atlas-destinations.json` is the publication/discovery authority.

`atlasPublished:false` means a schema-v2 Country can be reviewed directly at its canonical route but remains `noindex,follow`, outside sitemap and normal discovery.
`atlasPublished:true` enables normal discovery, `index,follow` and sitemap inclusion.

## Cloudflare project settings

- Framework preset: `None`
- Production branch: `main`
- Root directory: repository root
- Build command: `python3 scripts/build_cloudflare.py`
- Build output directory: `dist`
- Environment variable: `JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/`
- Automatic production deployment: enabled
- Preview branch deployments: none

Cloudflare is the production surface. Working `country/**` and `system/**` branches must not create production deployments.

## New Country review and publication

The normal lifecycle is deliberately simple.

1. Build the finished Country on one Country branch.
2. Open one review PR while the destination remains `atlasPublished:false`.
3. Required pre-merge checks run finish-line Content / Image / Map / Browser QA against the affected Country.
4. Merge the reviewed Country package while it remains unpublished.
5. Review the canonical page at:
   `https://atlas.yagenji.com/countries/{slug}/`
6. After explicit user approval, open one small publication PR from latest `main`.
7. The publication PR changes only the publication/discovery metadata required to set the Country live.
8. Merge it after required checks.
9. `.github/workflows/verify-production.yml` verifies the deployed SHA and affected route.

There is no Country Production State, publication queue, review cache branch, approval ledger or pipeline reconciliation step.

## QA behavior

Pre-merge:
- `validate` always resolves on every PR;
- Country changes run target finish-line QA;
- publication-metadata-only PRs reuse the already-reviewed Country QA and validate registries only;
- `browser-qa` always resolves on every PR and runs Browser QA only when rendering is affected.

Post-merge:
- production verification waits for Cloudflare to serve the merged SHA;
- target Country routes are smoke-tested when a Country/publication change is detected;
- shared rendering changes may trigger broader live Browser QA.

## Production package

The package deliberately excludes authoring-only material such as:
- `country.html` generic draft renderer;
- `scripts/`;
- `.github/`;
- authoring documentation;
- unreferenced production images;
- encoded source chunks such as `*.b64` and `*.parts.json`.

## Local production build

```bash
JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/ python3 scripts/build_cloudflare.py
```

Use the full Cloudflare build for production/full-scope verification. Country-only review should use the targeted Country build/Browser QA path.

The generated `dist/` directory is disposable and is not committed.
