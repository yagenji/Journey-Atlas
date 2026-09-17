#!/usr/bin/env python3
"""List allowable deployed SHAs for an explicitly non-runtime main commit.

Normal runtime changes require an exact SHA match. Only consecutive commits
containing exclusively documented non-runtime paths may use the last deployed
ancestor. This accommodates Cloudflare Pages build-watch and CF-Pages-Skip
without weakening Country, registry, asset, or QA workflow verification.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

# Deliberately narrow. State changes never enter the production dist package;
# Country JSON, canonical registry, policy, and production QA code are NOT safe.
SAFE_EXACT = {
    ".github/workflows/audit-icons.yml",
    ".github/workflows/validate-visual-policy-waivers.yml",
}
SAFE_PREFIXES = ("docs/", "ops/country-production/")
MAX_COMMITS = 100


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL
    ).strip()


def safe_change(path: str) -> bool:
    return path in SAFE_EXACT or any(path.startswith(p) for p in SAFE_PREFIXES)


def changed_paths(repo: Path, commit: str) -> list[str]:
    # Compare each commit with its first parent: squash is the required main
    # merge method. A root commit is never treated as skippable.
    parents = git(repo, "rev-list", "--parents", "-n", "1", commit).split()
    if len(parents) < 2:
        return []
    return git(repo, "diff", "--name-only", parents[1], commit).splitlines()


def candidate_commits(repo: Path, head: str = "HEAD") -> list[str]:
    """Newest-first SHAs ending at the first non-skippable commit.

    If HEAD changes a runtime file, the list contains only HEAD. An empty or
    unknown diff is treated as runtime-changing (fail closed).
    """
    commits = git(repo, "rev-list", "--first-parent", f"--max-count={MAX_COMMITS}", head).splitlines()
    if not commits:
        raise ValueError(f"No commits reachable from {head!r}")
    result = []
    for sha in commits:
        result.append(sha)
        paths = changed_paths(repo, sha)
        if not paths or not all(safe_change(p) for p in paths):
            break
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--candidate-file", type=Path)
    a = p.parse_args()
    candidates = candidate_commits(a.repo, a.head)
    output = "\n".join(candidates) + "\n"
    if a.candidate_file:
        a.candidate_file.write_text(output, encoding="ascii")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
