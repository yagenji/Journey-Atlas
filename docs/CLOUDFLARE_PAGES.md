# Cloudflare Pages deployment

JOURNEY ATLAS keeps GitHub as the source of truth and uses Cloudflare Pages as the production CDN/host.

## Production architecture

- Source repository: `yagenji/Journey-Atlas`
- Production branch: `main`
- Production domain: `https://atlas.yagenji.com/`
- Cloudflare build output: `dist/`
- Draft preview while authoring: existing GitHub Pages generic route (`country.html?country=...`)
- Production country routes: `/countries/{slug}/`
- A country is shipped only when its registry entry has `atlasPublished: true`.

The production package deliberately excludes:

- `country.html` (generic draft renderer)
- `scripts/`, `.github/`, authoring docs
- unpublished `data/countries/*.json`
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

A country remains a draft until `atlasPublished` is set to `true` in its destination registry. The strict validator checks published countries before a production build. Once published, the build generates:

- `/countries/{slug}/index.html`
- the corresponding runtime country JSON
- the country URL in `sitemap.xml`
- the production `href` in the destination registry copied into `dist/`

Unpublished country bodies are not copied into `dist/`.

## Local/CI build

```bash
JOURNEY_ATLAS_SITE_URL=https://atlas.yagenji.com/ python3 scripts/build_cloudflare.py
```

The generated `dist/` directory is disposable build output and should not be committed.
