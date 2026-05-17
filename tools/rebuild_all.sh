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

# --- Phase 1c: Apply vol 29 contributor linker ---
# Adds contributors that vol 29's master Index lists but per-volume
# tables don't, plus paired re-keys / duplicate-initials resolutions.
# Must run AFTER 1b (so the linker sees the post-corrections.json
# contributor table) and BEFORE Phase 2's extract-contributors (so
# the per-volume footer matcher sees the new ContributorInitials
# rows).  Conservative: NEEDS_REVIEW items are reported but not
# auto-applied.
echo
echo "=== Phase 1c: Applying vol 29 contributor linker [$(elapsed)] ==="
uv run python tools/pipeline/link_vol29_contributors.py --apply

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

  echo "  Preparing wikitext (corrections.json + quote-run conversion)..."
  uv run britannica prepare-wikitext "$vol"

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

# --- Phase 3b2: Link vol 29 master-Index article attributions ---
# Per-volume front matter doesn't list vol-29-only contributors (the
# Phase 1c INSERTs), and many of their attributed articles have no
# `(initials)` footer signature — so without this step they ship as
# orphans (no ArticleContributor rows) and get filtered out of
# contributors.json.  Must run AFTER Phase 3b so we only fill
# contributors who are still genuinely orphaned.
echo
echo "=== Phase 3b2: Linking vol 29 article attributions [$(elapsed)] ==="
uv run python tools/pipeline/link_vol29_articles.py --apply


# --- Phase 3c: Rebuild printed-page mapping (ws→printed / leaf→printed) ---
# MUST run before Phase 4's re-export: the article exporter consults
# printed_pages.json to translate each segment's ws-space PAGE marker
# into its printed-page number.  If this runs AFTER the exports (as it
# used to, in old Phase 6e), every rebuild ships with stale mappings —
# visible on SHIPBUILDING where page markers ran past the article's last
# printed page (981) into the next article's numbering (982+).
echo
echo "=== Phase 3c: Rebuilding printed-page mapping [$(elapsed)] ==="
uv run python tools/pipeline/build_printed_pages.py

# --- Phase 3d: Snapshot article index for cross-rebuild diff ---
# `data/derived/article_index.tsv` is a TSV (vol, page_start,
# page_end, article_type, title) sorted by (volume, page_start,
# title).  Commit it to git after each rebuild and `git log -p` on
# it shows article-list churn between rebuilds — catches "we lost N
# articles" regressions like the 2026-05-16 missing-33 incident
# where we had no way to identify which articles disappeared.
echo
echo "=== Phase 3d: Snapshot article index [$(elapsed)] ==="
uv run python tools/diagnostics/snapshot_article_index.py

# --- Phase 4: Re-export (xref targets now resolved cross-volume) ---
echo
echo "=== Phase 4: Re-exporting all volumes (with resolved xrefs) [$(elapsed)] ==="
for vol in $VOLUMES; do
  echo "  Re-exporting volume $vol..."
  uv run britannica export-articles "$vol"
done

# --- Phase 4b: Measure math widths (refresh scale-hint cache) ---
# Renders every unique display-mode `«MATH:` marker in the exported
# corpus through KaTeX in a headless browser and records the smallest
# font-size that fits the body-text column.  Cached at
# data/derived/math_widths.json (hash-keyed) — only NEW LaTeX gets
# re-measured.  See tools/diagnostics/measure_math_widths.py.
echo
echo "=== Phase 4b: Measuring math widths [$(elapsed)] ==="
uv run python tools/diagnostics/measure_math_widths.py

# --- Phase 4c: Annotate math markers with refreshed hints ---
# Walks every article JSON and rewrites `«MATH:` markers with the
# `[fs=N]` / `[popout]` annotation drawn from the just-refreshed
# cache.  Pure text transform — no re-rendering required.  Lets the
# rebuild emerge with every math marker correctly hinted, even
# though Phase 4's export ran with a (potentially) stale cache for
# newly added or changed LaTeX.
echo
echo "=== Phase 4c: Annotating math markers [$(elapsed)] ==="
uv run python tools/pipeline/annotate_math_markers.py

# --- Phase 6b: Build classified TOC (topics page data) ---
echo
echo "=== Phase 6b: Parsing classified TOC (vol 29 topics) [$(elapsed)] ==="
uv run python tools/vol29/parse_classified_toc.py

# --- Phase 6b2: Apply cached topic-disambiguation choices ---
# parse_classified_toc.py picks one article per ambiguous index entry
# (e.g. ABEL → first match), which is often wrong contextually. The
# disambiguator (Claude Haiku, cached) chooses the right article per
# category context (Chemistry > ABEL → Sir Frederick Augustus Abel,
# Mathematics > ABEL → Niels Henrik Abel, etc.). --apply-only consults
# the existing cache without API calls; run without that flag manually
# to resolve any uncached new ambiguities.
echo
echo "=== Phase 6b2: Applying cached TOC disambiguations [$(elapsed)] ==="
uv run python tools/vol29/disambiguate_toc.py --apply-only

# --- Phase 6c: Detect first-content fm scan per volume ---
echo
echo "=== Phase 6c: Detecting fm first-content pages [$(elapsed)] ==="
uv run python tools/diagnostics/detect_fm_blank_pages.py

# --- Phase 6d: Rebuild generated site pages ---
# All four ancillary pages auto-rebuild from source: about.html
# (editor's intro from docs/about.txt — user-editable, changes most
# often), and the three frozen-content pages preface.html /
# ancillary-prefatory-note.html / ancillary-index-preface.html /
# ancillary-abbreviations.html (1910 print transcriptions via
# corrections.json + raw wikitext / vol29_ancillary.json).
echo
echo "=== Phase 6d: Rebuilding generated site pages [$(elapsed)] ==="
uv run python tools/viewer/build_about_page.py
uv run python tools/viewer/build_ancillary_pages.py
uv run python tools/viewer/build_preface.py

# --- Phase 6e: Build Reader's Guide (65 chapters + 6 part pages + TOC) ---
# Depends on data/derived/articles/index.json (Phase 4) and
# data/derived/articles/contributors.json (Phase 3b) for link resolution.
echo
echo "=== Phase 6e: Building Reader's Guide [$(elapsed)] ==="
uv run python tools/viewer/build_readers_guide.py all > /dev/null

# --- Phase 6f: Pre-deploy quality report (visibility only) ---
# Runs the report before deploy so we can see the numbers in the log,
# but does NOT block the deploy — the site is currently broken, so
# even a regressing rebuild is an improvement.  Gate-style blocking
# (xref/stray_italic thresholds, title-shape check, pair-diff vs
# baseline) goes in once we're back to healthy.
echo
echo "=== Phase 6f: Pre-deploy quality report (no gate) [$(elapsed)] ==="
uv run python tools/diagnostics/quality_report.py

# --- Phase 6g: Pre-deploy contributor-dedup gate ---
# Produces a candidate list at sim ≥ 0.85 and aborts (via set -e) if
# anything isn't already covered by data/contributor_aliases.json's
# `aliases` (will collapse on the NEXT rebuild) or explicitly listed
# in its `distinct` section (acknowledged-different people).  Real
# dupes must be added to one or the other before deploy.
echo
echo "=== Phase 6g: Contributor-dedup gate [$(elapsed)] ==="
uv run python tools/db/dedup_contributors.py \
  --report data/derived/quality_reports/dedup_candidates.json
uv run python tools/diagnostics/check_dedup_candidates.py

# --- Phase 7: Deploy ---
if [ -z "$NO_DEPLOY" ]; then
  echo
  echo "=== Phase 7: Deploying [$(elapsed)] ==="

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
  aws s3 sync data/derived/images/ s3://britannica11.org/data/images/ \
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

  echo "  Uploading viewer..."
  aws s3 cp tools/viewer/viewer.html s3://britannica11.org/viewer.html
  aws s3 cp tools/viewer/index.html s3://britannica11.org/index.html
  aws s3 cp tools/viewer/search.html s3://britannica11.org/search.html
  aws s3 cp tools/viewer/scans.html s3://britannica11.org/scans.html
  aws s3 cp tools/viewer/search-api.js s3://britannica11.org/search-api.js
  aws s3 cp tools/viewer/article-urls.js s3://britannica11.org/article-urls.js
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
  ssh -i "$EC2_KEY" ec2-user@"$EC2_HOST" \
    "aws s3 sync s3://britannica11.org/data/articles/ ~/articles/ --delete --quiet && python3 ~/index_search_ec2.py"

  echo "  Deploy complete."
else
  echo
  echo "=== Skipping deploy (--no-deploy) ==="
fi

# --- Phase 8: (quality report now in Phase 6f, pre-deploy) ---
# Left intentionally blank — gate moved to before Phase 7 so regressions
# halt the rebuild instead of shipping.

# --- Phase 9: Deploy preflight ---
# After deploy, verify every asset referenced by the viewer HTML is
# reachable on britannica11.org.  Catches the "shipped HTML that
# references a file we forgot to upload" bug class (the article-urls.js
# near-miss on 2026-04-22).  Runs here — AFTER the quality report —
# so we get metrics even if the preflight fails, but set -e at the
# top of this script ensures we don't print the success banner if a
# reference is missing.
if [ "$NO_DEPLOY" = "" ]; then
  echo
  echo "=== Phase 9: Deploy preflight [$(elapsed)] ==="
  uv run python tools/diagnostics/check_deploy_refs.py
fi

echo
echo "============================================"
echo "  Rebuild complete. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
