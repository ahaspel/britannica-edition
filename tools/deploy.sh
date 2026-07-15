#!/bin/bash
# Deploy the ALREADY-BUILT corpus + viewer to production (britannica11.org).
#
# This is Phase 7 + Phase 9 of rebuild_all.sh, extracted so a local `--no-deploy`
# build can be reviewed and THEN shipped with one fast command — without rebuilding.
# It pushes whatever is currently in data/derived/ and tools/viewer/, so run it ONLY
# right after a clean FULL rebuild you have reviewed: a partial or stale tree here is
# exactly the "partial deploy" the project forbids ([[feedback_never_partial_rebuild]]).
# `rebuild_all.sh --deploy` calls this at the end; it is also safe to run standalone.
#
# NOTE: the CloudFront /article/* router function (tools/cloudfront/article-router.js) is
# managed on the distribution separately — update it in the CloudFront console/CLI when it
# changes; it is not part of this asset push.
#
# Usage: ./tools/deploy.sh
set -euo pipefail
export PYTHONIOENCODING=utf-8

EXPORT_DIR="data/derived/articles"
START=$(date +%s)
elapsed() { local s=$(( $(date +%s) - START )); printf "%d:%02d" $((s/60)) $((s%60)); }

echo "============================================"
echo "  Deploy to britannica11.org"
echo "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

echo "  Uploading articles to S3..."
aws s3 sync "$EXPORT_DIR" s3://britannica11.org/data/articles/ --delete

# Images and scans are static assets.  Always upload with a sensible
# Cache-Control so a re-uploaded scan (splice, vol-20 quality swap)
# actually reaches users in their normal browser windows on the next
# page load.  Without this header browsers fall back to heuristic
# freshness and serve the OLD bytes for hours after a CloudFront
# invalidation has already refreshed the CDN.
echo "  Uploading images to S3..."
# Don't pass --content-type for the images dir — files are mixed
# jpg/png/gif and the sync command would force one type for all.
# aws s3 sync auto-detects content-type from extension by default.
aws s3 sync data/images/ s3://britannica11.org/data/images/ \
  --size-only \
  --cache-control "public, max-age=300, must-revalidate"
echo "  Uploading scans to S3..."
aws s3 sync data/derived/scans/ s3://britannica11.org/data/scans/ \
  --size-only \
  --cache-control "public, max-age=300, must-revalidate" \
  --content-type "image/jpeg"

echo "  Uploading derived JSON (printed pages, scan map, classified TOC)..."
aws s3 cp data/derived/printed_pages.json s3://britannica11.org/data/printed_pages.json
aws s3 cp data/derived/printed_pages_leaf.json s3://britannica11.org/data/printed_pages_leaf.json
aws s3 cp data/derived/scan_map.json s3://britannica11.org/data/scan_map.json
aws s3 cp data/derived/classified_toc.json s3://britannica11.org/data/classified_toc.json
aws s3 cp data/derived/fm_first_content.json s3://britannica11.org/data/fm_first_content.json
aws s3 cp data/derived/volumes.json s3://britannica11.org/data/volumes.json

echo "  Uploading download bundle (agent JSONL + graphs)..."
aws s3 cp data/derived/eb1911-corpus.tar.gz s3://britannica11.org/download/eb1911-corpus.tar.gz
aws s3 cp data/derived/eb1911-corpus.tar.gz.sha256 s3://britannica11.org/download/eb1911-corpus.tar.gz.sha256
aws s3 cp data/derived/download/manifest.json s3://britannica11.org/download/manifest.json
aws s3 cp data/derived/download/README.md s3://britannica11.org/download/README.md

echo "  Uploading viewer..."
aws s3 cp tools/viewer/viewer.html s3://britannica11.org/viewer.html
aws s3 cp tools/viewer/index.html s3://britannica11.org/index.html
aws s3 cp tools/viewer/search.html s3://britannica11.org/search.html
aws s3 cp tools/viewer/scans.html s3://britannica11.org/scans.html
aws s3 cp tools/viewer/search-api.js s3://britannica11.org/search-api.js
aws s3 cp tools/viewer/article-urls.js s3://britannica11.org/article-urls.js
aws s3 cp tools/viewer/typeahead.js s3://britannica11.org/typeahead.js
aws s3 cp tools/viewer/favicon.svg s3://britannica11.org/favicon.svg --content-type "image/svg+xml"
aws s3 cp tools/viewer/contributors.html s3://britannica11.org/contributors.html
aws s3 cp tools/viewer/home.html s3://britannica11.org/home.html
aws s3 cp tools/viewer/preface.html s3://britannica11.org/preface.html
aws s3 cp tools/viewer/topics.html s3://britannica11.org/topics.html
aws s3 cp tools/viewer/ancillary.html s3://britannica11.org/ancillary.html
aws s3 cp tools/viewer/ancillary-prefatory-note.html s3://britannica11.org/ancillary-prefatory-note.html
aws s3 cp tools/viewer/ancillary-index-preface.html s3://britannica11.org/ancillary-index-preface.html
aws s3 cp tools/viewer/ancillary-abbreviations.html s3://britannica11.org/ancillary-abbreviations.html
aws s3 cp tools/viewer/about.html s3://britannica11.org/about.html
aws s3 cp tools/viewer/download.html s3://britannica11.org/download.html

echo "  Uploading Reader's Guide (72 pages + 1 image)..."
for f in tools/viewer/readers-guide.html \
         tools/viewer/readers-guide-part-*.html \
         tools/viewer/readers-guide-ch*.html; do
  aws s3 cp "$f" "s3://britannica11.org/$(basename "$f")" \
    --content-type "text/html; charset=utf-8" \
    --cache-control "public, max-age=300"
done
aws s3 cp tools/viewer/readers-guide-i_008.jpg s3://britannica11.org/readers-guide-i_008.jpg

echo "  Invalidating CloudFront..."
aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/*" > /dev/null

echo "  Indexing search (via EC2)..."
EC2_HOST="ec2-44-222-119-72.compute-1.amazonaws.com"
EC2_KEY="${EC2_KEY:-D:/work/web/cloudinstall/britannica11.pem}"
# Ship the indexer AND markers.py (pure-stdlib) so the EC2 copies match the
# repo and index_search_ec2.py imports the SAME marker->text converter the
# export uses — one definition, no drifting EC2 copy of the strip logic.
scp -i "$EC2_KEY" \
  tools/pipeline/index_search_ec2.py \
  src/britannica/markers.py \
  ec2-user@"$EC2_HOST":~/
ssh -i "$EC2_KEY" ec2-user@"$EC2_HOST" \
  "aws s3 sync s3://britannica11.org/data/articles/ ~/articles/ --delete --quiet && python3 ~/index_search_ec2.py"

echo "  Deploy complete. [$(elapsed)]"

# --- Deploy preflight (was Phase 9) ---
# Verify every asset referenced by the viewer HTML is reachable on
# britannica11.org.  Catches the "shipped HTML that references a file we forgot
# to upload" bug class (the article-urls.js near-miss on 2026-04-22).  set -e
# ensures the success banner below is not printed if a reference is missing.
echo
echo "=== Deploy preflight [$(elapsed)] ==="
uv run python tools/diagnostics/check_deploy_refs.py

echo
echo "============================================"
echo "  Deploy finished. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
