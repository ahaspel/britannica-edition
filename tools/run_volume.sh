#!/bin/bash
set -euo pipefail

VOLUME="${1:-}"
START_PAGE="${2:-}"
END_PAGE="${3:-}"
SKIP_FETCH="${4:-}"

if [ -z "$VOLUME" ] || [ -z "$START_PAGE" ] || [ -z "$END_PAGE" ]; then
  echo "Usage: ./tools/run_volume.sh <volume> <start_page> <end_page> [--skip-fetch]"
  exit 1
fi

PADDED_VOLUME=$(printf "%02d" "$VOLUME")
RUN_DIR="data/raw/wikisource/vol${PADDED_VOLUME}_${START_PAGE}_${END_PAGE}"

EXPORT_DIR="data/derived/articles"

echo
echo "=== Wiping volume $VOLUME from database ==="
./tools/db/wipe_volume.sh "$VOLUME"

echo
echo "=== Clearing old exports ==="
mkdir -p "$EXPORT_DIR"

if [ "$SKIP_FETCH" = "--skip-fetch" ]; then
  echo
  echo "=== Skipping fetch (using cached pages in $RUN_DIR) ==="
else
  echo
  echo "=== Preparing run dir: $RUN_DIR ==="
  mkdir -p "$RUN_DIR"

  echo
  echo "=== Fetching Wikisource pages $START_PAGE-$END_PAGE for volume $VOLUME ==="
  uv run python tools/fetch/fetch_wikisource_pages.py \
    --volume "$VOLUME" \
    --start "$START_PAGE" \
    --end "$END_PAGE" \
    --outdir "$RUN_DIR"
fi

echo
echo "=== Importing fetched pages ==="
uv run python tools/fetch/import_wikisource_pages.py \
  --indir "$RUN_DIR" \
  --volume "$VOLUME"

echo
echo "=== Cleaning pages ==="
uv run britannica clean-pages "$VOLUME"

echo
echo "=== Detecting boundaries ==="
uv run britannica detect-boundaries "$VOLUME"

echo
echo "=== Classifying articles ==="
uv run britannica classify-articles "$VOLUME"

echo
echo "=== Extracting cross-references ==="
uv run britannica extract-xrefs "$VOLUME"

echo
echo "=== Resolving cross-references ==="
uv run britannica resolve-xrefs "$VOLUME"

echo
echo "=== Extracting images ==="
uv run britannica extract-images "$VOLUME"

echo
echo "=== Extracting contributors ==="
uv run britannica extract-contributors "$VOLUME"

echo
echo "=== Exporting articles ==="
uv run britannica export-articles "$VOLUME"

echo
echo "=== Done ==="
