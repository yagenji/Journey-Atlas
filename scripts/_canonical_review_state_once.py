from pathlib import Path
import json
import sys
p = Path('scripts/country_production_protocol_v2.py')
text = p.read_text(encoding='utf-8')
needle = '    metrics = state.get("productionMetrics") if isinstance(state.get("productionMetrics"), dict) else {}\n'
replacement = '''    # A canonical-reviewed v2 Country must retain evidence from real live Browser QA.
    if (state.get("productionProtocolId") == "2.0" and phase == "REVIEW"
            and state.get("contentRef") == "main" and state.get("stateRef") == "main"):
        review = state.get("reviewDeployment") or {}
        expected_url = f"https://atlas.yagenji.com/countries/{state.get('slug')}/"
        if not (review.get("state") == "DONE"
                and review.get("url") == expected_url
                and review.get("productionVerification") == "LIVE_BROWSER_QA_PASS"
                and (state.get("publication") or {}).get("atlasPublished") is False):
            errors.append(f"{filename}: v2 REVIEW requires verified unpublished canonical Browser QA")

''' + needle
assert text.count(needle) == 1, 'protocol source changed; stop'
p.write_text(text.replace(needle, replacement), encoding='utf-8')
sys.path.insert(0, 'scripts')
import country_production_protocol_v2 as protocol
state = json.loads(Path('ops/country-production/grenada.json').read_text(encoding='utf-8'))
assert protocol.validate_protocol_state(state, 'grenada.json') == [], 'review State invalid'
state['reviewDeployment']['productionVerification'] = 'PENDING'
assert any('verified unpublished canonical Browser QA' in e for e in protocol.validate_protocol_state(state, 'grenada.json')), 'unverified REVIEW not rejected'
print('Canonical review source and negative validation PASS')
