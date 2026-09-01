# Cloudflare Pages deployment

JOURNEY ATLAS keeps GitHub as the source of truth and uses Cloudflare Pages as the production CDN/host.

## Production architecture

- Source repository: `yagenji/Journey-Atlas`
- Production branch: `main`
- Production domain: `https://atlas.yagenji.com/`
- Cloudflare build output: `dist/`
- Review preview while authoring: canonical `/countries/{slug}/` route generated from `schemaVersion: 2` Country JSON
- Production country routes: `/countries/{slug}/`
- `schemaVersion: 2` countries are shipped for direct review; `atlasPublished: true` controls discovery, indexing and sitemap inclusion.

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

Cloudflare Pages will automatically create preview deployments for non-production branches when preview deployments are enabled.

## First deployment sequence

1. Connect Cloudflare Pages to the GitHub repository.
2. Deploy `main` to the generated `*.pages.dev` address.
3. Verify the top page and all currently published country routes.
4. In Cloudflare Pages, add the custom domain `atlas.yagenji.com`.
5. At the current DNS provider for `yagenji.com`, create the CNAME Cloudflare requests for `atlas` to the Pages hostname.
6. Wait until Cloudflare reports the custom domain as active and HTTPS is valid.
7. Verify `https://atlas.yagenji.com/`, `robots.txt`, `sitemap.xml`, canonical URLs, and OG URLs.

Do not change `data/site.json.baseUrl` during the transition. GitHub Pages still uses that value for the authoring/preview deployment; the Cloudflare production build overrides it with `JOURNEY_ATLAS_SITE_URL`.

## Publishing a country

A `schemaVersion: 2` Country JSON is reviewable at its canonical `/countries/{slug}/` URL with `noindex,follow`. It becomes formally published only when `atlasPublished` is set to `true` in its destination registry. The strict validator checks both reviewable and published countries before a production build. Once published, the build additionally enables:

- `index,follow` on `/countries/{slug}/`
- the country URL in `sitemap.xml`
- the production `href` in the destination registry copied into `dist/`

Reviewable unpublished Country JSON and page assets are copied into `dist/` only when required by the canonical noindex review route.

## Local/CI build

```bash
JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/ python3 scripts/build_cloudflare.py
```

The generated `dist/` directory is disposable build output and should not be committed.
