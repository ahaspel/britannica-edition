#!/bin/bash
# Full rebuild of all 28 article volumes from cached wikitext.
# Wipes DB and exports, runs every pipeline stage, resolves
# cross-volume xrefs, re-exports, and runs quality analytics.
#
# Usage: ./tools/rebuild_all.sh
#
# Preserves: data/raw/wikisource/*, data/derived/quality_reports/*

set -euo pipefail

VOLUMES=$(seq 1 28)
EXPORT_DIR="data/derived/articles"

echo "============================================"
echo "  Full rebuild: volumes 1-28"
echo "============================================"
echo

# --- Phase 1: Wipe everything ---
echo "=== Phase 1: Wiping all volumes from database ==="
for vol in $VOLUMES; do
  echo "  Wiping volume $vol..."
  ./tools/db/wipe_volume.sh "$vol" > /dev/null 2>&1
done
echo "  Done."

echo
echo "=== Clearing exported articles ==="
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
echo "  Done."

# --- Phase 2: Per-volume pipeline ---
echo
echo "=== Phase 2: Running pipeline for each volume ==="
for vol in $VOLUMES; do
  PADDED=$(printf "%02d" "$vol")
  RUN_DIR="data/raw/wikisource/vol_${PADDED}"

  echo
  echo "--- Volume $vol ---"

  echo "  Importing pages..."
  uv run python tools/fetch/import_wikisource_pages.py \
    --indir "$RUN_DIR" \
    --volume "$vol"

  echo "  Cleaning pages..."
  uv run britannica clean-pages "$vol"

  echo "  Detecting boundaries..."
  uv run britannica detect-boundaries "$vol"

  echo "  Classifying articles..."
  uv run britannica classify-articles "$vol"

  echo "  Extracting cross-references..."
  uv run britannica extract-xrefs "$vol"

  echo "  Resolving cross-references (intra-volume)..."
  uv run britannica resolve-xrefs "$vol"

  echo "  Extracting images..."
  uv run britannica extract-images "$vol"

  echo "  Extracting contributors..."
  uv run britannica extract-contributors "$vol"

  echo "  Exporting articles..."
  uv run britannica export-articles "$vol"

  echo "  Volume $vol complete."
done

# --- Phase 3: Cross-volume xref resolution ---
echo
echo "=== Phase 3: Resolving cross-references across all volumes ==="
uv run britannica resolve-xrefs-all

# --- Phase 4: Re-export (xref targets now resolved cross-volume) ---
echo
echo "=== Phase 4: Re-exporting all volumes (with resolved xrefs) ==="
for vol in $VOLUMES; do
  echo "  Re-exporting volume $vol..."
  uv run britannica export-articles "$vol"
done

# --- Phase 5: Reindex search ---
echo
echo "=== Phase 5: Reindexing Meilisearch ==="
uv run python tools/index_search.py

# --- Phase 6: Quality analytics ---
echo
echo "=== Phase 6: Running quality report ==="
uv run python tools/quality_report.py

echo
echo "============================================"
echo "  Rebuild complete."
echo "============================================"
