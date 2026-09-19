from pathlib import Path
p=Path('.github/workflows/validate-country-data.yml')
s=p.read_text(encoding='utf-8')
needle="      - 'scripts/country_production_protocol_v2.py'\n"
assert s.count(needle)==2, 'validation triggers changed; manual review required'
s=s.replace(needle,needle+"      - 'scripts/publication_pipeline_v2.py'\n      - 'scripts/test_canonical_review_publication_gate.py'\n")
p.write_text(s,encoding='utf-8')
print('Publication helper and test now trigger standard validate on PR and main pushes')
