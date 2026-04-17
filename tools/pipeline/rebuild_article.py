#!/usr/bin/env python3
"""Quick rebuild of a single article by re-running the volume pipeline.

Usage:
    python tools/rebuild_article.py <volume> <TITLE> [--deploy]
    python tools/rebuild_article.py <volume> <start_page> <end_page> [--deploy]

Steps:
    1. Wipe the volume from the DB
    2. Re-run the volume pipeline (import, detect, transform, classify, xrefs, export)
    3. Deploy just the changed article JSON to S3

The volume pipeline is fast (no fetch) and ensures correct boundary detection.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from britannica.db.session import SessionLocal
from britannica.db.models import Article
from britannica.export.article_json import _safe_filename


def find_article(session, volume: int, title: str | None,
                 start_page: int | None, end_page: int | None) -> Article:
    if title:
        article = (
            session.query(Article)
            .filter(Article.volume == volume, Article.title == title.upper())
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
            matches = (
                session.query(Article)
                .filter(Article.volume == volume, Article.title.ilike(f"%{title}%"))
                .all()
            )
            if matches:
                print("Similar:")
                for m in matches[:10]:
                    print(f"  {m.title} (pages {m.page_start}-{m.page_end})")
            sys.exit(1)
        return article
    else:
        article = (
            session.query(Article)
            .filter(Article.volume == volume, Article.page_start == start_page)
            .first()
        )
        if not article:
            print(f"No article at page {start_page} in volume {volume}.")
            sys.exit(1)
        return article


def wipe_volume_db(volume: int):
    """Delete all data for a volume, respecting FK constraints."""
    session = SessionLocal()
    try:
        from sqlalchemy import text
        stmts = [
            f"DELETE FROM article_contributors WHERE article_id IN (SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM article_images WHERE article_id IN (SELECT id FROM articles WHERE volume = {volume}) OR source_page_id IN (SELECT id FROM source_pages WHERE volume = {volume})",
            f"UPDATE cross_references SET target_article_id = NULL, status = 'unresolved' WHERE target_article_id IN (SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM cross_references WHERE article_id IN (SELECT id FROM articles WHERE volume = {volume})",
            f"DELETE FROM article_segments WHERE article_id IN (SELECT id FROM articles WHERE volume = {volume}) OR source_page_id IN (SELECT id FROM source_pages WHERE volume = {volume})",
            f"DELETE FROM articles WHERE volume = {volume}",
            f"DELETE FROM source_pages WHERE volume = {volume}",
        ]
        for stmt in stmts:
            session.execute(text(stmt))
        session.commit()
    finally:
        session.close()


def run_volume_pipeline(volume: int):
    """Wipe and re-run the full pipeline for a volume."""
    project_root = Path(__file__).resolve().parent.parent

    print("  Wiping volume...")
    wipe_volume_db(volume)

    raw_dir = f"data/raw/wikisource/vol_{volume:02d}"

    steps = [
        ("Importing pages...",
         ["uv", "run", "python", "tools/fetch/import_wikisource_pages.py",
          "--indir", raw_dir, "--volume", str(volume), "--overwrite"]),
        ("Detecting boundaries...",
         ["uv", "run", "britannica", "detect-boundaries", str(volume)]),
        ("Transforming articles...",
         ["uv", "run", "britannica", "transform-articles", str(volume)]),
        ("Classifying articles...",
         ["uv", "run", "britannica", "classify-articles", str(volume)]),
        ("Extracting xrefs...",
         ["uv", "run", "britannica", "extract-xrefs", str(volume)]),
        ("Resolving xrefs...",
         ["uv", "run", "britannica", "resolve-xrefs", str(volume)]),
        ("Extracting images...",
         ["uv", "run", "britannica", "extract-images", str(volume)]),
        ("Extracting contributors...",
         ["uv", "run", "britannica", "extract-contributors", str(volume)]),
        ("Exporting articles...",
         ["uv", "run", "britannica", "export-articles", str(volume)]),
    ]

    for label, cmd in steps:
        print(f"  {label}")
        result = subprocess.run(
            cmd, check=True, cwd=str(project_root),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        # Print just the last line of output for brevity
        lines = result.stdout.strip().splitlines()
        if lines:
            print(f"    {lines[-1]}")


def deploy_article(filename: str):
    """Upload a single article JSON to S3 and invalidate CloudFront."""
    local_path = Path("data/derived/articles") / filename
    if not local_path.exists():
        print(f"  Warning: {local_path} not found, skipping deploy")
        return
    print(f"  Uploading {filename}...")
    subprocess.run(
        ["aws", "s3", "cp", str(local_path), f"s3://britannica11.org/data/{filename}"],
        check=True,
    )
    subprocess.run(
        ["aws", "cloudfront", "create-invalidation",
         "--distribution-id", "E24BJKH0IB4I6", "--paths", "/*"],
        check=True, stdout=subprocess.DEVNULL,
    )
    print("  Deployed and invalidated.")


def main():
    parser = argparse.ArgumentParser(description="Quick rebuild of a single article")
    parser.add_argument("volume", type=int)
    parser.add_argument("args", nargs="+", help="TITLE or START_PAGE END_PAGE")
    parser.add_argument("--deploy", action="store_true", help="Upload to S3 after rebuild")
    args = parser.parse_args()

    volume = args.volume

    title = None
    start_page = None
    end_page = None
    if len(args.args) == 2 and args.args[0].isdigit() and args.args[1].isdigit():
        start_page = int(args.args[0])
        end_page = int(args.args[1])
    else:
        title = " ".join(args.args)

    # Look up the article before wiping
    session = SessionLocal()
    try:
        article = find_article(session, volume, title, start_page, end_page)
        article_title = article.title
        article_page_start = article.page_start
        article_page_end = article.page_end
        old_filename = _safe_filename(article, article.title)
    finally:
        session.close()

    print(f"Rebuilding: {article_title} (vol {volume}, pages {article_page_start}-{article_page_end})")
    print(f"Re-running full volume {volume} pipeline\n")

    print("Step 1: Running volume pipeline...")
    run_volume_pipeline(volume)

    # Find the article's filename after rebuild (should be the same)
    session = SessionLocal()
    try:
        article = find_article(session, volume, article_title, None, None)
        filename = _safe_filename(article, article.title)
    finally:
        session.close()

    print(f"\nRebuilt: data/derived/articles/{filename}")

    if args.deploy:
        print("\nStep 2: Deploying...")
        deploy_article(filename)

    print("\nDone.")


if __name__ == "__main__":
    main()
