#!/usr/bin/env python3
"""One-time owner-authorized Cuba publication staging; never merge this helper into main."""
import hashlib
import json
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image

ROOT = Path.cwd()
SLUG = 'cuba'
URL = 'https://atlas.yagenji.com/countries/cuba/'
REVIEW_SHA = 'd407cd77cfb3ca253ab4016a6e191129f4ad9772'
QA_JOB_ID = 105812411633
QA_RUN_ID = 35411631678
STATE = ROOT / 'ops/country-production/cuba.json'
COUNTRY = ROOT / 'data/countries/cuba.json'
REGISTRY = ROOT / 'data/atlas-destinations.json'
STATUS = ROOT / 'data/country-renewal-status.json'

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, x, compact=False):
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':') if compact else None,
                            indent=None if compact else 2) + '\n', encoding='utf-8')

def run(*args):
    subprocess.run(args, check=True)

run('git', 'fetch', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main')
run('git', 'merge-base', '--is-ancestor', 'origin/main', 'HEAD')
run('git', 'merge-base', '--is-ancestor', REVIEW_SHA, 'HEAD')
run('git', 'diff', '--quiet', REVIEW_SHA, 'HEAD', '--', 'data/countries/cuba.json', 'assets/images/cuba')
state, country, registry = load(STATE), load(COUNTRY), load(REGISTRY)
assert state.get('slug') == SLUG and country.get('slug') == SLUG
assert country.get('publicationPipelineVersion') == 2
assert state.get('phase') == 'IMPLEMENTATION' and state.get('stateRevision') == 16
assert state.get('finalApproval', {}).get('state') == 'PENDING'
assert state.get('publication', {}).get('atlasPublished') is False
assert state.get('assetHandoff', {}).get('verifiedRasterCount') == 13
assert state.get('sceneBatchReview', {}).get('approval') == 'APPROVED'
assert state.get('tasteBatchReview', {}).get('approval') == 'APPROVED'
assert registry.get('count') == 201 and len(registry.get('destinations', [])) == 201
rows = [r for r in registry['destinations'] if r.get('slug') == SLUG]
assert len(rows) == 1 and rows[0].get('atlasPublished') is False
assert not rows[0].get('href')

job_url = f'https://api.github.com/repos/yagenji/Journey-Atlas/actions/jobs/{QA_JOB_ID}'
req = urllib.request.Request(job_url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'journey-atlas-cuba-release-qa'})
with urllib.request.urlopen(req, timeout=15) as response:
    job = json.load(response)
assert job.get('run_id') == QA_RUN_ID and job.get('head_sha') == REVIEW_SHA
assert job.get('status') == 'completed' and job.get('conclusion') == 'success'
assert job.get('name') == 'qa-reviewable' and job.get('completed_at')
with urllib.request.urlopen(urllib.request.Request(URL + '?prepublication=cuba-20260919', headers={'Cache-Control': 'no-cache'}), timeout=20) as response:
    html = response.read().decode('utf-8')
assert 'noindex,follow' in html.lower(), 'Canonical page noindex guard failed'
with urllib.request.urlopen(urllib.request.Request('https://atlas.yagenji.com/data/countries/cuba.json?prepublication=cuba-20260919', headers={'Cache-Control': 'no-cache'}), timeout=20) as response:
    live = json.load(response)
assert live.get('slug') == SLUG and live.get('nextRoutes') == [], 'Live corrected Cuba content missing'

assets = [state['hero']['asset']] + [x['asset'] for x in state['scenes']] + [x['asset'] for x in state['taste']]
country_assets = [country['hero']['image']] + [x['image'] for x in country['scenes']] + [x['image'] for x in country['taste']['items']]
assert assets == country_assets and len(assets) == len(set(assets)) == 13
assert len(state['scenes']) == 8 and len(state['taste']) == 4
assert all(x.get('state') == 'APPROVED' for x in [state['hero'], *state['scenes'], *state['taste']])
hashes = set()
for asset in assets:
    path = ROOT / asset
    assert path.is_file() and path.stat().st_size > 4096, asset
    with Image.open(path) as image:
        assert image.format == 'WEBP' and image.width >= 1000 and image.height >= 700, asset
        image.load()
    hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
assert len(hashes) == 13, 'Duplicate image bytes'
map_path = ROOT / country['map']['svg']
assert map_path.is_file() and ET.parse(map_path).getroot().get('viewBox') == '0 0 1200 760'
assert state.get('map', {}).get('state') == 'APPROVED'
assert country.get('nextRoutes') == []
print('Cuba verified live noindex QA, unchanged reviewed country files, 13 approved decoded unique assets and 1200x760 map: PASS')

stamp = datetime.now(timezone(timedelta(hours=9))).replace(microsecond=0).isoformat()
state['contentRef'] = 'main'
state['stateRef'] = 'main'
state['phase'] = 'REVIEW'
state['publicationPipelineVersion'] = 2
state['implementation'] = {**state.get('implementation', {}), 'state': 'DONE', 'completedAt': stamp,
                           'sharedTemplate': True, 'countrySpecificCss': False}
state['qa'] = {**state.get('qa', {}), 'state': 'PASS', 'productionState': 'CI_GATED',
               'sourceCommit': REVIEW_SHA,
               'checks': ['publication-v2-targeted-validation', 'publication-v2-image-audit',
                          'production-live-desktop-tablet-mobile-browser-qa'], 'runId': QA_RUN_ID}
state['reviewDeployment'] = {'state': 'DONE', 'url': URL, 'productionVerification': 'LIVE_BROWSER_QA_PASS',
                             'verifiedAt': job['completed_at'],
                             'verificationBasis': f'https://github.com/yagenji/Journey-Atlas/actions/runs/{QA_RUN_ID}/job/{QA_JOB_ID}',
                             'pipelineVersion': 2}
state['finalApproval'] = {'state': 'APPROVED', 'approvedAt': stamp,
                          'basis': 'User explicitly requested QA and formal Cuba publication repeatedly on 2026-09-19, after reviewing the corrected unpublished canonical page. The unchanged Cuba files passed live Desktop/Tablet/Mobile QA at run 35411631678.'}
state['next'] = {'action': 'FORMAL_PUBLISH', 'asset': None}
state['stateRevision'] += 1
state['updatedAt'] = stamp
write(STATE, state)
run('python3', 'scripts/validate_production_state_routed.py')
run('python3', 'scripts/publication_pipeline_v2.py', 'assert-publish-ready', SLUG)
run('python3', 'scripts/publication_pipeline_v2.py', 'finalize', SLUG)
published = load(STATE)
assert published['publication']['atlasPublished'] is True
assert published['reviewDeployment']['prePublicationReviewVerification'] == 'LIVE_BROWSER_QA_PASS'
updated = load(REGISTRY)
assert updated['count'] == 201 and len(updated['destinations']) == 201
assert len([r for r in updated['destinations'] if r.get('slug') == SLUG and r.get('atlasPublished') is True]) == 1
assert next(r for r in updated['destinations'] if r.get('slug') == SLUG)['image'] == state['hero']['asset']
status = load(STATUS)
status_rows = status.setdefault('countries', [])
row = next((r for r in status_rows if r.get('slug') == SLUG), None)
base = {'slug': SLUG, 'nameJa': country.get('nameJa') or 'キューバ', 'wave': 9, 'published': True,
        'auditState': 'AUDITED', 'renewalClass': 'UNCLASSIFIED', 'content': 'DONE', 'visual': 'DONE',
        'map': 'DONE', 'sources': 'DONE', 'qa': 'PASS', 'production': 'CI_GATED',
        'hardImageGate': True, 'automatedAudit': 'DONE',
        'notes': ['Publication Pipeline v2. Corrected Cuba canonical noindex Desktop/Tablet/Mobile Browser QA verified before explicit user approval. Production verification remains required after merge.']}
if row is None:
    status_rows.append(base)
else:
    row.update(base)
status['updatedAt'] = stamp[:10]
write(STATUS, status, compact=True)
run('python3', 'scripts/validate_production_state_routed.py')
run('python3', 'scripts/audit_published_countries.py')
run('python3', 'scripts/validate_country.py', '--strict', str(COUNTRY.relative_to(ROOT)))
changed = set(subprocess.check_output(['git', 'diff', '--name-only'], text=True).splitlines())
expected = {'ops/country-production/cuba.json', 'data/atlas-destinations.json', 'data/country-renewal-status.json'}
assert changed == expected, f'Unexpected changed paths: {changed}'
run('git', 'config', 'user.name', 'github-actions[bot]')
run('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
run('git', 'add', *sorted(expected))
run('git', 'commit', '-m', 'Stage approved Cuba publication after verified canonical QA')
run('git', 'push', 'origin', 'HEAD:country/cuba-publication-20260919')
print('Cuba publication content staged on Country-only branch; merge and live production verification still required')
