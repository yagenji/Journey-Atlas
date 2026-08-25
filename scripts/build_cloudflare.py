#!/usr/bin/env python3
"""Build the clean Cloudflare Pages production package for JOURNEY ATLAS."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTION_URL = "https://atlas.yagenji.com/"


def run(*args: str, env: dict[str, str]) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def main() -> int:
    env = os.environ.copy()
    env.setdefault("JOURNEY_ATLAS_SITE_URL", DEFAULT_PRODUCTION_URL)

    run(sys.executable, "scripts/validate_country.py", "--published", env=env)
    run(sys.executable, "scripts/build_site.py", env=env)
    run(sys.executable, "scripts/validate_country.py", "--published", env=env)
    run(sys.executable, "scripts/package_site.py", env=env)

    dist = ROOT / "dist"
    expected = [
        dist / "index.html",
        dist / "sitemap.xml",
        dist / "robots.txt",
        dist / "_headers",
        dist / "assets" / "css" / "country.css",
        dist / "assets" / "css" / "top.css",
        dist / "countries" / "iceland" / "index.html",
    ]
    missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
    if missing:
        raise FileNotFoundError("Cloudflare package is incomplete: " + ", ".join(missing))

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    target = env["JOURNEY_ATLAS_SITE_URL"].rstrip("/") + "/"
    if target not in sitemap:
        raise ValueError(f"Production URL not found in sitemap: {target}")

    print(f"Cloudflare Pages package ready: dist/ ({target})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
