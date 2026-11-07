#!/usr/bin/env bash
# Upload only the already-approved New Caledonia Region image binaries to the Draft PR branch.
# Usage (from a local Journey-Atlas checkout with GitHub push access):
#   bash ops/upload_new_caledonia_images.sh /absolute/path/JOURNEY_ATLAS_New_Caledonia_13_APPROVED_IMAGES.zip
# This script does NOT merge, deploy or publish the Region.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: bash ops/upload_new_caledonia_images.sh /path/to/JOURNEY_ATLAS_New_Caledonia_13_APPROVED_IMAGES.zip" >&2
  exit 2
fi
archive="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
if [ ! -f "$archive" ]; then echo "ZIP not found: $archive" >&2; exit 2; fi
repo="$(git rev-parse --show-toplevel)"
branch="draft/new-caledonia-region-20261107"
if [ "$(git -C "$repo" branch --show-current)" != "$branch" ]; then
  echo "Switch to $branch before running. No files were changed." >&2
  exit 2
fi

# Archive paths already include the correct approved-image destination.
unzip -oq "$archive" 'assets/images/france/new-caledonia/approved/*.webp' -d "$repo"
image_dir="$repo/assets/images/france/new-caledonia/approved"
count="$(find "$image_dir" -maxdepth 1 -type f -name '*.webp' | wc -l | tr -d ' ')"
if [ "$count" -ne 13 ]; then
  echo "Expected 13 approved WebPs, found $count; do not push." >&2
  exit 1
fi

git -C "$repo" add assets/images/france/new-caledonia/approved
if ! git -C "$repo" diff --cached --quiet; then
  git -C "$repo" commit -m "assets: add 13 approved New Caledonia Region images"
  git -C "$repo" push origin "$branch"
else
  echo "No new image changes to commit."
fi
echo "13 image files checked. Draft PR remains unmerged and unpublished."
