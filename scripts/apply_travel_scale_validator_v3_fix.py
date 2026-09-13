#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/validate_country.py")
text = path.read_text(encoding="utf-8")
old = '''            else:\n                final_duration = travel_items[2].get("duration") if isinstance(travel_items[2], dict) else None\n'''
new = '''            elif data.get("contentQaVersion", 1) < 3:\n                # Content QA v3 intentionally uses qualitative travel-scope labels.\n                # Its no-duration-count rule is enforced by validate_country_editorial_v2.py.\n                # Keep the legacy published day-format gate only for v1/v2 Countries.\n                final_duration = travel_items[2].get("duration") if isinstance(travel_items[2], dict) else None\n'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected exactly one published Travel Scale legacy block, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched scripts/validate_country.py")
