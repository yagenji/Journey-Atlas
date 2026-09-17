# JOURNEY ATLAS — Country Production Protocol 2.0

Status: **technical compatibility reference**. This file is intentionally short and is **not** startup reading for a new Country.

## Human operation

Use `docs/COUNTRY_PRODUCTION_RULES.md` as the single human operational authority for new Country production.

Do not load this file together with the human rules merely to repeat the same production sequence.

## Machine authority

Protocol 2 enforcement remains in:
- `ops/country-production-policy.json` — lifecycle, interaction, review/publication contract;
- `ops/image-generation-policy.json` — image-generation/state contract;
- `scripts/country_production_protocol_v2.py` — current NEXT, gates and handoff behavior;
- current validators and Publication Pipeline v2 workflows.

Read those machine sources only when executing or diagnosing their specific contract. Do not copy their complete contents into chat prompts.

## Compatibility

- New Countries use the current Protocol 2 / Content QA / Publication Pipeline contracts enforced by main.
- Existing in-flight legacy Countries retain their recorded contract until explicitly migrated.
- Canonical unpublished review remains separate from formal publication; final publication still requires explicit user approval.
- This compatibility file must not introduce a second set of editorial, visual or publication rules.
