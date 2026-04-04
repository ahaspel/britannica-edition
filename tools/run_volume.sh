#!/bin/bash
set -euo pipefail

VOLUME="${1:-}"
SKIP_FETCH=""
CLEAN_EXPORTS=""

# Check for flags anywhere in args
for arg in "$@"; do
  if [ "$arg" = "--skip-fetch" ]; then
    SKIP_FETCH="yes"
  elif [ "$arg" = "--clean-exports" ]; then
    CLEAN_EXPORTS="yes"
  fi
done

if [ -z "$VOLUME" ]; then
  echo "Usage: ./tools/run_volume.sh <volume> [--skip-fetch] [--clean-exports]"
  exit 1
fi

# Page counts per volume (from Wikisource DjVu files)
PAGE_COUNTS=(0 1029 1027 1015 1031 1002 1017 1008 1027 997 967 968 985 985 953 994 1016 1039 1000 1034 1054 1019 993 1069 1100 1090 1104 1092 1091 982)
END_PAGE=${PAGE_COUNTS[$VOLUME]:-1000}

PADDED_VOLUME=$(printf "%02d" "$VOLUME")
RUN_DIR="data/raw/wikisource/vol_${PADDED_VOLUME}"

EXPORT_DIR="data/derived/articles"

echo
echo "=== Wiping volume $VOLUME from database ==="
./tools/db/wipe_volume.sh "$VOLUME"

echo
echo "=== Clearing old exports ==="
if [ -n "$CLEAN_EXPORTS" ]; then
  echo "  Wiping entire export directory..."
  rm -rf "$EXPORT_DIR"
fi
mkdir -p "$EXPORT_DIR"

if [ -n "$SKIP_FETCH" ]; then
  echo
  echo "=== Skipping fetch (using cached pages in $RUN_DIR) ==="
else
  echo
  echo "=== Preparing run dir: $RUN_DIR ==="
  mkdir -p "$RUN_DIR"

  echo
  echo "=== Fetching Wikisource pages 1-$END_PAGE for volume $VOLUME ==="
  uv run python tools/fetch/fetch_wikisource_pages.py \
    --volume "$VOLUME" \
    --start 1 \
    --end "$END_PAGE" \
    --outdir "$RUN_DIR"
fi

echo
echo "=== Importing fetched pages ==="
uv run python tools/fetch/import_wikisource_pages.py \
  --indir "$RUN_DIR" \
  --volume "$VOLUME"

echo
echo "=== Detecting boundaries ==="
uv run britannica detect-boundaries "$VOLUME"

echo
echo "=== Transforming articles ==="
uv run britannica transform-articles "$VOLUME"

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
