#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = "atlas-destinations-editorial.json"
SELF = Path(__file__).resolve()

TARGET_FILES = [
    "docs/README.md",
    "README.md",
    "scripts/validate_destination_scope.py",
    "scripts/package_site.py",
    "scripts/country_overlay_v2.py",
    "scripts/new_country.py",
    "docs/COUNTRY_TEMPLATE.md",
    "assets/js/top.js",
    "scripts/audit_published_countries.py",
    "scripts/classify_country_impact.py",
    "scripts/build_site.py",
    "scripts/audit_country_region_labels.py",
    "scripts/manage_review_preview_site.py",
    "assets/js/map-regions.js",
    "scripts/validate_images.py",
    "scripts/normalize_country_region_labels.py",
    "scripts/validate_country.py",
    "scripts/qa_published_browser.py",
    "scripts/publication_pipeline_v2.py",
    "scripts/build_country_preview_targeted.py",
    "scripts/country_production_state.py",
    "scripts/normalize_country_image_delivery.py",
    ".github/workflows/validate-destination-scope.yml",
    ".github/workflows/validate-production-state.yml",
    ".github/workflows/publish-country-queue.yml",
    ".github/workflows/validate-country-data.yml",
    ".github/workflows/browser-country-qa.yml",
    ".github/workflows/verify-production.yml",
    ".github/workflows/sync-conflicted-country-publication.yml",
    ".github/workflows/deploy-country-preview.yml",
    ".github/workflows/publication-pipeline-v2-finalize.yml",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_exact(rel: str, old: str, new: str, expected: int = 1) -> None:
    text = read(rel)
    found = text.count(old)
    if found != expected:
        raise SystemExit(f"{rel}: expected {expected} exact match(es), found {found}: {old!r}")
    write(rel, text.replace(old, new, expected))


def special_replacements() -> None:
    replace_exact(
        "assets/js/top.js",
        "const editorialRegistryPromise=fetch('data/atlas-destinations-editorial.json')\n"
        "  .then((response)=>{if(!response.ok) throw new Error('Editorial destination registry not found');return response.json();});\n\n",
        "",
    )
    replace_exact(
        "assets/js/top.js",
        "Promise.all([coreRegistryPromise,editorialRegistryPromise])\n"
        "  .then(([core, editorial])=>{\n"
        "    const items=[...(core.destinations||[]),...(editorial.destinations||[])];\n"
        "    destinations=sortForDisplay(items);",
        "coreRegistryPromise\n"
        "  .then((core)=>{\n"
        "    destinations=sortForDisplay(core.destinations||[]);",
    )

    replace_exact(
        "assets/js/map-regions.js",
        "    fetch('data/atlas-destinations.json?v=20260825-0128').then(r => r.json()),\n"
        "    fetch('data/atlas-destinations-editorial.json?v=20260825-0128').then(r => r.json())",
        "    fetch('data/atlas-destinations.json?v=20260825-0128').then(r => r.json())",
    )
    replace_exact(
        "assets/js/map-regions.js",
        "]).then(([m, a, rd, core, editorial]) => {\n"
        "    regions = rd.regions || [];\n"
        "    dest = [...(core.destinations || []), ...(editorial.destinations || [])];",
        "]).then(([m, a, rd, core]) => {\n"
        "    regions = rd.regions || [];\n"
        "    dest = core.destinations || [];",
    )

    replace_exact(
        "scripts/build_site.py",
        "    for path in (CORE_REGISTRY_PATH, EDITORIAL_REGISTRY_PATH):",
        "    for path in (CORE_REGISTRY_PATH,):",
    )

    replace_exact(
        "scripts/validate_destination_scope.py",
        "    compat = load(COMPAT_REGISTRY)\n",
        "",
    )
    replace_exact(
        "scripts/validate_destination_scope.py",
        "    if compat.get(\"count\") != 0 or compat.get(\"destinations\") not in ([], None):\n"
        "        errors.append(\"atlas-destinations-editorial.json must remain an empty compatibility registry\")\n"
        "    if compat.get(\"deprecated\") is not True:\n"
        "        errors.append(\"atlas-destinations-editorial.json must be marked deprecated\")\n"
        "    if compat.get(\"canonicalRegistry\") != \"data/atlas-destinations.json\":\n"
        "        errors.append(\"compatibility registry must point to data/atlas-destinations.json\")\n\n",
        "",
    )

    replace_exact(
        "docs/COUNTRY_TEMPLATE.md",
        "`data/atlas-destinations.json` or `data/atlas-destinations-editorial.json`",
        "`data/atlas-destinations.json`",
    )


def normalize_common_references() -> None:
    # Same-line Python tuples must stay tuples after removing the compatibility entry.
    tuple_old = '("atlas-destinations.json", "atlas-destinations-editorial.json")'
    tuple_new = '("atlas-destinations.json",)'

    for rel in TARGET_FILES:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"Missing expected migration target: {rel}")
        text = path.read_text(encoding="utf-8")
        text = text.replace(tuple_old, tuple_new)
        text = text.replace(', ROOT / "data" / "atlas-destinations-editorial.json"', '')
        text = text.replace(' data/atlas-destinations-editorial.json', '')
        text = text.replace(' or `data/atlas-destinations-editorial.json`', '')

        # All remaining occurrences in known targets are standalone dependency/docs lines.
        lines = text.splitlines(keepends=True)
        lines = [line for line in lines if TARGET not in line]
        path.write_text("".join(lines), encoding="utf-8")


def delete_compat_registry() -> None:
    path = ROOT / "data" / TARGET
    if not path.exists():
        raise SystemExit(f"Compatibility registry already missing unexpectedly: {path}")
    path.unlink()


def assert_clean() -> None:
    leftovers: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == SELF:
            continue
        if ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if TARGET in text:
            for number, line in enumerate(text.splitlines(), 1):
                if TARGET in line:
                    leftovers.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    if leftovers:
        raise SystemExit("Compatibility registry references remain:\n" + "\n".join(leftovers))
    if (ROOT / "data" / TARGET).exists():
        raise SystemExit("Compatibility registry file still exists")


def main() -> int:
    special_replacements()
    normalize_common_references()
    delete_compat_registry()
    assert_clean()
    print("Editorial compatibility registry migration PASS: canonical 201 registry is the sole destination registry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
