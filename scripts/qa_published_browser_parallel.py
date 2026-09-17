#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_OUT = Path(os.environ.get("QA_OUT_DIR", "qa-browser-output"))


def partition(items: list[tuple[str, str]], workers: int) -> list[list[tuple[str, str]]]:
    if workers < 1:
        raise ValueError("workers must be >= 1")
    groups = [[] for _ in range(min(workers, max(1, len(items))))]
    for index, item in enumerate(items):
        groups[index % len(groups)].append(item)
    return [group for group in groups if group]


def run_original(env: dict[str, str]) -> int:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "qa_published_browser.py")],
        cwd=ROOT,
        env=env,
        check=False,
    ).returncode


def run_shard(index: int, group: list[tuple[str, str]], base_env: dict[str, str]) -> tuple[int, int, str]:
    env = dict(base_env)
    env["QA_SLUGS"] = ",".join(slug for slug, _name in group)
    env["QA_OUT_DIR"] = str(BASE_OUT / f"shard-{index:02d}")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "qa_published_browser.py")],
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return index, proc.returncode, proc.stdout


def merge_reports(
    qa: Any,
    groups: list[list[tuple[str, str]]],
    shard_codes: dict[int, int],
) -> int:
    results: list[dict] = []
    failures: list[dict] = []
    countries: list[str] = []
    viewports = qa.VIEWPORTS
    viewport_order = {name: index for index, name in enumerate(viewports)}
    missing_reports: list[str] = []

    for index, group in enumerate(groups):
        countries.extend(slug for slug, _name in group)
        report_path = BASE_OUT / f"shard-{index:02d}" / "report.json"
        if not report_path.exists():
            missing_reports.append(str(report_path))
            continue
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        results.extend(payload.get("results") or [])
        failures.extend(payload.get("failures") or [])

    if missing_reports:
        failures.append(
            {
                "slug": "_parallel_runner",
                "viewport": "preflight",
                "errors": ["missing shard report(s): " + ", ".join(missing_reports)],
            }
        )

    results.sort(key=lambda row: (row.get("slug", ""), viewport_order.get(row.get("viewport", ""), 99)))
    failures.sort(key=lambda row: (row.get("slug", ""), viewport_order.get(row.get("viewport", ""), 99)))
    merged = {
        "baseUrl": qa.BASE_URL,
        "countries": sorted(countries),
        "viewports": viewports,
        "parallelWorkers": len(groups),
        "results": results,
        "failures": failures,
        "pass": not failures and all(code == 0 for code in shard_codes.values()),
    }
    BASE_OUT.mkdir(parents=True, exist_ok=True)
    (BASE_OUT / "report.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pass": merged["pass"],
                "parallelWorkers": len(groups),
                "countryCount": len(countries),
                "failureCount": len(failures),
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0 if merged["pass"] else 1


def self_test() -> int:
    sample = [(f"c{i}", f"C{i}") for i in range(10)]
    groups = partition(sample, 4)
    assert len(groups) == 4
    flattened = [item for group in groups for item in group]
    assert sorted(flattened) == sorted(sample)
    assert max(len(group) for group in groups) - min(len(group) for group in groups) <= 1
    assert partition(sample[:2], 4) == [[sample[0]], [sample[1]]]
    print("Parallel browser QA partition self-test passed.")
    return 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()

    base_env = dict(os.environ)
    requested = base_env.get("QA_SLUGS", "").strip()
    scope = base_env.get("QA_SCOPE", "published").strip().lower()

    # Preserve the existing single-process path for targeted or non-published QA.
    if requested or scope != "published":
        return run_original(base_env)

    import qa_published_browser as qa

    countries = qa.load_countries()
    if len(countries) <= 1:
        return run_original(base_env)

    workers = int(base_env.get("QA_PARALLEL_WORKERS", "4"))
    workers = max(1, min(workers, 4, len(countries)))
    groups = partition(countries, workers)
    print(
        f"Parallel published Country QA: {len(countries)} countries across {len(groups)} workers",
        flush=True,
    )

    shard_codes: dict[int, int] = {}
    with ThreadPoolExecutor(max_workers=len(groups)) as pool:
        futures = {
            pool.submit(run_shard, index, group, base_env): index
            for index, group in enumerate(groups)
        }
        for future in as_completed(futures):
            index, code, output = future.result()
            shard_codes[index] = code
            print(f"\n===== published QA shard {index:02d} (exit={code}) =====", flush=True)
            print(output, end="" if output.endswith("\n") else "\n", flush=True)

    return merge_reports(qa, groups, shard_codes)


if __name__ == "__main__":
    raise SystemExit(main())
