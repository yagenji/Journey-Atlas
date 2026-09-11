# Cloudflare Pages deployment

JOURNEY ATLAS keeps GitHub as the source of truth and uses Cloudflare Pages as the production CDN/host.

## Production architecture

- Source repository: `yagenji/Journey-Atlas`
- Production branch: `main`
- Production domain: `https://atlas.yagenji.com/`
- Cloudflare build output: `dist/`
- Protocol 2 pre-main Country review: targeted GitHub Pages preview from `country/{slug}`
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

For a Protocol 2 new Country, pre-main review uses the explicit GitHub Pages Country preview workflow. That workflow builds and Browser-QAs only the target Country. It does not run `build_cloudflare.py`, does not rebuild unrelated Countries, and does not alter production. After the user approves the final Country page, the terminal publication PR is integrated to `main` once and Cloudflare performs the one real production build.

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

A Protocol 2 new Country stays on `country/{slug}` through final page review. Its targeted GitHub Pages review package keeps `atlasPublished:false`, `noindex,follow`, sitemap exclusion, and normal-navigation exclusion.

Only after explicit final page approval does the terminal publication change move to `main` and set `atlasPublished:true`. The production build then enables:

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
