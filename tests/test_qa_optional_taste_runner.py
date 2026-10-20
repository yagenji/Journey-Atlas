#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "browser-country-qa.yml").read_text(encoding="utf-8")
production = (ROOT / ".github" / "workflows" / "verify-production.yml").read_text(encoding="utf-8")
parallel = (ROOT / "scripts" / "run_country_browser_qa_parallel.py").read_text(encoding="utf-8")
assert "python3 scripts/qa_country_browser.py" in workflow
assert production.count("python3 scripts/qa_country_browser.py") == 2
assert '"scripts/qa_country_browser.py"' in production
assert "with_name('qa_country_browser.py')" in parallel
print("Optional Taste browser runner routing PASS")
