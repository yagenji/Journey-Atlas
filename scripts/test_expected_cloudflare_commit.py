#!/usr/bin/env python3
"""Offline tests for Cloudflare production SHA-equivalence safety guards."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("expected_cloudflare_commit.py")
spec = importlib.util.spec_from_file_location("expected_cloudflare_commit", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DeploymentShaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.root = self.commit("index.html", "runtime")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True).strip()

    def commit(self, path, text):
        dest = self.repo / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        self.git("add", path)
        self.git("commit", "-qm", f"Change {path}")
        return self.git("rev-parse", "HEAD")

    def candidates(self):
        return module.candidate_commits(self.repo)

    def test_runtime_head_must_match_exactly(self):
        sha = self.commit("data/countries/panama.json", "{}")
        self.assertEqual(self.candidates(), [sha])

    def test_docs_only_may_use_preceding_deployed_sha(self):
        sha = self.commit("docs/README.md", "docs")
        self.assertEqual(self.candidates(), [sha, self.root])

    def test_state_only_is_non_runtime_but_registry_is_strict(self):
        state = self.commit("ops/country-production/panama.json", "{}")
        self.assertEqual(self.candidates(), [state, self.root])
        registry = self.commit("data/atlas-destinations.json", "{}")
        self.assertEqual(self.candidates(), [registry])

    def test_mixed_state_and_runtime_change_is_strict(self):
        self.commit("ops/country-production/panama.json", "{}")
        (self.repo / "assets/js").mkdir(parents=True)
        (self.repo / "assets/js/app.js").write_text("runtime", encoding="utf-8")
        (self.repo / "ops/country-production/panama.json").write_text("changed", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "mixed change")
        self.assertEqual(self.candidates(), [self.git("rev-parse", "HEAD")])

    def test_multiple_skips_allow_only_consecutive_safe_ancestors(self):
        first = self.commit("assets/js/app.js", "runtime")
        second = self.commit("docs/a.md", "docs")
        third = self.commit("ops/country-production/costarica.json", "{}")
        self.assertEqual(self.candidates(), [third, second, first])

    def test_production_workflows_and_policies_never_skip(self):
        for path in (
            ".github/workflows/verify-production.yml",
            ".github/workflows/reconcile-canonical-review-state.yml",
            "ops/country-production-policy.json",
            "scripts/expected_cloudflare_commit.py",
        ):
            with self.subTest(path=path):
                sha = self.commit(path, path)
                self.assertEqual(self.candidates(), [sha])

    def test_only_explicitly_safe_workflows_can_skip(self):
        for path in (
            ".github/workflows/audit-icons.yml",
            ".github/workflows/validate-visual-policy-waivers.yml",
        ):
            with self.subTest(path=path):
                prev = self.git("rev-parse", "HEAD")
                sha = self.commit(path, path)
                self.assertEqual(self.candidates()[:2], [sha, prev])

    def test_empty_commit_fails_closed(self):
        self.git("commit", "--allow-empty", "-qm", "empty")
        self.assertEqual(self.candidates(), [self.git("rev-parse", "HEAD")])


if __name__ == "__main__":
    unittest.main()
