#!/bin/bash
# Full rebuild of all 28 article volumes from cached wikitext.
# Wipes everything (DB, exports, S3), rebuilds from scratch,
# deploys, and runs quality analytics.
#
# Usage: ./tools/rebuild_all.sh [--no-deploy]
#
# Preserves: data/raw/wikisource/*, data/derived/quality_reports/*

set -euo pipefail

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
uv run python -c "
import sys; sys.path.insert(0, 'src')
from britannica.db.session import SessionLocal
from sqlalchemy import text
s = SessionLocal()
for table in ['article_contributors', 'article_images', 'cross_references', 'article_segments', 'articles', 'contributors', 'source_pages']:
    s.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
s.commit()
s.close()
print('  Done.')
"

echo "  Clearing exports..."
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
echo "  Done."

if [ -z "$NO_DEPLOY" ]; then
  echo "  Clearing S3 bucket..."
  aws s3 rm s3://britannica11.org/data/ --recursive --quiet
  echo "  Done."
fi

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

# --- Phase 3: Cross-volume xref resolution ---
echo
echo "=== Phase 3: Resolving cross-references across all volumes [$(elapsed)] ==="
uv run britannica resolve-xrefs-all

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
uv run python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from britannica.db.session import SessionLocal
from britannica.db.models import SourcePage
s = SessionLocal()
fm = {'dedication': {'title': 'Dedication', 'pages': [5], 'body': ''}, 'preface': {'title': 'Editorial Preface', 'author': 'Hugh Chisholm', 'date': 'December 10, 1910', 'pages': list(range(6, 24)), 'body': ''}}
p = s.query(SourcePage).filter(SourcePage.volume == 1, SourcePage.page_number == 5).first()
if p: fm['dedication']['body'] = (p.cleaned_text or p.raw_text or '').strip()
body = ''
for pg in range(6, 24):
    p = s.query(SourcePage).filter(SourcePage.volume == 1, SourcePage.page_number == pg).first()
    if not p: continue
    text = (p.cleaned_text or p.raw_text or '').strip()
    if not text: continue
    if not body:
        body = text
    elif body.endswith(('\n', '.', '!', '?', ':')):
        body = body + '\n\n' + text
    else:
        body = body + ' ' + text
fm['preface']['body'] = body
with open('data/derived/articles/front_matter.json', 'w', encoding='utf-8') as f:
    json.dump(fm, f, indent=2, ensure_ascii=False)
print('Exported front matter.')
s.close()
"

# --- Phase 6: Post-processing cleanup ---
echo
echo "=== Phase 6: Post-processing exported articles [$(elapsed)] ==="
uv run python tools/postprocess.py

# --- Phase 7: Deploy ---
if [ -z "$NO_DEPLOY" ]; then
  echo
  echo "=== Phase 7: Deploying [$(elapsed)] ==="

  echo "  Uploading articles to S3..."
  aws s3 sync "$EXPORT_DIR" s3://britannica11.org/data/

  echo "  Uploading viewer..."
  aws s3 cp tools/viewer/viewer.html s3://britannica11.org/viewer.html
  aws s3 cp tools/viewer/index.html s3://britannica11.org/index.html
  aws s3 cp tools/viewer/search.html s3://britannica11.org/search.html
  aws s3 cp tools/viewer/contributors.html s3://britannica11.org/contributors.html
  aws s3 cp tools/viewer/home.html s3://britannica11.org/home.html
  aws s3 cp tools/viewer/preface.html s3://britannica11.org/preface.html

  echo "  Invalidating CloudFront..."
  aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/*" > /dev/null

  echo "  Indexing search..."
  MEILI_URL="${MEILI_URL:-https://britannica11.org/search-api}" \
  MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-}" \
    uv run python tools/index_search.py

  echo "  Deploy complete."
else
  echo
  echo "=== Skipping deploy (--no-deploy) ==="
fi

# --- Phase 8: Quality analytics ---
echo
echo "=== Phase 8: Running quality report [$(elapsed)] ==="
uv run python tools/quality_report.py

echo
echo "============================================"
echo "  Rebuild complete. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
