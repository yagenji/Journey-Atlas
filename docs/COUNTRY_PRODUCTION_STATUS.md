# COUNTRY PRODUCTION STATUS

Country: Estonia
Status: GENERATING

Branch: estonia-v2-visual
Latest commit: pending status-file commit

Completed:
- Estonia country content implemented in data/countries/estonia.json.
- Estonia review route implemented at countries/estonia/index.html.
- Detailed 1200x760-style map asset implemented at assets/images/estonia/map-atlas-v2.svg.
- Hero + 8 scene assets are present as 1200x800 WebP files.
- Automated image decode/format/dimension QA passed for all 9 WebP assets.
- Country data validation passed.
- Review deployment to main succeeded.
- atlasPublished:false remains in data/atlas-destinations.json.
- Review route remains noindex,follow and excluded from normal discovery.
- TRAVEL THEMES taxonomy currently assigns Estonia to: 街を歩く / 時をたどる / 暮らしに出会う.

Current state:
- Visual QA found a specification mismatch: the current 9 assets under assets/images/estonia/approved/ are photographic source images rather than the JOURNEY ATLAS visual language of recognizable real places rendered with restrained watercolor treatment.
- Because visual quality/spec consistency is a Definition-of-Done gate, Estonia must not be marked COMPLETE.
- Existing main review page is preserved while visual remediation is performed on this branch.

Remaining:
- Regenerate Estonia Hero first, one image at a time, to Iceland / Norway visual standard.
- Obtain visual approval for the Hero before replacing production assets.
- Regenerate and approve all 8 scene images one by one.
- Replace only approved final assets in production paths; remove superseded photo-source production assets if no longer referenced.
- Re-run image QA, JSON validation, map/page integration checks, responsive/accessibility QA, and review deployment.
- Perform final visual review on the production country URL.
- Keep atlasPublished:false until explicit publication approval.

Next action:
- Generate a new Tallinn Old Town Hero from the Kohtuotsa viewpoint: recognizable real Tallinn skyline and red-roofed Old Town, wide composition, photographic spatial realism with quiet restrained watercolor softness, no poster treatment, no text, no invented architecture.

Last verified main commit:
- cc7a17f7e20fb2667b8a8b0e8c7c9a2def9cd6e8

Previous Estonia work branch:
- estonia-v1-build @ 3d68e8357b6c440039d3b0d6afc3e1ee1e32e8a0
- main is 2 commits ahead with no file differences versus that branch.
