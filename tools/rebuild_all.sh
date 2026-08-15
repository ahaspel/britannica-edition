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
#
# The phases (the serious work is the walk, the export, and the resolve —
# everything after is derivation and verification):
#   1  Clean      truncate DB + clear exports
#   2  Walk       per-volume pipeline: (import +) detect-boundaries, parallel
#   3  Page map   3.1 printed-page mapping · 3.2 article-index snapshot
#   4  Export     4.1 corpus-export · 4.2 math-width cache
#   5  Resolve    5.1 classified TOC · 5.2 TOC disambiguations · 5.3 kind index
#                 5.4 post-export pass (math · contributors · xrefs · render)
#   6  Site       6.1 fm first-content scan · 6.2 generated pages + stamp
#                 6.3 Reader's Guide · 6.4 download bundles
#   7  Gates      7.1 quality report · 7.2 overlap audit (reports)
#                 7.3 mangled-marker · 7.4 link census · 7.5 contributor-dedup (gates)
#   8  Deploy     opt-in (--deploy); default is build-only
#
# Relabeled 2026-08-15.  Decoder for pre-relabel logs/docs (old → new):
#   3c→3.1  3d→3.2  4→4.1  4b→4.2  6b→5.1  6b2→5.2  6b3→5.3  6b4/6b5→5.4
#   6c→6.1  6d→6.2  6e→6.3  6h→6.4  6f→7.1+7.2  6i→7.3  6i2→7.4  6g→7.5  7→8

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

  # Note: S3 bucket is NOT cleared here — s3 sync --delete in the deploy
  # (Phase 8) handles cleanup. This keeps the site live during the rebuild.

# NOTE: the contributor ROSTER is no longer built here.  It used to be built
# PRE-walk (build_contributor_table + vol-29 linker) — but its only walk-time
# consumer was the [[Author:]] signature render, which is now deferred
# (the walk emits a neutral «AL» marker).  So the post-export pass (Phase 5.4)
# builds the roster from footers + front matter + vol-29 and THEN resolves the
# ambiguous [[Author:]] links against the finished roster — for both binding and
# render.  ([[project_roster_from_author_links]])

# --- Phase 2: Walk the volumes (bounded-parallel) ---
# The volumes are INDEPENDENT: detect-boundaries wipes+rebuilds only its OWN
# volume's rows (wipe_articles filters Article.volume; no cross-volume delete,
# no shared global state — Postgres sequences give unique ids concurrently), so
# the walk fans out.  Bounded (PHASE2_PAR, default 6) so 28 writers don't swamp
# Postgres/CPU.  A failure in ANY volume aborts the rebuild — never ship a
# partial corpus ([[feedback_never_partial_rebuild]]).  Each volume's output is
# captured to a per-volume log and printed on completion/failure (parallel
# stdout would interleave).  detect-boundaries ALWAYS runs (derived from
# source_pages, changes with code); --skip-import only spares the page IMPORT.
PHASE2_PAR=${PHASE2_PAR:-6}
echo
echo "=== Phase 2: Walking the volumes (parallel x$PHASE2_PAR) ==="
P2_DIR=$(mktemp -d)

walk_volume() {
  local vol="$1" PADDED RUN_DIR LOG
  PADDED=$(printf "%02d" "$vol")
  RUN_DIR="data/raw/wikisource/vol_${PADDED}"
  LOG="$P2_DIR/vol_${vol}.log"
  # subshell owns its own set -e: import (if any) must succeed before detect.
  if ( set -e
       [ -n "$SKIP_IMPORT" ] || uv run python tools/fetch/import_wikisource_pages.py --indir "$RUN_DIR" --volume "$vol"
       uv run britannica detect-boundaries "$vol"
     ) > "$LOG" 2>&1
  then
    echo ok > "$P2_DIR/vol_${vol}.status"
    echo "  Volume $vol complete. [$(elapsed)]"
  else
    echo fail > "$P2_DIR/vol_${vol}.status"
    echo "  !! Volume $vol FAILED [$(elapsed)] — log follows:"
    cat "$LOG"
  fi
}

for vol in $VOLUMES; do
  walk_volume "$vol" &
  # throttle: never more than PHASE2_PAR walks in flight.  `|| true` so a failed
  # job's non-zero wait doesn't trip set -e mid-collect — failures are tallied below.
  while [ "$(jobs -r | wc -l)" -ge "$PHASE2_PAR" ]; do wait -n || true; done
done
wait || true

P2_FAILS=0
for vol in $VOLUMES; do
  [ "$(cat "$P2_DIR/vol_${vol}.status" 2>/dev/null)" = "ok" ] \
    || { echo "  volume $vol did not complete"; P2_FAILS=$((P2_FAILS + 1)); }
done
rm -rf "$P2_DIR"
if [ "$P2_FAILS" -ne 0 ]; then
  echo "=== Phase 2 FAILED: $P2_FAILS volume(s) did not complete — aborting rebuild ==="
  exit 1
fi

# --- Phase 3.1: Rebuild printed-page mapping (ws→printed / leaf→printed) ---
# MUST run before Phase 4's re-export: the article exporter consults
# printed_pages.json to translate each segment's ws-space PAGE marker
# into its printed-page number.  If this ran AFTER the exports (as it
# once did), every rebuild shipped with stale mappings — visible on
# SHIPBUILDING where page markers ran past the article's last
# printed page (981) into the next article's numbering (982+).
echo
echo "=== Phase 3.1: Rebuilding printed-page mapping [$(elapsed)] ==="
uv run python tools/pipeline/build_printed_pages.py

# --- Phase 3.2: Snapshot article index for cross-rebuild diff ---
# `data/derived/article_index.tsv` is a TSV (vol, page_start,
# page_end, article_type, title) sorted by (volume, page_start,
# title).  Commit it to git after each rebuild and `git log -p` on
# it shows article-list churn between rebuilds — catches "we lost N
# articles" regressions like the 2026-05-16 missing-33 incident
# where we had no way to identify which articles disappeared.
echo
echo "=== Phase 3.2: Snapshot article index [$(elapsed)] ==="
uv run python tools/diagnostics/snapshot_article_index.py

# --- Phase 4.1: Assemble + export the whole corpus (in-memory resolution) ---
echo
echo "=== Phase 4.1: Assembling + exporting all volumes [$(elapsed)] ==="
uv run britannica corpus-export

# --- Phase 4.2: Measure math widths (refresh scale-hint cache) ---
# Renders every unique display-mode `«MATH:` marker in the exported
# corpus through KaTeX in a headless browser and records the smallest
# font-size that fits the body-text column.  Cached at
# data/derived/math_widths.json (hash-keyed) — only NEW LaTeX gets
# re-measured.  See tools/diagnostics/measure_math_widths.py.
echo
echo "=== Phase 4.2: Measuring math widths [$(elapsed)] ==="
uv run python tools/diagnostics/measure_math_widths.py

# (Math-marker annotation from the refreshed cache is no longer its own phase —
# it is the first transform of the merged post-export pass, Phase 5.4 below, so
# the corpus is read and written once instead of three times.)

# --- Phase 5.1: Build classified TOC (topics page data) ---
echo
echo "=== Phase 5.1: Building classified TOC (vol 29 topics) [$(elapsed)] ==="
uv run python tools/vol29/populate_classified_toc.py

# --- Phase 5.2: Apply cached topic-disambiguation choices ---
# populate_classified_toc.py picks one article per ambiguous index entry
# (e.g. ABEL → first match), which is often wrong contextually. The
# disambiguator (Claude Haiku, cached) chooses the right article per
# category context (Chemistry > ABEL → Sir Frederick Augustus Abel,
# Mathematics > ABEL → Niels Henrik Abel, etc.). --apply-only consults
# the existing cache without API calls; run without that flag manually
# to resolve any uncached new ambiguities.
echo
echo "=== Phase 5.2: Applying cached TOC disambiguations [$(elapsed)] ==="
uv run python tools/vol29/disambiguate_toc.py --apply-only

# --- Phase 5.3: Build the kind index (filename -> [kinds]) ---
# Reads the FINISHED classified_toc (post-5.2) and each article's lead_kind to
# emit data/derived/kind_index.json — the general form of the person set,
# consumed by the xref collision-picker.  [[project_resolver_consolidation]] B.
echo
echo "=== Phase 5.3: Building kind index [$(elapsed)] ==="
uv run python tools/vol29/build_kind_index.py

# --- Phase 5.4: Post-export pass (math hints + contributors + xrefs + render) ---
# ONE load of the ~37k article JSONs, every corpus-wide transform, ONE write —
# was three separate phases (math, contributors, xrefs+render), each
# re-reading and rewriting the whole corpus and each replaying the stable_id
# dedup in its own process.  The order inside is the DEPENDENCY order:
#   math hints   — must be on the body before the render reads it;
#   contributors — the "By …" byline is baked into rendered_html, so binding
#                  must precede the render or every article renders author-less;
#                  runs after the kind index (5.3) so vol-29 credits are
#                  disambiguated by the contributor's kind FOOTPRINT;
#   xrefs+render — the export deferred resolution (defer_xrefs) so the picker can
#                  consult the topic resolution built above; (re)writes
#                  xref_resolution.jsonl.
# MUST run before any consumer of the decorated bodies / rendered_html / xref
# graph / contributors (6.3 Reader's Guide, 6.4 download bundle, the search index).
# Each transform is still runnable alone via its own module's main().
# [[project_resolver_consolidation]]
echo
echo "=== Phase 5.4: Post-export pass (math · contributors · xrefs · render) [$(elapsed)] ==="
uv run python tools/pipeline/post_export.py

# --- Phase 6.1: Detect first-content fm scan per volume ---
echo
echo "=== Phase 6.1: Detecting fm first-content pages [$(elapsed)] ==="
uv run python tools/diagnostics/detect_fm_blank_pages.py

# --- Phase 6.2: Rebuild generated site pages ---
# Generated site pages auto-rebuild from source: about.html and
# download.html (editor-authored prose from docs/about.txt and
# docs/download.txt — user-editable, changes most often), and the
# three frozen-content pages preface.html /
# ancillary-prefatory-note.html / ancillary-index-preface.html /
# ancillary-abbreviations.html (1910 print transcriptions via
# corrections.json + raw wikitext / vol29_ancillary.json).
echo
echo "=== Phase 6.2: Rebuilding generated site pages [$(elapsed)] ==="
uv run python tools/viewer/build_about_page.py
uv run python tools/viewer/build_download_page.py
uv run python tools/viewer/build_ancillary_pages.py
uv run python tools/viewer/build_preface.py
# Corpus fingerprint for the viewer's `?v=` article-cache bust.  MUST run after
# Phase 5.4, which patches every article JSON — stamping before that would
# fingerprint bytes we are not shipping.
uv run python tools/viewer/build_stamp.py

# --- Phase 6.3: Build Reader's Guide (65 chapters + 6 part pages + TOC) ---
# Depends on data/derived/articles/index.json (Phase 4) and
# data/derived/articles/contributors.json (Phase 4) for link resolution.
echo
echo "=== Phase 6.3: Building Reader's Guide [$(elapsed)] ==="
uv run python tools/viewer/build_readers_guide.py all > /dev/null

# --- Phase 6.4: Build the public download bundles (agent JSONL + 3 graphs) ---
# The corpus and its three knowledge graphs re-rendered for download:
# articles.jsonl (Markdown records), xref_edges.jsonl (reference graph),
# topics.json (subject taxonomy), contributors.json (authorship roster).
# Pure REASSEMBLY of already-derived data (article JSONs + classified_toc) — a
# few minutes, no DB, no recompute.  MUST run after Phase 5.2 so it reads the
# DISAMBIGUATED classified_toc.json (ABEL→right Abel, Zürich town vs canton).
echo
echo "=== Phase 6.4: Building download bundles [$(elapsed)] ==="
uv run python -m britannica.export.download
# The maps bundle (colour plates + Stieler originals) rebuilds too so a registry
# or image change never ships a stale archive; validates maps.json's file refs.
uv run python -m britannica.export.download maps

# --- Phase 7.1: Quality report (visibility, no gate) ---
# The standing numbers, printed to the log so a regression is visible in the
# build that introduced it.  Deliberately not a gate — the hard invariants
# each have their own gate below (7.3-7.5); everything here is judgment.
echo
echo "=== Phase 7.1: Quality report (no gate) [$(elapsed)] ==="
uv run python tools/diagnostics/quality_report.py

# --- Phase 7.2: Overlap audit (visibility, no gate) ---
# The quality report is the LEAK side: it reads `rendered_html` and asks what
# survived raw into the output.  It is structurally blind to LOSS — something the
# SOURCE had and the output silently lacks never appears in it, because it never
# reads the source ([[feedback_loss_vs_leak]]).  Every defect the 2026-07 unpaired-
# styler arc turned up was of that kind: an unpaired `{{fine print/s}}` produced
# the empty string, and a `{{…/e}}` sitting in a page footer was deleted with the
# `<noinclude>` before the walker ever ran.  Neither leaks; neither was visible for
# as long as it existed.  This audit is the missing half — it reads RAW source and
# counts the construct halves that cannot pair (dangling) and the spans that cross
# (which no tree can bound).  `--refresh` because the corpus pickle is stale by
# definition on a fresh rebuild.  No gate: it is a standing number to watch move.
echo
echo "=== Phase 7.2: Overlap audit (no gate) [$(elapsed)] ==="
uv run python tools/diagnostics/overlap_audit.py --refresh --examples 6

# A guillemet is our marker delimiter, so one standing outside a well-formed
# token is either a marker WE mangled or one the SOURCE already had.  The leak
# oracle cannot tell — it matches well-formed markers, and a mangled marker is
# not one, which is how `«#I»` (a link target split on a close marker's slash)
# and `«BR)` (an equation label read to the wrong `»`) both shipped unseen.
# Comparing against the raw source separates them exactly and needs no baseline:
# 24 articles carry Wikisource's own `Â«` mojibake and stay silent; anything we
# invent aborts the build.  A GATE, not a report — this class is never benign.
echo
echo "=== Phase 7.3: Mangled-marker gate [$(elapsed)] ==="
uv run python tools/diagnostics/mangled_markers.py

# The census is 7.3's other half: 7.3 proves we invented no mangled markers,
# the census proves resolved links did not go DOWN vs production.  A link that
# stops resolving dies silently — the bake strips it to plain text, and no
# marker-level check can tell that from a link that legitimately never bound
# (the 2026-08-14 «LN» grammar fork lost ~370 links invisibly).  Counts
# resolved `/article/` anchors in a ~250-article production sample.
echo
echo "=== Phase 7.4: Resolved-link census gate [$(elapsed)] ==="
uv run python tools/diagnostics/link_census.py 250 --gate

# --- Phase 7.5: Contributor-dedup gate ---
# Produces a candidate list at sim ≥ 0.85 and aborts (via set -e) if
# anything isn't already covered by data/contributor_aliases.json's
# `aliases` (will collapse on the NEXT rebuild) or explicitly listed
# in its `distinct` section (acknowledged-different people).  Real
# dupes must be added to one or the other before deploy.
echo
echo "=== Phase 7.5: Contributor-dedup gate [$(elapsed)] ==="
uv run python tools/db/dedup_contributors.py \
  --report data/derived/quality_reports/dedup_candidates.json
uv run python tools/diagnostics/check_dedup_candidates.py

# --- Phase 8: Deploy (OPT-IN) ---
# The full deploy + preflight now live in tools/deploy.sh, so the exact same push runs
# whether we deploy here (--deploy) or ship a reviewed build later (./tools/deploy.sh).
# Default is build-only: a partial/stale push is the "partial deploy" we forbid, and a
# reviewed full build shipped whole is not.
if [ -n "$DEPLOY" ]; then
  echo
  echo "=== Phase 8: Deploying [$(elapsed)] ==="
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
