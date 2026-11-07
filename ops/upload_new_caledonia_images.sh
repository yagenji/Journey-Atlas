#!/usr/bin/env bash
# Register approved New Caledonia artwork on the existing Draft PR branch.
# Requires a local checkout with GitHub push access. Does not merge or publish.
# Usage: bash ops/upload_new_caledonia_images.sh /absolute/path/JOURNEY_ATLAS_New_Caledonia_13_APPROVED_IMAGES.zip
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/JOURNEY_ATLAS_New_Caledonia_13_APPROVED_IMAGES.zip" >&2
  exit 2
fi
archive="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
[ -f "$archive" ] || { echo "ZIP not found: $archive" >&2; exit 2; }
repo="$(git rev-parse --show-toplevel)"
branch="draft/new-caledonia-region-20261107"
if [ "$(git -C "$repo" branch --show-current)" != "$branch" ]; then
  echo "Switch to $branch before running. No files were changed." >&2
  exit 2
fi

# Verify exactly 13 images, paths, SHA-256 hashes, and WebP file type
# BEFORE writing any assets. Do not re-encode or modify approved pixels.
python3 - "$archive" "$repo" <<'PY'
import hashlib
import pathlib
import shutil
import sys
import zipfile

archive, repo = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
rel = pathlib.Path("assets/images/france/new-caledonia/approved")
checksums = (repo / rel / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
expected = {}
for line in checksums:
    if not line or line.startswith("#"):
        continue
    digest, filename = line.split(maxsplit=1)
    filename = filename.strip()
    if filename.startswith("*"):
        filename = filename[1:]
    if not (len(digest) == 64 and filename.endswith(".webp")):
        raise SystemExit(f"Malformed checksum line: {line}")
    expected[str(rel / filename)] = digest.lower()

with zipfile.ZipFile(archive) as z:
    actual = {p for p in z.namelist() if p.endswith(".webp")}
    if len(expected) != 13 or actual != set(expected):
        raise SystemExit(f"Expected exactly 13 named WebPs: missing={set(expected)-actual}, unexpected={actual-set(expected)}")
    verified = {}
    for name, want in expected.items():
        raw = z.read(name)
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            raise SystemExit(f"Approved file differs from SHA256SUMS: {name}")
        if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
            raise SystemExit(f"Not a valid WebP signature: {name}")
        verified[name] = raw

for name, raw in verified.items():
    dst = repo / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Preserve approved bytes, and refuse to silently replace different files.
    if dst.exists() and dst.read_bytes() != raw:
        raise SystemExit(f"Different asset already exists: {dst}")
    dst.write_bytes(raw)
print(f"Verified and placed {len(verified)} approved WebP files without re-encoding")
PY

git -C "$repo" add assets/images/france/new-caledonia/approved
if ! git -C "$repo" diff --cached --quiet; then
  git -C "$repo" commit -m "assets: install 13 checksum-verified approved New Caledonia images"
  git -C "$repo" push origin "$branch"
else
  echo "Approved assets were already committed."
fi
echo "Done: Draft PR updated; no merge or publication performed."
