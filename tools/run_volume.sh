#!/bin/bash
set -euo pipefail

VOLUME="${1:-}"
START_PAGE="${2:-}"
END_PAGE="${3:-}"

if [ -z "$VOLUME" ] || [ -z "$START_PAGE" ] || [ -z "$END_PAGE" ]; then
  echo "Usage: ./tools/run_volume.sh <volume> <start_page> <end_page>"
  exit 1
fi

PADDED_VOLUME=$(printf "%02d" "$VOLUME")
RUN_DIR="data/raw/wikisource/vol${PADDED_VOLUME}_${START_PAGE}_${END_PAGE}"

echo
echo "=== Wiping volume $VOLUME ==="
./tools/db/wipe_volume.sh "$VOLUME"

echo
echo "=== Preparing run dir: $RUN_DIR ==="
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR"

echo
echo "=== Fetching Wikisource pages $START_PAGE-$END_PAGE for volume $VOLUME ==="
uv run python tools/fetch/fetch_wikisource_pages.py \
  --volume "$VOLUME" \
  --start "$START_PAGE" \
  --end "$END_PAGE" \
  --outdir "$RUN_DIR"

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
echo "=== Exporting articles ==="
uv run britannica export-articles "$VOLUME"

echo
echo "=== Done ==="