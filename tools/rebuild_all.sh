#!/bin/bash
# Full rebuild of all 28 article volumes from cached wikitext.
# Wipes everything (DB, exports, S3), rebuilds from scratch,
# deploys, and runs quality analytics.
#
# Usage: ./tools/rebuild_all.sh [--no-deploy]
#
# Preserves: data/raw/wikisource/*, data/derived/quality_reports/*

set -euo pipefail

# Truncate the log file so old output doesn't cause confusion
: > rebuild.log 2>/dev/null || true

# Ensure required services are running
echo "Checking services..."
if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qi postgres; then
  echo "  PostgreSQL not running. Starting services..."
  ./tools/pipeline/start_services.sh
fi
uv run python tools/db/check_connection.py

VOLUMES=$(seq 1 28)
EXPORT_DIR="data/derived/articles"
BUILD_START=$(date +%s)
NO_DEPLOY=""

for arg in "$@"; do
  if [ "$arg" = "--no-deploy" ]; then
    NO_DEPLOY="yes"
  fi
done

elapsed() {
  local now=$(date +%s)
  local secs=$((now - BUILD_START))
  printf "%d:%02d" $((secs / 60)) $((secs % 60))
}

echo "============================================"
echo "  Full rebuild: volumes 1-28"
echo "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo

# --- Phase 1: Clean everything ---
echo "=== Phase 1: Cleaning everything [$(elapsed)] ==="

echo "  Truncating database..."
uv run python tools/db/truncate_all.py

echo "  Verifying..."
uv run python tools/db/verify_empty.py

echo "  Clearing exports..."
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
echo "  Done."

  # Note: S3 bucket is NOT cleared here — s3 sync --delete in Phase 7
  # handles cleanup. This keeps the site live during the rebuild.

# --- Phase 1b: Build contributor table from front matter ---
echo
echo "=== Phase 1b: Building contributor table [$(elapsed)] ==="
uv run python tools/pipeline/build_contributor_table.py

# --- Phase 2: Per-volume pipeline ---
echo
echo "=== Phase 2: Running pipeline for each volume ==="
for vol in $VOLUMES; do
  PADDED=$(printf "%02d" "$vol")
  RUN_DIR="data/raw/wikisource/vol_${PADDED}"

  echo
  echo "--- Volume $vol [$(elapsed)] ---"

  echo "  Importing pages..."
  uv run python tools/fetch/import_wikisource_pages.py \
    --indir "$RUN_DIR" \
    --volume "$vol"

  echo "  Detecting boundaries..."
  uv run britannica detect-boundaries "$vol"

  echo "  Transforming articles..."
  uv run britannica transform-articles "$vol"

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

  echo "  Volume $vol complete. [$(elapsed)]"
done

# --- Phase 3: Cross-volume resolution ---
echo
echo "=== Phase 3a: Resolving cross-references across all volumes [$(elapsed)] ==="
uv run britannica resolve-xrefs-all

echo
echo "=== Phase 3b: Linking contributors from front matter [$(elapsed)] ==="
uv run python tools/pipeline/link_contributors_from_frontmatter.py


# --- Phase 4: Re-export (xref targets now resolved cross-volume) ---
echo
echo "=== Phase 4: Re-exporting all volumes (with resolved xrefs) [$(elapsed)] ==="
for vol in $VOLUMES; do
  echo "  Re-exporting volume $vol..."
  uv run britannica export-articles "$vol"
done

# --- Phase 5: Export front matter ---
echo
echo "=== Phase 5: Exporting front matter [$(elapsed)] ==="
uv run python tools/pipeline/export_front_matter.py

# --- Phase 6: Post-processing cleanup ---
echo
echo "=== Phase 6: Post-processing exported articles [$(elapsed)] ==="
uv run python tools/pipeline/postprocess.py

# --- Phase 6b: Build classified TOC (topics page data) ---
echo
echo "=== Phase 6b: Parsing classified TOC (vol 29 topics) [$(elapsed)] ==="
uv run python tools/vol29/parse_classified_toc.py

# --- Phase 6c: Detect first-content fm scan per volume ---
echo
echo "=== Phase 6c: Detecting fm first-content pages [$(elapsed)] ==="
uv run python tools/diagnostics/detect_fm_blank_pages.py

# --- Phase 6d: Rebuild generated site pages (article IDs change) ---
echo
echo "=== Phase 6d: Rebuilding generated site pages [$(elapsed)] ==="
uv run python tools/viewer/build_about_page.py
uv run python tools/viewer/build_ancillary_pages.py

# --- Phase 7: Deploy ---
if [ -z "$NO_DEPLOY" ]; then
  echo
  echo "=== Phase 7: Deploying [$(elapsed)] ==="

  echo "  Uploading articles to S3..."
  aws s3 sync "$EXPORT_DIR" s3://britannica11.org/data/articles/ --delete

  # Images and scans are static assets — upload separately with:
  #   aws s3 sync data/derived/images/ s3://britannica11.org/data/images/ --size-only
  #   aws s3 sync data/derived/scans/ s3://britannica11.org/data/scans/ --size-only

  echo "  Uploading derived JSON (printed pages, scan map, classified TOC)..."
  aws s3 cp data/derived/printed_pages.json s3://britannica11.org/data/printed_pages.json
  aws s3 cp data/derived/printed_pages_leaf.json s3://britannica11.org/data/printed_pages_leaf.json
  aws s3 cp data/derived/scan_map.json s3://britannica11.org/data/scan_map.json
  aws s3 cp data/derived/classified_toc.json s3://britannica11.org/data/classified_toc.json
  aws s3 cp data/derived/fm_first_content.json s3://britannica11.org/data/fm_first_content.json

  echo "  Uploading viewer..."
  aws s3 cp tools/viewer/viewer.html s3://britannica11.org/viewer.html
  aws s3 cp tools/viewer/index.html s3://britannica11.org/index.html
  aws s3 cp tools/viewer/search.html s3://britannica11.org/search.html
  aws s3 cp tools/viewer/scans.html s3://britannica11.org/scans.html
  aws s3 cp tools/viewer/contributors.html s3://britannica11.org/contributors.html
  aws s3 cp tools/viewer/home.html s3://britannica11.org/home.html
  aws s3 cp tools/viewer/preface.html s3://britannica11.org/preface.html
  aws s3 cp tools/viewer/topics.html s3://britannica11.org/topics.html
  aws s3 cp tools/viewer/ancillary.html s3://britannica11.org/ancillary.html
  aws s3 cp tools/viewer/ancillary-prefatory-note.html s3://britannica11.org/ancillary-prefatory-note.html
  aws s3 cp tools/viewer/ancillary-index-preface.html s3://britannica11.org/ancillary-index-preface.html
  aws s3 cp tools/viewer/ancillary-abbreviations.html s3://britannica11.org/ancillary-abbreviations.html
  aws s3 cp tools/viewer/about.html s3://britannica11.org/about.html

  echo "  Invalidating CloudFront..."
  aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/*" > /dev/null

  echo "  Indexing search (via EC2)..."
  EC2_HOST="ec2-44-222-119-72.compute-1.amazonaws.com"
  EC2_KEY="${EC2_KEY:-D:/work/web/cloudinstall/britannica11.pem}"
  ssh -i "$EC2_KEY" ec2-user@"$EC2_HOST" \
    "aws s3 sync s3://britannica11.org/data/articles/ ~/articles/ --delete --quiet && python3 ~/index_search_ec2.py"

  echo "  Deploy complete."
else
  echo
  echo "=== Skipping deploy (--no-deploy) ==="
fi

# --- Phase 8: Quality analytics ---
echo
echo "=== Phase 8: Running quality report [$(elapsed)] ==="
uv run python tools/diagnostics/quality_report.py

echo
echo "============================================"
echo "  Rebuild complete. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
