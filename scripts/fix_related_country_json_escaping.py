#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "dominica": ["stlucia", "stvincentgrenadines"],
    "gambia": ["guineabissau", "sierraleone"],
    "grenada": ["stvincentgrenadines", "stlucia"],
    "iran": ["turkiye"],
    "lesotho": ["kyrgyz"],
    "stkittsnevis": ["stlucia"],
}
for owner, slugs in TARGETS.items():
    path = ROOT / "data" / "countries" / f"{owner}.json"
    text = path.read_text(encoding="utf-8")
    for slug in slugs:
        bad = f'\\"{slug}\\"'
        count = text.count(bad)
        if count != 1:
            raise SystemExit(f"Expected one malformed {owner}:{slug}, found {count}")
        text = text.replace(bad, f'"{slug}"')
    path.write_text(text, encoding="utf-8")
print("Repaired related-country JSON escaping")
