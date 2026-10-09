#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "browser-country-qa.yml").read_text(encoding="utf-8")
parallel = (ROOT / "scripts" / "run_country_browser_qa_parallel.py").read_text(encoding="utf-8")
assert "python3 scripts/qa_country_browser.py" in workflow
assert "with_name('qa_country_browser.py')" in parallel
print("Optional Taste browser runner routing PASS")

# Temporary branch-only hook for cross-sectional Seasons QA.
subprocess.run(["python3", "scripts/audit_seasons_cross_section.py"], cwd=ROOT, check=True)
