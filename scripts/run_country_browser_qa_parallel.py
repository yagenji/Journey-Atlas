#!/usr/bin/env python3
"""Run the existing full Country browser audit across two local workers.

Build and serve the production package once. Each worker runs the unchanged
Selenium audit for every viewport, with an independent report directory.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

VIEWPORTS = ('desktop', 'tablet', 'mobile')


def split_slugs(slugs: list[str], workers: int) -> list[list[str]]:
    if workers < 1 or len(set(slugs)) != len(slugs):
        raise ValueError('Invalid worker count or duplicate Country slug')
    buckets = [[] for _ in range(min(workers, len(slugs)))]
    for index, slug in enumerate(sorted(slugs)):
        buckets[index % len(buckets)].append(slug)
    if sorted(slug for bucket in buckets for slug in bucket) != sorted(slugs):
        raise AssertionError('Country coverage changed while splitting workers')
    return buckets


def self_test() -> int:
    for count in (0, 1, 2, 3, 13, 29):
        slugs = [f'country-{i}' for i in range(count)]
        for workers in (1, 2, 3):
            buckets = split_slugs(slugs, workers)
            assert len(buckets) == min(workers, count)
            assert sorted(sum(buckets, [])) == sorted(slugs)
            assert max((len(bucket) for bucket in buckets), default=0) - min(
                (len(bucket) for bucket in buckets), default=0
            ) <= 1
    try:
        split_slugs(['belize', 'belize'], 2)
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate Country slugs must fail closed')
    print('Country Browser QA partition self-test PASS')
    return 0


def run(scope: str, output_root: Path, workers: int) -> int:
    if scope not in {'published', 'unpublished-reviewable'}:
        raise ValueError(f'Full-browser QA scope not supported: {scope}')
    if os.environ.get('QA_SLUGS', '').strip():
        raise ValueError('Full-browser QA must not inherit a restricted QA_SLUGS list')
    # The same selection function as the existing audit is the only source of
    # Country membership; do not keep a second list in the workflow.
    os.environ['QA_SCOPE'] = scope
    import qa_published_browser as qa  # Selenium is installed by the workflow.

    slugs = [slug for slug, _ in qa.load_countries()]
    buckets = split_slugs(slugs, workers)
    if not buckets:
        print(f'No {scope} Countries to inspect')
        return 0
    output_root.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    running = []
    try:
        for index, bucket in enumerate(buckets):
            output_dir = output_root / f'shard-{index}'
            output_dir.mkdir(parents=True, exist_ok=True)
            log_path = output_dir / 'runner.log'
            log = log_path.open('w', encoding='utf-8')
            env = os.environ.copy()
            env.update(QA_SCOPE=scope, QA_SLUGS=','.join(bucket), QA_OUT_DIR=str(output_dir))
            try:
                process = subprocess.Popen(
                    [sys.executable, str(Path(__file__).with_name('qa_published_browser.py'))],
                    env=env, stdout=log, stderr=subprocess.STDOUT,
                )
            except BaseException:
                log.close()
                raise
            running.append((index, bucket, output_dir, log_path, log, process))
            print(f'Browser QA {scope} shard {index}: {len(bucket)} Countries', flush=True)
        failed = False
        audited = []
        for index, bucket, output_dir, log_path, log, process in running:
            code = process.wait()
            log.close()
            report_path = output_dir / 'report.json'
            try:
                report = json.loads(report_path.read_text(encoding='utf-8'))
                pairs = Counter((row['slug'], row['viewport']) for row in report['results'])
                expected = Counter((slug, viewport) for slug in bucket for viewport in VIEWPORTS)
                complete = (sorted(report['countries']) == sorted(bucket) and pairs == expected)
                success = code == 0 and report['pass'] is True and not report['failures'] and complete
            except (OSError, ValueError, KeyError, TypeError) as exc:
                success = False
                print(f'Browser QA {scope} shard {index}: invalid report: {exc}', flush=True)
            if not success:
                failed = True
                print(f'Browser QA {scope} shard {index} FAILED (exit {code}); log tail:', flush=True)
                print('\n'.join(log_path.read_text(encoding='utf-8', errors='replace').splitlines()[-80:]), flush=True)
            else:
                audited.extend(bucket)
                print(f'Browser QA {scope} shard {index} PASS: {len(bucket)} Countries × 3 viewports', flush=True)
        if sorted(audited) != sorted(slugs):
            failed = True
        print(f'Browser QA {scope}: {len(audited)}/{len(slugs)} Countries; elapsed {time.monotonic() - started:.1f}s', flush=True)
        return 1 if failed else 0
    finally:
        for _index, _bucket, _out, _log_path, log, process in running:
            if process.poll() is None:
                process.terminate()
                process.wait()
            if not log.closed:
                log.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', choices=['published', 'unpublished-reviewable'])
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.scope:
        parser.error('--scope is required')
    if args.workers < 1 or args.workers > 2:
        parser.error('--workers must be 1 or 2 (limit concurrent browsers on one runner)')
    return run(args.scope, Path(os.environ.get('QA_OUT_DIR', 'qa-browser-output')), args.workers)


if __name__ == '__main__':
    raise SystemExit(main())
