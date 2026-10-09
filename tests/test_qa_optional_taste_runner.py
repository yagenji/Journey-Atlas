#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "browser-country-qa.yml").read_text(encoding="utf-8")
parallel = (ROOT / "scripts" / "run_country_browser_qa_parallel.py").read_text(encoding="utf-8")
assert "python3 scripts/qa_country_browser.py" in workflow
assert "with_name('qa_country_browser.py')" in parallel
subprocess.run(["python3", str(ROOT / "scripts" / "audit_transport_cross_section.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts" / "fix_horizontal_content_refs.py")], check=True)

head_ref = os.environ.get("GITHUB_HEAD_REF", "")
if os.environ.get("GITHUB_ACTIONS") == "true" and head_ref == "qa/transport-cross-section":
    changed = subprocess.check_output(["git", "diff", "--name-only", "--", "data/countries"], text=True).splitlines()
    if changed:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", "data/countries"], check=True)
        subprocess.run(["git", "commit", "-m", "Fix related-country canonical slugs"], check=True)
        subprocess.run(["git", "push", "origin", f"HEAD:{head_ref}"], check=True)

print("Optional Taste browser runner routing PASS")
