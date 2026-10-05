#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
text = (root / "scripts" / "qa_country_browser.py").read_text(encoding="utf-8")
assert "return len(items)" in text
assert "taste_count == 0" in text
assert "#taste-section" in text
print("Optional Taste contract PASS")
