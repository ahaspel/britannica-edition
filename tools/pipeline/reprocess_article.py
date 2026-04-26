"""Re-process a single article via the full per-volume pipeline.

Faithfully replicates rebuild_all.sh for the article's volume so local
testing matches what a full rebuild would produce. Wipes the volume's
articles, re-applies corrections.json to wikitext, re-detects
boundaries, re-transforms, and re-exports.

Use this whenever you need iteration to reflect:
  - corrections.json edits (clean-pages applies to wikitext)
  - title/boundary changes (detect-boundaries re-runs)
  - body code changes (transform-articles re-runs)

Cost: ~30-90s per call (per-volume detect + transform + export).

Usage: uv run python tools/pipeline/reprocess_article.py TITLE VOLUME
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment
from britannica.db.models.article_image import ArticleImage
from britannica.db.models.contributor import ArticleContributor
from britannica.db.models.cross_reference import CrossReference
from britannica.db.session import SessionLocal
from britannica.export.article_json import export_articles_to_json
from britannica.pipeline.stages.clean_pages import clean_pages
from britannica.pipeline.stages.detect_boundaries import (
    detect_boundaries,
    persist_articles,
)
from britannica.pipeline.stages.transform_articles import transform_articles
from sqlalchemy import delete, select


def _wipe_volume_articles(volume: int) -> int:
    """Delete all articles + dependents for a volume; preserve
    source_pages so we don't have to re-import."""
    s = SessionLocal()
    try:
        art_ids = [
            a[0] for a in s.execute(
                select(Article.id).where(Article.volume == volume)
            ).all()
        ]
        if not art_ids:
            return 0
        # Cross-references targeting this volume's articles need to
        # have target nulled (FK constraint), then any CRs originating
        # in this volume can be deleted outright.
        s.execute(
            CrossReference.__table__.update()
            .where(CrossReference.target_article_id.in_(art_ids))
            .values(target_article_id=None, status="unresolved")
        )
        s.execute(
            delete(CrossReference)
            .where(CrossReference.article_id.in_(art_ids))
        )
        s.execute(
            delete(ArticleContributor)
            .where(ArticleContributor.article_id.in_(art_ids))
        )
        s.execute(
            delete(ArticleImage)
            .where(ArticleImage.article_id.in_(art_ids))
        )
        s.execute(
            delete(ArticleSegment)
            .where(ArticleSegment.article_id.in_(art_ids))
        )
        s.execute(delete(Article).where(Article.id.in_(art_ids)))
        s.commit()
        return len(art_ids)
    finally:
        s.close()


def reprocess(title: str, volume: int) -> None:
    title_upper = title.upper()

    t0 = time.time()
    print(f"[{time.time()-t0:5.1f}s] Wiping vol {volume} articles…")
    n = _wipe_volume_articles(volume)
    print(f"[{time.time()-t0:5.1f}s]   Deleted {n} articles")

    print(f"[{time.time()-t0:5.1f}s] Cleaning pages "
          f"(applies corrections.json to wikitext)…")
    n = clean_pages(volume)
    print(f"[{time.time()-t0:5.1f}s]   Cleaned {n} pages")

    print(f"[{time.time()-t0:5.1f}s] Detecting boundaries…")
    detected = detect_boundaries(volume)
    print(f"[{time.time()-t0:5.1f}s]   Detected {len(detected)} articles")
    persist_articles(detected)

    print(f"[{time.time()-t0:5.1f}s] Transforming articles…")
    n = transform_articles(volume)
    print(f"[{time.time()-t0:5.1f}s]   Transformed {n} articles")

    print(f"[{time.time()-t0:5.1f}s] Exporting volume {volume} to JSON…")
    n = export_articles_to_json(volume, "data/derived/articles")
    print(f"[{time.time()-t0:5.1f}s]   Exported {n} articles")

    # Locate the article in the freshly-rebuilt set and report its
    # output filename so the caller can inspect it.
    s = SessionLocal()
    try:
        article = (
            s.query(Article)
            .filter(Article.volume == volume,
                    Article.title == title_upper)
            .first()
        )
        if not article:
            articles = (
                s.query(Article)
                .filter(Article.volume == volume,
                        Article.title.ilike(f"%{title}%"))
                .order_by(Article.page_start)
                .all()
            )
            if len(articles) == 1:
                article = articles[0]
                print(f"[{time.time()-t0:5.1f}s] Fuzzy match: "
                      f"{article.title!r}")
            elif len(articles) > 1:
                print(f"[{time.time()-t0:5.1f}s] Multiple matches:")
                for a in articles:
                    print(f"    p{a.page_start}: {a.title}")
                return
            else:
                print(f"[{time.time()-t0:5.1f}s] "
                      f"No article matching {title!r}")
                return
    finally:
        s.close()

    # Match export_articles_to_json's filename scheme
    from britannica.export.article_json import _safe_filename
    fn = _safe_filename(article, article.title)
    out = Path("data/derived/articles") / fn
    if out.exists():
        size = out.stat().st_size
        print(f"[{time.time()-t0:5.1f}s] OK  {out}  ({size:,} bytes)")
    else:
        print(f"[{time.time()-t0:5.1f}s] WARN  expected {out}  (not found)")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        reprocess(title=sys.argv[1], volume=int(sys.argv[2]))
    else:
        print("Usage: uv run python tools/pipeline/reprocess_article.py "
              "TITLE VOLUME")
        sys.exit(1)
