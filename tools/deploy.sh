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

# BUILD WHAT WE SHIP, at ship time — the same argument the corpus fingerprint
# below makes for itself.  The sampler used to be uploaded from whatever happened
# to be on disk, and drifted four days behind the corpus it sits beside on the
# download page: built Aug 16, shipped Aug 19 next to a corpus carrying 31 source
# corrections and five producer fixes it did not contain, under a freshly
# computed sha256 that made it look current.
#
# FIRST, before any upload: the build carries hard gates (every article anchored
# once, no duplicate ids, every href resolves, per-chunk text preservation) and
# `set -e` aborts on them — and aborting before the first `aws s3` call is what
# keeps a failed sampler from becoming a partial deploy.  ~80s.
# BEFORE ANYTHING ELSE: is this corpus the output of a rebuild that finished its
# gates, and has anything written to it since?  The header above asks a human to
# run this "ONLY right after a clean FULL rebuild you have reviewed" — an
# instruction judged in the moment by whoever wants to ship.  This is that
# instruction as a check.  ~40ms.
echo "  Verifying the corpus against the last completed rebuild..."
uv run python tools/diagnostics/corpus_stamp.py --check

echo "  Building vol-1 sampler EPUB [$(elapsed)]..."
uv run python -m britannica.epub.build --volume 1 --out eb1911-vol01.epub

echo "  Uploading articles to S3..."
# Cache policy is load-bearing here: article JSONs are content-addressed ({hash}.json,
# immutable — a hash's bytes never change) so they cache hard; but index.json /
# contributors.json are rewritten every deploy, so they MUST revalidate (no-cache).
# Shipping them cacheable is what broke navigation for returning users on 2026-07-15: browsers held
# the pre-deploy index/contributors and resolved every link to a now-deleted old filename.
aws s3 sync "$EXPORT_DIR" s3://britannica11.org/data/articles/ --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.json" --exclude "contributors.json"
# index.json (~18.6MB) exceeds CloudFront's 10MB on-the-fly gzip cap, so it was
# shipping RAW — an 18.6MB download on the render path of the index page + the
# typeahead everywhere (~3s at 50Mbps).  Pre-compress it: a stored gzip object
# is not subject to the size cap, Content-Encoding: gzip is honoured by every
# HTTP client, and fetch().json() decompresses transparently — no viewer change.
# ~18.6MB -> ~2.6MB.  Keeps no-cache (the object is still rewritten every deploy).
gzip -9 -c "$EXPORT_DIR/index.json" > "$EXPORT_DIR/index.json.gz"
aws s3 cp "$EXPORT_DIR/index.json.gz" s3://britannica11.org/data/articles/index.json \
  --cache-control "no-cache" --content-type "application/json" \
  --content-encoding "gzip"
rm -f "$EXPORT_DIR/index.json.gz"
# contributors.json (1.9MB) is under the cap → CloudFront already brotli's it.
aws s3 cp "$EXPORT_DIR/contributors.json" s3://britannica11.org/data/articles/contributors.json \
  --cache-control "no-cache" --content-type "application/json"

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

echo "  Uploading derived JSON (printed pages, scan map, classified TOC) — no-cache..."
# Regenerated every deploy and read client-side to build links/pages, so they MUST
# revalidate (no-cache) — a stale copy of these is how returning users broke on 2026-07-15.
for j in printed_pages printed_pages_leaf scan_map classified_toc fm_first_content volumes; do
  aws s3 cp "data/derived/$j.json" "s3://britannica11.org/data/$j.json" \
    --content-type "application/json" --cache-control "no-cache"
done
# maps.json is hand-curated source (lives at data/maps.json, not data/derived/)
aws s3 cp data/maps.json s3://britannica11.org/data/maps.json \
  --content-type "application/json" --cache-control "no-cache"

echo "  Uploading download bundle (agent JSONL + graphs)..."
aws s3 cp data/derived/eb1911-corpus.tar.gz s3://britannica11.org/download/eb1911-corpus.tar.gz
aws s3 cp data/derived/eb1911-corpus.tar.gz.sha256 s3://britannica11.org/download/eb1911-corpus.tar.gz.sha256
aws s3 cp data/derived/eb1911-maps.tar.gz s3://britannica11.org/download/eb1911-maps.tar.gz
aws s3 cp data/derived/eb1911-maps.tar.gz.sha256 s3://britannica11.org/download/eb1911-maps.tar.gz.sha256
echo "  Uploading vol-1 sampler EPUB (built above)..."
sha256sum eb1911-vol01.epub | awk '{print $1}' > eb1911-vol01.epub.sha256
aws s3 cp eb1911-vol01.epub s3://britannica11.org/download/eb1911-vol01.epub
aws s3 cp eb1911-vol01.epub.sha256 s3://britannica11.org/download/eb1911-vol01.epub.sha256
aws s3 cp data/derived/download/manifest.json s3://britannica11.org/download/manifest.json
aws s3 cp data/derived/download/README.md s3://britannica11.org/download/README.md

# Regenerate the corpus fingerprint HERE, immediately before shipping it, so the
# stamp provably describes the bytes this deploy uploaded.  Generating it only in
# the rebuild would let a deploy run against a corpus changed since — and because
# this script has no `set -e`, a missing or stale stamp would not stop the
# deploy: S3 would keep the PREVIOUS stamp, pinning every reader to the previous
# build's `?v=` and restoring the exact immutable-cache staleness the stamp
# exists to defeat.  It costs ~5s and is deterministic, so running it twice
# (rebuild + here) yields the same value.
echo "  Stamping corpus fingerprint..."
uv run python tools/viewer/build_stamp.py || {
  echo "FATAL: could not stamp the corpus fingerprint — refusing to deploy," >&2
  echo "       because shipping the previous stamp silently serves stale articles." >&2
  exit 1
}

echo "  Uploading viewer (HTML + JS = no-cache; content isn't hashed yet, so revalidate)..."
# HTML shell + generated pages: no-cache so a deploy is never served stale. A cached shell/JS
# against a fresh corpus resolves every link to a deleted old filename — the 2026-07-15 regression.
# (The heavy stuff — article JSONs, images, scans — still caches hard; only these small files
# revalidate. Permanent fix is content-hashed asset names → immutable; see the queued item.)
for f in viewer index search scans maps contributors home preface topics \
         ancillary ancillary-prefatory-note ancillary-index-preface ancillary-abbreviations \
         about download; do
  aws s3 cp "tools/viewer/$f.html" "s3://britannica11.org/$f.html" \
    --content-type "text/html; charset=utf-8" --cache-control "no-cache"
done
# build-stamp.js carries the corpus fingerprint the viewer appends to article
# fetches as `?v=`.  It MUST stay no-cache: a stale stamp would keep pointing at
# the previous build's URL, which is precisely the immutable-cache staleness the
# stamp exists to defeat.
for f in search-api article-urls typeahead gc-gate build-stamp; do
  aws s3 cp "tools/viewer/$f.js" "s3://britannica11.org/$f.js" \
    --content-type "application/javascript" --cache-control "no-cache"
done
aws s3 cp tools/viewer/favicon.svg s3://britannica11.org/favicon.svg \
  --content-type "image/svg+xml" --cache-control "public, max-age=86400"

echo "  Uploading Reader's Guide (72 pages + 1 image)..."
for f in tools/viewer/readers-guide.html \
         tools/viewer/readers-guide-part-*.html \
         tools/viewer/readers-guide-ch*.html; do
  aws s3 cp "$f" "s3://britannica11.org/$(basename "$f")" \
    --content-type "text/html; charset=utf-8" \
    --cache-control "no-cache"
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

# --- HuggingFace dataset mirror (folded in; best-effort, NON-FATAL) ---
# One command instead of a forgotten second step.  Kept non-fatal because the
# SITE is already live by this point — an HF auth/network hiccup must never fail
# a deploy whose site push already succeeded.  `--with huggingface_hub` supplies
# the package; auth is a cached `hf auth login` (WRITE token) or $HF_TOKEN.
echo
echo "=== HuggingFace dataset mirror [$(elapsed)] ==="
if uv run --with huggingface_hub python tools/publish_hf.py britannica11/eb1911; then
  echo "  HuggingFace mirror updated."
else
  echo "  WARNING: HuggingFace publish failed — the site deploy above still SUCCEEDED."
  echo "  Auth once with a WRITE token, then run just the publish (no full redeploy):"
  echo "    uv run --with huggingface_hub hf auth login   # --force to replace a read-only token"
  echo "    uv run --with huggingface_hub python tools/publish_hf.py britannica11/eb1911"
fi

echo
echo "============================================"
echo "  Deploy finished. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
