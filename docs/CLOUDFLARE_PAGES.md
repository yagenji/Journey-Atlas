# Cloudflare Pages deployment

JOURNEY ATLAS keeps GitHub as the source of truth and uses Cloudflare Pages as the production CDN/host.

## Production architecture

- Source repository: `yagenji/Journey-Atlas`
- Production branch: `main`
- Production domain: `https://atlas.yagenji.com/`
- Cloudflare build output: `dist/`
- Protocol 2 pre-main Country review: persistent targeted GitHub Pages preview triggered by the one Review PR
- Review route: `/reviews/{slug}/countries/{slug}/`
- Review cache branch: `review-previews` (generated cache only; never production authority)
- Production country routes: `/countries/{slug}/`
- `atlasPublished: true` controls discovery, indexing and sitemap inclusion in production.

The production package deliberately excludes:

- `country.html` (generic draft renderer)
- `scripts/`, `.github/`, authoring docs
- non-reviewable Country JSON and unreferenced production images
- Base64 source chunks (`*.b64`, `*.parts.json`, `*-parts/`)

## Cloudflare Pages project settings

Create a Pages project from the existing GitHub repository with these settings:

- Framework preset: `None`
- Production branch: `main`
- Root directory: repository root
- Build command: `python3 scripts/build_cloudflare.py`
- Build output directory: `dist`
- Environment variable: `JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/`

JOURNEY ATLAS does **not** use automatic Cloudflare Preview deployments for working branches. Cloudflare is the production surface and normal Country production must not deploy there before final page approval.

Recommended Pages branch control:
- Production branch: `main`
- Automatic production deployment: enabled
- Preview branch deployments: **None**

This prevents `country/**`, `system/**`, State-update and PR branches from creating unnecessary Cloudflare builds and notification email.

For a Protocol 2 new Country, pre-main review uses GitHub Pages, not Cloudflare. Open one Review PR from `country/{slug}` to `main`; opening or synchronizing that PR automatically runs the targeted Country preview workflow. No dedicated preview-trigger commit and no normal-path manual dispatch is required.

The GitHub Pages workflow:

- builds and Browser-QAs only the target Country;
- stores the compact review package under `/reviews/{slug}/`;
- preserves other active Country review paths instead of overwriting them;
- retains up to 8 review snapshots;
- uses immutable raw source-commit URLs for Country raster images so snapshots do not duplicate the raster payload;
- does not run `build_cloudflare.py`;
- does not alter production.

After the user approves the final Country page, update **the same Review PR** to terminal publication State. The serialized publication queue synchronizes latest `main`, waits for required checks and squash-merges it. Cloudflare then performs the one real production build. Do not create a second publication PR.

## First deployment sequence

1. Connect Cloudflare Pages to the GitHub repository.
2. Deploy `main` to the generated `*.pages.dev` address.
3. Verify the top page and all currently published country routes.
4. In Cloudflare Pages, add the custom domain `atlas.yagenji.com`.
5. At the current DNS provider for `yagenji.com`, create the CNAME Cloudflare requests for `atlas` to the Pages hostname.
6. Wait until Cloudflare reports the custom domain as active and HTTPS is valid.
7. Verify `https://atlas.yagenji.com/`, `robots.txt`, `sitemap.xml`, canonical URLs, and OG URLs.

Do not change `data/site.json.baseUrl` during the transition. Build workflows override the site URL with `JOURNEY_ATLAS_SITE_URL` for their intended environment.

## Reviewing and publishing a Country

A Protocol 2 new Country stays authoritative on `country/{slug}` through final page review. Its persistent GitHub Pages review keeps the Country out of production discovery; the review cache is `noindex` and is not the canonical production route.

Only after explicit final page approval does the same Review PR become the terminal publication change. Its terminal State includes the legacy COMPLETE-validator fields, including `reviewDeployment.state:DONE` with canonical URL `https://atlas.yagenji.com/countries/{slug}/` and CI-gated production-verification markers as defined by the State contract.

The production build then enables:

- `index,follow` on `/countries/{slug}/`
- the country URL in `sitemap.xml`
- the production `href` in the destination registry copied into `dist/`

Legacy already-integrated unpublished review pages may still exist on the canonical production route, but that is not the normal Protocol 2 path for new Countries.

## Local production build

```bash
JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/ python3 scripts/build_cloudflare.py
```

Use the full Cloudflare builder only for production/full-scope validation. Country-only authoring/review uses `scripts/build_country_preview_targeted.py` instead.

The generated `dist/` directory is disposable build output and should not be committed.
