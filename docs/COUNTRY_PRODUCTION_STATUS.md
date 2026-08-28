# COUNTRY PRODUCTION STATUS

Country: Estonia
Status: QA

Branch: estonia-v3-cachefix
Latest commit: 7acf83c670062702659b6742d8b4fc1e3adaa5f2

Completed:
- Estonia country content implemented in data/countries/estonia.json.
- Estonia review route implemented at countries/estonia/index.html.
- Detailed map implemented at assets/images/estonia/map-atlas-v2.svg with a 1200 x 760 viewBox.
- Hero + 8 scene visuals explicitly APPROVED.
- Final visual direction locked to photographic realism 60% / watercolor treatment 40%, using Iceland as reference.
- Approved Hero + 8 scene binaries committed to assets/images/estonia/approved/ as 1200 x 800 WebP.
- Full WebP decode and exact 1200 x 800 dimensions verified for all 9 final images.
- Estonia country JSON validation passed.
- Temporary ZIP and temporary materialization workflow removed after successful asset replacement.
- PR #8 merged to main for REVIEW DEPLOYMENT.
- Deploy JOURNEY ATLAS to GitHub Pages workflow succeeded on main commit 58f0d3ae41283beed818724d34137b59068b0d9a.
- Source validation, production build, production-build validation, Pages setup, site upload and Pages deployment all succeeded.
- Cloudflare production package build and package validation also succeeded.
- Deployed GitHub Pages artifact was downloaded and verified to contain the 9 new Estonia WebP assets at 1200 x 800.
- atlasPublished:false remains unchanged.
- Estonia remains noindex,follow, sitemap-excluded and not linked from normal published-country discovery.
- TRAVEL THEMES taxonomy remains: 街を歩く / 時をたどる / 暮らしに出会う.
- Previous structural browser QA confirmed no console errors, all 8 scene cards, no material horizontal overflow, and Iceland / Norway template consistency before the final image replacement.
- Final image contact-sheet QA confirms coherent visual treatment across Hero + 8 scenes.

Current state:
- Root cause of the deployed-photo symptom identified: Estonia final generated images had replaced the old photographs under identical asset URLs while production image assets were cacheable for 24 hours.
- GitHub main and the GitHub Pages deploy artifact already contained the approved generated images, but existing browser/CDN cache could continue serving the old photo bytes.
- A clean cache-safe fix is prepared on estonia-v3-cachefix.
- The 9 approved generated assets now use new location-based final paths ending in -atlas.webp.
- Estonia JSON now references only the new -atlas.webp paths.
- Old photographic asset filenames and PHOTO_SOURCES.json have been removed from the Estonia approved production folder on this branch.
- Runtime photoCredits and the obsolete photoAssets source entry have been removed because those credits no longer describe the displayed generated visuals.
- Common Cloudflare image caching is changed to max-age=0, must-revalidate so future Country review image replacements do not remain stale for 24 hours.
- CSS, JS and icons retain their existing one-day cache policy.

Remaining:
- Validate all 9 renamed WebP assets at 1200 x 800 with complete decode.
- Validate Estonia country JSON and the Cloudflare review package.
- Merge estonia-v3-cachefix to main.
- Confirm Cloudflare/GitHub deployment success.
- Re-check https://atlas.yagenji.com/countries/estonia/ and confirm the new generated visual URLs are loaded.
- Keep atlasPublished:false.

Next action:
- Run cache-fix QA, merge to main, and review the canonical Estonia URL.
- Do not publish; atlasPublished:false remains mandatory.

Visual approval checklist:
- Hero / Tallinn Old Town: APPROVED
- Scene 1 / Viru Bog: APPROVED
- Scene 2 / Soomaa National Park: APPROVED
- Scene 3 / Panga Cliff: APPROVED
- Scene 4 / Kaali Meteorite Crater: APPROVED
- Scene 5 / Narva Castle: APPROVED
- Scene 6 / Suur Taevaskoda: APPROVED
- Scene 7 / Kõpu Lighthouse: APPROVED
- Scene 8 / Suur Munamägi: APPROVED

Review deployment:
- main commit: 58f0d3ae41283beed818724d34137b59068b0d9a
- deploy run: 33176689650
- PR: #8
- publication state: atlasPublished:false
