#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "browser-country-qa.yml").read_text(encoding="utf-8")
parallel = (ROOT / "scripts" / "run_country_browser_qa_parallel.py").read_text(encoding="utf-8")
assert "python3 scripts/qa_country_browser.py" in workflow
assert "with_name('qa_country_browser.py')" in parallel
subprocess.run(["python3", str(ROOT / "scripts" / "audit_transport_cross_section.py")], check=True)
print("Optional Taste browser runner routing PASS")
