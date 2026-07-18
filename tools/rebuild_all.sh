#!/bin/bash
# Full rebuild of all 28 article volumes from cached wikitext.
# Wipes the DB + exports and rebuilds from scratch, then runs quality analytics.
#   * By DEFAULT it does NOT deploy — review the local build, then ship exactly what
#     you reviewed with ./tools/deploy.sh (or pass --deploy to rebuild + deploy).
#   * By DEFAULT it REUSES the imported source_pages (the raw wikileaves are static) —
#     pass --reimport only when the raw files actually changed.
#
# Usage: ./tools/rebuild_all.sh [--deploy] [--reimport]
#
#   --reimport  Re-import the raw wikisource pages into source_pages (Phase 2) instead of
#               reusing them.  Rarely needed — the raw wikileaves never change — and costs
#               ~30 min.  Without it, source_pages is spared at truncate and Phase 2's page
#               import is skipped; detect-boundaries still runs every volume, re-deriving
#               segments/articles from the kept pages (contributors are harvested later,
#               in corpus-export's assemble walk).
#
# Preserves: data/raw/wikisource/*, data/derived/quality_reports/*

set -euo pipefail

# Force UTF-8 on every Python subprocess's stdout/stderr.  On a cp1252 Windows
# console a non-ASCII character in a log line (e.g. the "→" in the xref-persist
# message) raises UnicodeEncodeError, which under `set -e` aborts the ENTIRE
# rebuild mid-flight.  This makes the pipeline robust to its own log output.
export PYTHONIOENCODING=utf-8

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
DEPLOY=""
SKIP_IMPORT="yes"        # reuse source_pages by default; --reimport to re-fetch the raw

for arg in "$@"; do
  if [ "$arg" = "--deploy" ]; then
    DEPLOY="yes"
  elif [ "$arg" = "--no-deploy" ]; then
    DEPLOY=""            # accepted for muscle-memory; no-deploy is now the DEFAULT
  elif [ "$arg" = "--reimport" ]; then
    SKIP_IMPORT=""       # actually re-import the raw source_pages (rarely needed)
  elif [ "$arg" = "--skip-import" ]; then
    SKIP_IMPORT="yes"    # accepted for muscle-memory; skip-import is now the DEFAULT
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
if [ -n "$SKIP_IMPORT" ]; then
  echo "  Mode: reusing source_pages (skipping Phase 2 page import; pass --reimport to re-fetch)"
else
  echo "  Mode: --reimport (re-importing the raw source_pages)"
fi
echo

# --- Phase 1: Clean everything ---
echo "=== Phase 1: Cleaning everything [$(elapsed)] ==="

if [ -n "$SKIP_IMPORT" ]; then
  echo "  Truncating database (keeping source_pages — reusing imported raw)..."
  uv run python tools/db/truncate_all.py --keep-source-pages
  # verify_empty is skipped on purpose: source_pages is intentionally non-empty.
else
  echo "  Truncating database..."
  uv run python tools/db/truncate_all.py

  echo "  Verifying..."
  uv run python tools/db/verify_empty.py
fi

echo "  Clearing exports..."
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
echo "  Done."

  # Note: S3 bucket is NOT cleared here — s3 sync --delete in Phase 7
  # handles cleanup. This keeps the site live during the rebuild.

# NOTE: the contributor ROSTER is no longer built here.  It used to be Phase 1b
# (build_contributor_table) + Phase 1c (vol-29 linker), PRE-walk — but its only
# walk-time consumer was the [[Author:]] signature render, which is now deferred
# (the walk emits a neutral «AL» marker).  So Phase 6b4 (resolve_contributors_post)
# builds the roster from footers + front matter + vol-29 and THEN resolves the
# ambiguous [[Author:]] links against the finished roster — for both binding and
# render.  ([[project_roster_from_author_links]])

# --- Phase 2: Per-volume pipeline ---
echo
echo "=== Phase 2: Running pipeline for each volume ==="
for vol in $VOLUMES; do
  PADDED=$(printf "%02d" "$vol")
  RUN_DIR="data/raw/wikisource/vol_${PADDED}"

  echo
  echo "--- Volume $vol [$(elapsed)] ---"

  if [ -z "$SKIP_IMPORT" ]; then
    echo "  Importing pages..."
    uv run python tools/fetch/import_wikisource_pages.py \
      --indir "$RUN_DIR" \
      --volume "$vol"
  else
    echo "  Reusing imported pages (--skip-import)."
  fi

  # detect-boundaries ALWAYS runs: it's derived from source_pages (re-created
  # each rebuild) and changes with code.  --skip-import only spares the immutable
  # page IMPORT above.  (Contributor harvest + linking now ride corpus-export's
  # single assemble walk — Phase 4 — so there's no per-volume extract pass.)
  echo "  Detecting boundaries..."
  uv run britannica detect-boundaries "$vol"

  echo "  Volume $vol complete. [$(elapsed)]"
done

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

# --- Phase 4: Assemble + export the whole corpus (in-memory resolution) ---
echo
echo "=== Phase 4: Assembling + exporting all volumes [$(elapsed)] ==="
uv run britannica corpus-export

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
echo "=== Phase 6b: Building classified TOC (vol 29 topics) [$(elapsed)] ==="
uv run python tools/vol29/populate_classified_toc.py

# --- Phase 6b2: Apply cached topic-disambiguation choices ---
# populate_classified_toc.py picks one article per ambiguous index entry
# (e.g. ABEL → first match), which is often wrong contextually. The
# disambiguator (Claude Haiku, cached) chooses the right article per
# category context (Chemistry > ABEL → Sir Frederick Augustus Abel,
# Mathematics > ABEL → Niels Henrik Abel, etc.). --apply-only consults
# the existing cache without API calls; run without that flag manually
# to resolve any uncached new ambiguities.
echo
echo "=== Phase 6b2: Applying cached TOC disambiguations [$(elapsed)] ==="
uv run python tools/vol29/disambiguate_toc.py --apply-only

# --- Phase 6b3: Build the kind index (filename -> [kinds]) ---
# Reads the FINISHED classified_toc (post-6b2) and each article's lead_kind to
# emit data/derived/kind_index.json — the general form of the person set,
# consumed by the xref collision-picker.  [[project_resolver_consolidation]] B.
echo
echo "=== Phase 6b3: Building kind index [$(elapsed)] ==="
uv run python tools/vol29/build_kind_index.py

# --- Phase 6b4: Resolve contributor attributions post-export ---
# ALL contributor binding (signatures + front-matter + vol-29) now lives here,
# after the kind index (6b3), so vol-29 credits are disambiguated by the
# contributor's kind FOOTPRINT + the credit's own hint — a kind-mismatched
# homonym (Adams-the-township for the historian) is abstained, not bound.
# Patches each article JSON's `contributors` + rebuilds contributors.json.
# MUST run BEFORE 6b5 (render): the "By …" byline is baked into rendered_html
# from the `contributors` field, so binding has to happen first or every article
# renders author-less.  Also before any other contributor consumer (6e Reader's
# Guide, 6h download bundle, the search index).  [[project_resolver_consolidation]]
echo
echo "=== Phase 6b4: Resolving contributor attributions post-export [$(elapsed)] ==="
uv run python tools/pipeline/resolve_contributors_post.py

# --- Phase 6b5: Resolve inline xrefs + render post-export ---
# The export deferred xref resolution (defer_xrefs) so the collision-picker can
# consult the topic resolution + kind index built above.  This phase runs the
# REORDERED tail — resolve, bake «LN» markers into each body, render — patching
# every article JSON in place and (re)writing xref_resolution.jsonl.  RENDER IS
# LAST: it reads the `contributors` bound in 6b4 so the byline appears.  MUST run
# before any consumer of the decorated bodies / rendered_html / xref graph
# (6e Reader's Guide, 6h download bundle, the search index).
# [[project_resolver_consolidation]] F.
echo
echo "=== Phase 6b5: Resolving inline xrefs + rendering post-export [$(elapsed)] ==="
uv run python tools/pipeline/resolve_xrefs_post.py

# --- Phase 6c: Detect first-content fm scan per volume ---
echo
echo "=== Phase 6c: Detecting fm first-content pages [$(elapsed)] ==="
uv run python tools/diagnostics/detect_fm_blank_pages.py

# --- Phase 6d: Rebuild generated site pages ---
# Generated site pages auto-rebuild from source: about.html and
# download.html (editor-authored prose from docs/about.txt and
# docs/download.txt — user-editable, changes most often), and the
# three frozen-content pages preface.html /
# ancillary-prefatory-note.html / ancillary-index-preface.html /
# ancillary-abbreviations.html (1910 print transcriptions via
# corrections.json + raw wikitext / vol29_ancillary.json).
echo
echo "=== Phase 6d: Rebuilding generated site pages [$(elapsed)] ==="
uv run python tools/viewer/build_about_page.py
uv run python tools/viewer/build_download_page.py
uv run python tools/viewer/build_ancillary_pages.py
uv run python tools/viewer/build_preface.py

# --- Phase 6e: Build Reader's Guide (65 chapters + 6 part pages + TOC) ---
# Depends on data/derived/articles/index.json (Phase 4) and
# data/derived/articles/contributors.json (Phase 4) for link resolution.
echo
echo "=== Phase 6e: Building Reader's Guide [$(elapsed)] ==="
uv run python tools/viewer/build_readers_guide.py all > /dev/null

# --- Phase 6h: Build the public download bundle (agent JSONL + 3 graphs) ---
# The corpus and its three knowledge graphs re-rendered for download:
# articles.jsonl (Markdown records), xref_edges.jsonl (reference graph),
# topics.json (subject taxonomy), contributors.json (authorship roster).
# Pure REASSEMBLY of already-derived data (article JSONs + classified_toc) — a
# few minutes, no DB, no recompute.  MUST run after Phase 6b2 so it reads the
# DISAMBIGUATED classified_toc.json (ABEL→right Abel, Zürich town vs canton).
echo
echo "=== Phase 6h: Building download bundle [$(elapsed)] ==="
uv run python -m britannica.export.download

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

# --- Phase 7: Deploy (OPT-IN) ---
# The full deploy + preflight now live in tools/deploy.sh, so the exact same push runs
# whether we deploy here (--deploy) or ship a reviewed build later (./tools/deploy.sh).
# Default is build-only: a partial/stale push is the "partial deploy" we forbid, and a
# reviewed full build shipped whole is not.
if [ -n "$DEPLOY" ]; then
  echo
  echo "=== Phase 7: Deploying [$(elapsed)] ==="
  ./tools/deploy.sh
else
  echo
  echo "=== Build complete — NOT deployed.  Review it, then ship with: ./tools/deploy.sh ==="
fi

echo
echo "============================================"
echo "  Rebuild complete. Total time: $(elapsed)"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
