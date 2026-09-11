#!/usr/bin/env python3
"""Run Country image-delivery audit for explicitly changed Country slugs only.

The canonical normalization logic remains in normalize_country_image_delivery.py.
This wrapper avoids decoding every reviewable Country image when CI already knows
which Country or Countries changed.
"""

from __future__ import annotations

import argparse

import normalize_country_image_delivery as delivery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", action="append", required=True)
    args = parser.parse_args()

    requested = list(dict.fromkeys(args.slug))
    reviewable = set(delivery.reviewable_slugs())
    missing = [slug for slug in requested if slug not in reviewable]
    if missing:
        parser.error("not reviewable: " + ", ".join(missing))

    plans = delivery.build_plan(requested)
    delivery.print_plan(plans)
    errors = delivery.audit_delivery(requested)
    print(f"TARGETED AUDIT countries={len(requested)} issues={len(errors)}")
    for error in errors:
        print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
