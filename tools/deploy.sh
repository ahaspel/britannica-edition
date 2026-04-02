#!/bin/bash
# Deploy the Britannica edition to production.
#
# Usage: ./tools/deploy.sh [--skip-upload] [--skip-search]
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - S3 bucket exists at data.britannica11.org
#   - Meilisearch running at search.britannica11.org
#
# What this does:
#   1. Uploads article JSONs + metadata to S3
#   2. Uploads viewer HTML files to S3 (or a separate bucket)
#   3. Indexes articles in production Meilisearch
#   4. Invalidates CloudFront cache

set -euo pipefail

BUCKET="britannica11.org"
CLOUDFRONT_DIST_ID="${CLOUDFRONT_DIST_ID:-}"
MEILI_URL="${MEILI_URL:-https://britannica11.org/search-api}"
MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-}"

SKIP_UPLOAD=""
SKIP_SEARCH=""

for arg in "$@"; do
  case "$arg" in
    --skip-upload) SKIP_UPLOAD=yes ;;
    --skip-search) SKIP_SEARCH=yes ;;
  esac
done

echo "============================================"
echo "  Deploying to britannica11.org"
echo "============================================"
echo

# --- Verify local data exists ---
ARTICLE_COUNT=$(ls data/derived/articles/*.json 2>/dev/null | grep -v index.json | grep -v contributors.json | wc -l)
if [ "$ARTICLE_COUNT" -lt 1000 ]; then
  echo "ERROR: Only $ARTICLE_COUNT article files found. Run tools/rebuild_all.sh first."
  exit 1
fi
echo "Found $ARTICLE_COUNT article files."

# --- Upload data to S3 ---
if [ -z "$SKIP_UPLOAD" ]; then
  echo
  echo "=== Uploading article data to s3://$BUCKET/data/ ==="
  aws s3 sync data/derived/articles/ "s3://$BUCKET/data/" \
    --delete \
    --content-type "application/json" \
    --cache-control "public, max-age=3600"

  echo
  echo "=== Uploading volumes.json ==="
  aws s3 cp data/derived/volumes.json "s3://$BUCKET/data/volumes.json" \
    --content-type "application/json" \
    --cache-control "public, max-age=3600"

  echo
  echo "=== Uploading viewer files ==="
  # Upload title page image
  aws s3 cp "tools/viewer/title_page.jpg" "s3://$BUCKET/title_page.jpg" \
    --content-type "image/jpeg" \
    --cache-control "public, max-age=86400"

  for f in home.html index.html viewer.html search.html contributors.html preface.html about.html; do
    aws s3 cp "tools/viewer/$f" "s3://$BUCKET/$f" \
      --content-type "text/html" \
      --cache-control "public, max-age=300"
  done

  echo "  Upload complete."
else
  echo "Skipping upload (--skip-upload)."
fi

# --- Invalidate CloudFront cache ---
if [ -n "$CLOUDFRONT_DIST_ID" ] && [ -z "$SKIP_UPLOAD" ]; then
  echo
  echo "=== Invalidating CloudFront cache ==="
  aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DIST_ID" \
    --paths "/*" > /dev/null
  echo "  Invalidation submitted."
else
  if [ -z "$CLOUDFRONT_DIST_ID" ]; then
    echo "  Skipping CloudFront invalidation (CLOUDFRONT_DIST_ID not set)."
  fi
fi

# --- Index Meilisearch ---
if [ -z "$SKIP_SEARCH" ]; then
  if [ -z "$MEILI_MASTER_KEY" ]; then
    echo
    echo "WARNING: MEILI_MASTER_KEY not set. Skipping search indexing."
    echo "  Set it and re-run with: MEILI_MASTER_KEY=yourkey ./tools/deploy.sh --skip-upload"
  else
    echo
    echo "=== Indexing articles in Meilisearch ==="
    MEILI_URL="$MEILI_URL" MEILI_MASTER_KEY="$MEILI_MASTER_KEY" \
      uv run python tools/index_search.py
    echo "  Indexing complete."
  fi
else
  echo "Skipping search indexing (--skip-search)."
fi

echo
echo "============================================"
echo "  Deploy complete."
echo "  Site: https://britannica11.org"
echo "============================================"
