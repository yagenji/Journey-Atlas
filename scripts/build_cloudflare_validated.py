#!/usr/bin/env python3
"""Build the Cloudflare package after source validation has already passed.

This CI-only wrapper deliberately leaves scripts/build_cloudflare.py unchanged.
It reuses the production builder and skips only the exact source-validation
commands that the calling workflow has already completed in the same job.
All build, packaging, build-meta, expected-file, and sitemap checks still run.
"""

from __future__ import annotations

import sys

import build_cloudflare


SKIP_AFTER_SOURCE_VALIDATION = {
    ("scripts/validate_lens_slugs.py",),
    ("scripts/validate_country.py", "--reviewable"),
    ("scripts/validate_country.py", "--published"),
}


def main() -> int:
    original_run = build_cloudflare.run

    def validated_run(*args: str, env: dict[str, str]) -> None:
        command = tuple(args[1:]) if args and args[0] == sys.executable else tuple(args)
        if command in SKIP_AFTER_SOURCE_VALIDATION:
            print("+ [source already validated] skip", " ".join(command), flush=True)
            return
        original_run(*args, env=env)

    build_cloudflare.run = validated_run
    try:
        return build_cloudflare.main()
    finally:
        build_cloudflare.run = original_run


if __name__ == "__main__":
    raise SystemExit(main())
