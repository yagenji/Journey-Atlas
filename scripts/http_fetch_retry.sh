#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <url> <output-file>" >&2
  exit 2
fi

url="$1"
output="$2"

curl -fsS \
  --retry 4 \
  --retry-all-errors \
  --retry-delay 2 \
  --connect-timeout 10 \
  --max-time 30 \
  -H 'Cache-Control: no-cache' \
  "$url" \
  -o "$output"
