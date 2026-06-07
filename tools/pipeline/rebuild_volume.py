#!/usr/bin/env python3
"""Rebuild a volume's articles (targeted at one article for the
post-rebuild report / deploy).  The script is named after what it
ACTUALLY does — rebuild the whole volume — even though you specify a
single article as the target.  Boundary detection, transformation, and
xref resolution are inherently per-volume operations; you can't
rebuild just one article in isolation.

Both modes wipe the volume's article records and rebuild from
`SourcePage` rows.  They differ in how aggressive the wipe is and how
many stages get re-run.

Default (fast) mode — for code-iteration:
    * Preserves `source_pages`.
    * Runs only `prepare_wikitext` → `detect_boundaries` →
      `transform_articles` → `export_articles_to_json`, in-process.
    * Skips classify / extract-xrefs / resolve-xrefs / extract-images /
      extract-contributors — those don't change when you're tweaking
      detection / transform / export logic.
    * ~30-90s per volume.

`--full` mode — for source-data changes:
    * Wipes everything including `source_pages`.
    * Re-imports from `data/raw/wikisource/vol_NN/`.
    * Runs the full per-volume pipeline via subprocess (matches
      `rebuild_all.sh`'s Phase 2 invocation per volume).
    * Required when source data may have changed or when image /
      contributor / classification extraction needs to refresh.

`--deploy` uploads just the target article's JSON to S3 and
invalidates CloudFront.  Works in either mode.

Note: `tools/db/rebuild_volume.sh` is a related but distinct tool —
it does a clean-baseline rebuild of a whole volume (wipes derived
JSON, runs quality_report) without targeting any one article.  Use
this Python script when you want fast code-iteration on a specific
article's output; use the shell script when you want a clean
volume-level baseline.

Usage:
    uv run python tools/pipeline/rebuild_volume.py <volume> <TITLE> \\
        [--full] [--deploy]
    uv run python tools/pipeline/rebuild_volume.py <volume> \\
        <START_PAGE> <END_PAGE> [--full] [--deploy]

Examples:
    uv run python tools/pipeline/rebuild_volume.py 1 BAG-PIPE
    uv run python tools/pipeline/rebuild_volume.py 1 BAG-PIPE --deploy
    uv run python tools/pipeline/rebuild_volume.py 1 219 223 --full
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from britannica.db.models import Article
from britannica.db.session import SessionLocal
from britannica.export.article_json import (
    _safe_filename,
    export_articles_to_json,
)
from britannica.pipeline.stages.detect_boundaries import (
    persist_articles,
    wipe_articles,
)
from britannica.pipeline.stages.super_detect import detect_boundaries
from britannica.pipeline.stages.prepare_wikitext import prepare_wikitext
from britannica.pipeline.stages.transform_articles import transform_articles
from sqlalchemy import text


# ── Article lookup ────────────────────────────────────────────────────

def find_article(session, volume: int, title: str | None,
                 start_page: int | None, end_page: int | None) -> Article:
    """Resolve a `<volume> TITLE` or `<volume> START_PAGE [END_PAGE]`
    argument set to a concrete Article row.  Title lookup tries exact
    upper-case first, then case-insensitive, then a substring search
    that lists similar titles when nothing matches."""
    if title:
        title_upper = title.upper()
        article = (
            session.query(Article)
            .filter(Article.volume == volume, Article.title == title_upper)
            .first()
        )
        if not article:
            article = (
                session.query(Article)
                .filter(Article.volume == volume, Article.title.ilike(title))
                .first()
            )
        if not article:
            print(f"Article '{title}' not found in volume {volume}.")
            similar = (
                session.query(Article)
                .filter(Article.volume == volume,
                        Article.title.ilike(f"%{title}%"))
                .order_by(Article.page_start)
                .all()
            )
            if similar:
                print("Similar:")
                for m in similar[:10]:
                    print(f"  {m.title} (pages {m.page_start}-{m.page_end})")
            sys.exit(1)
        return article

    article = (
        session.query(Article)
        .filter(Article.volume == volume, Article.page_start == start_page)
        .first()
    )
    if not article:
        print(f"No article at page {start_page} in volume {volume}.")
        sys.exit(1)
    return article


# ── Wipe helpers ──────────────────────────────────────────────────────
# Articles-only wipe is provided by ``britannica.pipeline.stages
# .detect_boundaries.wipe_articles``; rebuild calls it directly.


def _wipe_everything(volume: int) -> None:
    """Full wipe — articles + source_pages.  Forces a re-import from
    `data/raw/wikisource/vol_NN/` in the next step."""
    s = SessionLocal()
    try:
        stmts = [
            f"DELETE FROM article_contributors WHERE article_id IN "
            f"(SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM article_images WHERE article_id IN "
            f"(SELECT id FROM articles WHERE volume = {volume}) "
            f"OR source_page_id IN "
            f"(SELECT id FROM source_pages WHERE volume = {volume})",
            f"UPDATE cross_references SET target_article_id = NULL, "
            f"status = 'unresolved' WHERE target_article_id IN "
            f"(SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM cross_references WHERE article_id IN "
            f"(SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM article_segments WHERE article_id IN "
            f"(SELECT id FROM articles WHERE volume = {volume}) "
            f"OR source_page_id IN "
            f"(SELECT id FROM source_pages WHERE volume = {volume})",
            f"DELETE FROM articles WHERE volume = {volume}",
            f"DELETE FROM source_pages WHERE volume = {volume}",
        ]
        for stmt in stmts:
            s.execute(text(stmt))
        s.commit()
    finally:
        s.close()


# ── Pipeline runners ──────────────────────────────────────────────────

def _run_fast(volume: int, t0: float) -> None:
    """In-process minimal pipeline: prepare_wikitext → detect →
    transform → export.  Article-shaping stages only — skips
    classification, xrefs, images, contributors."""
    print(f"[{time.time()-t0:5.1f}s] Wiping vol {volume} articles…")
    n = wipe_articles(volume)
    print(f"[{time.time()-t0:5.1f}s]   Deleted {n} articles")

    print(f"[{time.time()-t0:5.1f}s] Preparing wikitext "
          f"(corrections.json + quote-run conversion)…")
    n = prepare_wikitext(volume)
    print(f"[{time.time()-t0:5.1f}s]   Prepared {n} pages")

    print(f"[{time.time()-t0:5.1f}s] Detecting boundaries…")
    detected = detect_boundaries(volume)
    persist_articles(detected)
    print(f"[{time.time()-t0:5.1f}s]   Detected {len(detected)} articles")

    print(f"[{time.time()-t0:5.1f}s] Transforming articles…")
    n = transform_articles(volume)
    print(f"[{time.time()-t0:5.1f}s]   Transformed {n} articles")

    print(f"[{time.time()-t0:5.1f}s] Exporting volume {volume} to JSON…")
    n = export_articles_to_json(volume, "data/derived/articles")
    print(f"[{time.time()-t0:5.1f}s]   Exported {n} articles")


def _run_full(volume: int, t0: float) -> None:
    """Subprocess full pipeline, matching Phase 2 of `rebuild_all.sh`.
    Wipes everything (including source_pages), re-imports, runs every
    article-pipeline stage."""
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = f"data/raw/wikisource/vol_{volume:02d}"

    print(f"[{time.time()-t0:5.1f}s] Wiping vol {volume} "
          f"(articles + source_pages)…")
    _wipe_everything(volume)

    steps = [
        ("Importing pages",
         ["uv", "run", "python", "tools/fetch/import_wikisource_pages.py",
          "--indir", raw_dir, "--volume", str(volume), "--overwrite"]),
        ("Preparing wikitext",
         ["uv", "run", "britannica", "prepare-wikitext", str(volume)]),
        ("Detecting boundaries",
         ["uv", "run", "britannica", "detect-boundaries", str(volume)]),
        ("Transforming articles",
         ["uv", "run", "britannica", "transform-articles", str(volume)]),
        ("Classifying articles",
         ["uv", "run", "britannica", "classify-articles", str(volume)]),
        ("Extracting xrefs",
         ["uv", "run", "britannica", "extract-xrefs", str(volume)]),
        ("Resolving xrefs",
         ["uv", "run", "britannica", "resolve-xrefs-all"]),
        ("Extracting images",
         ["uv", "run", "britannica", "extract-images", str(volume)]),
        ("Extracting contributors",
         ["uv", "run", "britannica", "extract-contributors", str(volume)]),
        ("Exporting articles",
         ["uv", "run", "britannica", "export-articles", str(volume)]),
    ]
    for label, cmd in steps:
        print(f"[{time.time()-t0:5.1f}s] {label}…")
        result = subprocess.run(
            cmd, check=True, cwd=str(project_root),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            print(f"[{time.time()-t0:5.1f}s]   {lines[-1]}")


# ── Deploy ────────────────────────────────────────────────────────────

CLOUDFRONT_DIST_ID = "E24BJKH0IB4I6"


def _deploy_article(filename: str) -> None:
    """Upload one article JSON to S3 + invalidate CloudFront."""
    local_path = Path("data/derived/articles") / filename
    if not local_path.exists() or local_path.stat().st_size == 0:
        print(f"  Warning: {local_path} missing or empty — skipping deploy")
        return
    print(f"  Uploading {filename} to S3…")
    subprocess.run(
        ["aws", "s3", "cp", str(local_path),
         f"s3://britannica11.org/data/articles/{filename}"],
        check=True,
    )
    subprocess.run(
        ["aws", "cloudfront", "create-invalidation",
         "--distribution-id", CLOUDFRONT_DIST_ID,
         "--paths", f"/data/articles/{filename}"],
        check=True, stdout=subprocess.DEVNULL,
    )
    print("  Deployed and invalidated.")


# ── Entry point ───────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("volume", type=int)
    p.add_argument("args", nargs="+",
                   help="TITLE  OR  START_PAGE END_PAGE")
    p.add_argument("--full", action="store_true",
                   help="Wipe source_pages + re-import + run every "
                        "article-pipeline stage (slower; needed when "
                        "source data changed or image/contributor "
                        "extraction must refresh).")
    p.add_argument("--deploy", action="store_true",
                   help="Upload the rebuilt article JSON to S3 and "
                        "invalidate CloudFront.")
    args = p.parse_args()

    title = None
    start_page = end_page = None
    if (len(args.args) == 2
            and args.args[0].isdigit() and args.args[1].isdigit()):
        start_page = int(args.args[0])
        end_page = int(args.args[1])
    else:
        title = " ".join(args.args)

    # Verify the article exists before wiping (so a typo'd title
    # doesn't silently rebuild a volume that doesn't contain it).
    s = SessionLocal()
    try:
        a = find_article(s, args.volume, title, start_page, end_page)
        target_title = a.title
        target_range = f"pp.{a.page_start}-{a.page_end}"
    finally:
        s.close()

    mode = "full" if args.full else "fast"
    print(f"Rebuilding {target_title!r} (vol {args.volume}, "
          f"{target_range}) — {mode} mode")
    print()

    t0 = time.time()
    if args.full:
        _run_full(args.volume, t0)
    else:
        _run_fast(args.volume, t0)

    # Look up the rebuilt article to report (and deploy) its output JSON.
    s = SessionLocal()
    try:
        a = find_article(s, args.volume, target_title, None, None)
        filename = _safe_filename(a, a.title)
    finally:
        s.close()

    out = Path("data/derived/articles") / filename
    if out.exists():
        size = out.stat().st_size
        print(f"\n[{time.time()-t0:5.1f}s] OK  {out}  ({size:,} bytes)")
    else:
        print(f"\n[{time.time()-t0:5.1f}s] WARN  expected {out}  (not found)")

    if args.deploy:
        print()
        _deploy_article(filename)

    return 0


if __name__ == "__main__":
    sys.exit(main())
