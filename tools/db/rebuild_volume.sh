#!/bin/bash
# Full per-volume rebuild for local iteration: wipes the volume's DB
# rows AND its exported article JSON files, then runs the per-volume
# stages of `rebuild_all.sh`'s Phase 2, finishing with a quality
# report.  No deploy — produces fresh data/derived/articles/${VOL}-*
# JSONs for spot-checking in the local viewer.
#
# Guarantees a clean baseline per [[feedback_clean_baseline_required]]:
# wipes both DB and disk so post-run metrics reflect only this run.
#
# Usage:  ./tools/db/rebuild_volume.sh <volume>
#         (output streams to stdout; redirect to a file if you want a log)
set -euo pipefail

VOLUME=${1:-}
if [ -z "$VOLUME" ]; then
  echo "Usage: ./tools/db/rebuild_volume.sh <volume>"
  exit 1
fi
PADDED=$(printf "%02d" "$VOLUME")

echo "=== rebuild vol $VOLUME start $(date '+%H:%M:%S') ==="

echo "Wiping DB rows for vol $VOLUME..."
./tools/db/wipe_volume.sh "$VOLUME"

# The book's output root, asserted non-empty before it reaches `rm`.
DERIVED=$(uv run python -m britannica.corpora derived)
: "${DERIVED:?the book did not name its output root}"
echo "Wiping $DERIVED/articles/${PADDED}-*.json..."
shopt -s nullglob
rm -f "$DERIVED"/articles/${PADDED}-*.json
shopt -u nullglob

uv run python tools/fetch/import_wikisource_pages.py \
    --indir "data/raw/wikisource/vol_${PADDED}" --volume "$VOLUME"
uv run britannica detect-boundaries "$VOLUME"
uv run britannica extract-contributors "$VOLUME"
uv run britannica export-articles "$VOLUME"

echo "=== pipeline done $(date '+%H:%M:%S') ==="
echo "Running quality_report..."
uv run python tools/diagnostics/quality_report.py
echo "=== rebuild vol $VOLUME complete $(date '+%H:%M:%S') ==="
