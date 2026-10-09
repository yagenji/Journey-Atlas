#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXES = {
    "dominica": [("saintlucia", "stlucia"), ("saintvincentandthegrenadines", "stvincentgrenadines")],
    "gambia": [("guinea-bissau", "guineabissau"), ("sierra-leone", "sierraleone")],
    "grenada": [("saintvincentandthegrenadines", "stvincentgrenadines"), ("saintlucia", "stlucia")],
    "iran": [("turkey", "turkiye")],
    "lesotho": [("kyrgyzstan", "kyrgyz")],
    "stkittsnevis": [("saintlucia", "stlucia")],
}

changed = []
for owner, replacements in FIXES.items():
    path = ROOT / "data" / "countries" / f"{owner}.json"
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        target = ROOT / "data" / "countries" / f"{new}.json"
        if not target.exists():
            raise SystemExit(f"Missing canonical related-country target: {new}")
        pattern = rf'(\"slug\"\s*:\s*)\"{re.escape(old)}\"'
        text, count = re.subn(pattern, rf'\1\"{new}\"', text)
        if count != 1:
            raise SystemExit(f"Expected one {owner}:{old} related-country slug, found {count}")
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed.append(owner)

print("Normalized related-country slugs:", ", ".join(changed) if changed else "none")
