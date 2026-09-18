#!/usr/bin/env python3
"""One-time narrowly scoped guard against two parallel Country publication owners."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
queue = root / '.github/workflows/publish-country-queue.yml'
text = queue.read_text(encoding='utf-8')
old = '''          if state.get("productionProtocolId") != "2.0":
              print("false")
              raise SystemExit

          registry_published = False
'''
new = '''          if state.get("productionProtocolId") != "2.0":
              print("false")
              raise SystemExit

          # Pipeline v2 has its own guarded finalizer. Never let the older
          # publication queue race it for the same approved Country PR.
          country_path = Path("data/countries") / f"{slug}.json"
          if (country_path.exists() and
                  json.loads(country_path.read_text(encoding="utf-8")).get("publicationPipelineVersion") == 2):
              print("false")
              raise SystemExit

          registry_published = False
'''
assert text.count(old) == 1, 'Legacy queue publication-readiness anchor changed'
queue.write_text(text.replace(old, new, 1), encoding='utf-8')

policy_path = root / 'ops/country-production-policy.json'
policy = json.loads(policy_path.read_text(encoding='utf-8'))
assert policy['postVisual']['publicationQueueWorkflow'] == '.github/workflows/publish-country-queue.yml'
policy['postVisual']['publicationQueueWorkflow'] = '.github/workflows/publication-pipeline-v2-finalize.yml'
policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

checks = root / '.github/workflows/validate-publication-pipeline-v2.yml'
text = checks.read_text(encoding='utf-8')
old = "          final = Path('.github/workflows/publication-pipeline-v2-finalize.yml').read_text()\n"
new = old + "          legacy_queue = Path('.github/workflows/publish-country-queue.yml').read_text()\n"
assert text.count(old) == 1, 'Pipeline v2 validator anchor changed'
text = text.replace(old, new, 1)
old = "          if 'validate_country_map_v6.py' not in checks:\n"
new = ("          if 'publicationPipelineVersion' not in legacy_queue or 'publicationPipelineVersion') == 2' not in legacy_queue:\n"
       "              raise SystemExit('Legacy publication queue must reject v2-owned Countries')\n" + old)
assert text.count(old) == 1, 'Pipeline v2 map validator anchor changed'
checks.write_text(text.replace(old, new, 1), encoding='utf-8')

import subprocess
subprocess.run(['python3', 'scripts/publication_pipeline_v2.py', 'self-test'], check=True)
subprocess.run(['python3', '-m', 'py_compile', 'scripts/_one_time_legacy_queue_isolation_20260918.py'], check=True)
(root / 'scripts/_one_time_legacy_queue_isolation_20260918.py').unlink()
(root / '.github/workflows/_one-time-legacy-queue-isolation-20260918.yml').unlink()
print('Legacy queue ownership separated; one-time files removed.')
