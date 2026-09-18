#!/usr/bin/env python3
"""One-time, strictly matched patch on the dedicated ops branch; self-removes before PR."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected exactly one anchor, found {count}: {old[:95]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


review = '.github/workflows/publication-pipeline-v2-review.yml'
patch(review,
      '      - name: Wait for the authoritative target QA on this exact Country revision\n',
      '''      - name: Require an independently authorized Country State writer before review QA
        if: steps.target.outputs.ready == 'true'
        env:
          PUBLISH_TOKEN: ${{ secrets.ATLAS_PUBLICATION_TOKEN }}
        shell: bash
        run: |
          if [ -z "$PUBLISH_TOKEN" ]; then
            echo '::error::ATLAS_PUBLICATION_TOKEN is required to reconcile review State on a Country PR. No QA, Pages deployment or GITHUB_TOKEN branch push was started. Configure the repository Actions secret, or complete the guarded review using the connected GitHub account.'
            exit 1
          fi
      - name: Wait for the authoritative target QA on this exact Country revision
''')
patch(review, 'token: ${{ secrets.ATLAS_PUBLICATION_TOKEN || github.token }}',
      'token: ${{ secrets.ATLAS_PUBLICATION_TOKEN }}')

canonical = '.github/workflows/canonical-country-review.yml'
patch(canonical, '      available: ${{ steps.ready.outputs.available }}\n',
      '      available: ${{ steps.ready.outputs.available }}\n      authorized: ${{ steps.auth.outputs.authorized }}\n')
patch(canonical, '\n  promote:\n', '''
      - name: Require authorized Country PR writer for automatic canonical promotion
        id: auth
        env:
          PUBLISH_TOKEN: ${{ secrets.ATLAS_PUBLICATION_TOKEN }}
        shell: bash
        run: |
          if [ -n "$PUBLISH_TOKEN" ]; then
            echo 'authorized=true' >> "$GITHUB_OUTPUT"
          else
            echo 'authorized=false' >> "$GITHUB_OUTPUT"
            echo 'Canonical promotion is paused: configure ATLAS_PUBLICATION_TOKEN or perform the guarded unpublished merge and live QA using the connected GitHub account. No Actions-bot PR update was attempted.' >> "$GITHUB_STEP_SUMMARY"
          fi

  promote:
''')
patch(canonical, "    if: needs.discover.outputs.available == 'true'\n",
      "    if: needs.discover.outputs.available == 'true' && needs.discover.outputs.authorized == 'true'\n")
patch(canonical, '    env:\n      GH_TOKEN: ${{ github.token }}\n      SLUG: ${{ matrix.slug }}',
      '    env:\n      GH_TOKEN: ${{ secrets.ATLAS_PUBLICATION_TOKEN }}\n      SLUG: ${{ matrix.slug }}')
patch(canonical, '          ref: ${{ matrix.branch }}\n          fetch-depth: 0\n',
      '          ref: ${{ matrix.branch }}\n          fetch-depth: 0\n          token: ${{ secrets.ATLAS_PUBLICATION_TOKEN }}\n')

final = '.github/workflows/publication-pipeline-v2-finalize.yml'
patch(final, '      - name: Ensure reusable review PR exists\n',
      '      - name: Find existing post-approval publication PR\n')
patch(final,
      '''          if [ -z "$pr" ]; then
            echo '::error::Open the reusable owner-authored Country PR before final approval. Publishing must not create a new PR.'
            exit 1
          fi
          echo "number=$pr" >> "$GITHUB_OUTPUT"
''',
      '''          # Canonical review merged its PR BEFORE user approval. A distinct
          # publication PR will be created only AFTER finalization has been staged.
          echo "number=$pr" >> "$GITHUB_OUTPUT"
''')
patch(final,
      '            git push --force-with-lease="refs/heads/$HEAD_REF:$(git rev-parse origin/$HEAD_REF)" origin "HEAD:refs/heads/$HEAD_REF"\n',
      '''            git push --force-with-lease="refs/heads/$HEAD_REF:$(git rev-parse origin/$HEAD_REF)" origin "HEAD:refs/heads/$HEAD_REF"
            if [ -z "$PR_NUMBER" ]; then
              PR_NUMBER="$(gh api --method POST "repos/$GITHUB_REPOSITORY/pulls" -f head="$HEAD_REF" -f base=main -f title="Publish approved $SLUG Country" -f body="Formal publication after explicit Country-page approval recorded in Production State. This PR follows the already-merged unpublished canonical review PR; retain all required checks and post-merge live verification." --jq '.number')"
              [ -n "$PR_NUMBER" ] || { echo 'Publication PR creation failed.' >&2; exit 1; }
            fi
''')
patch(final,
      '            if [ "$(git rev-parse origin/main)" != "$latest_main" ]; then echo "main advanced; retrying latest overlay"; continue; fi\n            response=',
      '''            if [ "$(git rev-parse origin/main)" != "$latest_main" ]; then echo "main advanced; retrying latest overlay"; continue; fi
            # A workflow_dispatch QA success is not a substitute for required
            # checks on the real publication PR's current head revision.
            timeout 420 gh pr checks "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --required --watch
            response=''' )

legacy = '.github/workflows/deploy-country-preview.yml'
patch(legacy,
      '''        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}

      - name: Set up Python''',
      '''        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          # New Pipeline v2 branches still trigger this legacy workflow. Avoid
          # downloading the full asset tree just to decide it is inapplicable.
          filter: blob:none
          sparse-checkout-cone-mode: false
          sparse-checkout: |
            data/countries/
            data/atlas-destinations.json
            ops/country-production/

      - name: Set up Python''')
patch(legacy,
      '      - name: Preview not required\n',
      '''      - name: Expand legacy preview sources only when actually required
        if: steps.target.outputs.should_preview == 'true'
        run: git sparse-checkout disable

      - name: Preview not required
''')

rules = 'docs/COUNTRY_PRODUCTION_RULES.md'
patch(rules,
      'Open or reuse one PR only after all 13 approved rasters are handed off and verified, when entering implementation/review QA. State-transition checks still run on Country pushes; PR-only checks must not be triggered by per-image progress. Do not open a PR for each image or State update.',
      'Open one unpublished-review PR only after all 13 approved rasters are handed off and verified, when entering implementation/review QA. The canonical noindex review merges that PR before final page approval. After explicit final approval, create a separate publication PR from the retained Country branch; do not create image-by-image, State-only, or verification-only PRs. State-transition checks still run on Country pushes; PR-only checks must not be triggered by per-image progress.')
patch(rules,
      'Until that external identity is enabled and the end-to-end path is verified, use the connected GitHub account to finalize the **existing owner-authored Country PR** on latest main after final approval, preserve all publication gates, wait for the actual required `validate` and `browser-qa` checks on its current PR head, squash merge, and verify the deployed SHA and canonical page. Do not create another PR, use Actions-bot commits to force PR checks, or add empty commits to trigger checks. A skipped automatic finalizer is not a publication success.',
      'Automatic review State reconciliation and canonical promotion also require `ATLAS_PUBLICATION_TOKEN`; if it is missing, the workflows stop before making Actions-bot changes to a Country PR. Until an independent identity is configured and the full path verified, use the connected GitHub account to perform each guarded stage: merge the **unpublished-review PR** only after its genuine required PR checks, confirm the canonical noindex page and live browser QA, record the verified review State, and—only after explicit final page approval—create the **separate publication PR** on latest main. Wait for actual `validate` and `browser-qa` checks on that PR head, squash merge and verify the deployed SHA and canonical page. Do not use Actions-bot commits or empty commits to force checks. A skipped or blocked automatic workflow is not a review or publication success.')

policy_path = ROOT / 'ops/country-production-policy.json'
policy = json.loads(policy_path.read_text(encoding='utf-8'))
assert policy['publicationAutomation']['review']['autoOpenReusablePr'] is True
assert policy['postVisual']['secondPublicationPr'] == 'REQUIRED_AFTER_UNPUBLISHED_REVIEW_PR_MERGE'
assert policy['postVisual']['reuseReviewPrForPublication'] is False
policy['publicationAutomation']['review']['autoOpenReusablePr'] = False
policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Source-aspect framing is opt-in for FUTURE Country scaffolds only. Every
# existing published/in-flight Country and its approved card rendering is intact.
scaffold = 'scripts/new_country.py'
patch(scaffold,
      '"imageState":"PENDING"}\n',
      '"imageState":"PENDING","imageFraming":"SOURCE_ASPECT"}\n')
patch(scaffold,
      'print("Publication Pipeline v2 locked for this new Country: post-handoff targeted QA, persistent review deployment, State reconciliation and post-approval publication are automated.")',
      'print("Publication Pipeline v2: independent ATLAS_PUBLICATION_TOKEN is needed for automated State reconciliation and canonical review; final page approval remains mandatory.")')

app = 'assets/js/app.js'
patch(app,
      "    image.addEventListener('load', () => {\n      // Match approved 4:3 artwork with integral paper ground to its own frame.\n",
      """    image.addEventListener('load', () => {
      // New Country assets opt in; unchanged legacy Country images keep the
      // exact approved framing rather than inheriting a global visual change.
      if (item.imageFraming === 'SOURCE_ASPECT' && image.naturalWidth > 0 &&
          image.naturalHeight > 0 &&
          Math.abs(image.naturalWidth / image.naturalHeight - 3 / 2) < 0.005) {
        article.querySelector('.taste-card__image').classList.add('taste-card__image--source-3x2');
        image.classList.add('taste-card__img--source-3x2');
      }
      // Match approved 4:3 artwork with integral paper ground to its own frame.
""")
css = 'assets/css/taste-image-framing.css'
patch(css,
      '/* Panama\'s approved 3:2 Taste illustrations include their own safe margins.\n',
      '''/* Future Country 3:2 artwork uses its real source aspect and integral paper
   ground. Legacy artwork has no opt-in and is rendered exactly as approved. */
.taste-card__image--source-3x2 {
  aspect-ratio: 3 / 2;
  background: transparent;
}
.taste-card__img--source-3x2 {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

/* Panama's approved 3:2 Taste illustrations include their own safe margins.
''')

# Validate every edited source before committing; fail the one-time job closed.
import subprocess
subprocess.run(['python3', '-m', 'py_compile', 'scripts/new_country.py',
                'scripts/_one_time_pipeline_repair_20260918.py'], check=True)
subprocess.run(['node', '--check', 'assets/js/app.js'], check=True)
subprocess.run(['python3', 'scripts/publication_pipeline_v2.py', 'self-test'], check=True)
assert json.loads(policy_path.read_text(encoding='utf-8'))['publicationAutomation']['review']['autoOpenReusablePr'] is False
(ROOT / 'scripts/_one_time_pipeline_repair_20260918.py').unlink()
(ROOT / '.github/workflows/_one-time-pipeline-repair-20260918.yml').unlink()
print('One-time patch and source checks PASS; temporary files removed.')
