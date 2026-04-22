"""Re-process a single article and export it. For fast iteration.

Usage: uv run python tools/reprocess_article.py JAPAN 15
       uv run python tools/reprocess_article.py --id 1462316
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.export.article_json import (
    _leaf_for_ws, _printed_page, _safe_filename, stable_id,
)
from britannica.pipeline.stages.transform_articles import _transform_text_v2


def reprocess(article_id=None, title=None, volume=None):
    s = SessionLocal()
    try:
        if article_id:
            article = s.query(Article).filter(Article.id == article_id).first()
        else:
            article = (
                s.query(Article)
                .filter(Article.title == title.upper(), Article.volume == volume)
                .first()
            )
        if not article:
            print(f"Article not found")
            return

        segments = (
            s.query(ArticleSegment, SourcePage.page_number)
            .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == article.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )

        raw_parts = []
        for seg, pn in segments:
            raw = seg.segment_text or ""
            if not raw.strip():
                continue
            raw_parts.append(f"\x01PAGE:{pn}\x01{raw}")

        joined = "\n".join(raw_parts)
        joined = re.sub(r"(\w)-\n(\x01PAGE:\d+\x01)(\w)", r"\1\2\3", joined)

        body = _transform_text_v2(joined, article.volume, segments[0][1] if segments else 0)

        # Convert PAGE markers to printed page numbers
        body = re.sub(
            r"\x01PAGE:(\d+)\x01",
            lambda m: f"\x01PAGE:{_printed_page(article.volume, int(m.group(1)))}\x01",
            body,
        )

        out = {
            "id": article.id,
            "stable_id": stable_id(article),
            "title": article.title,
            "volume": article.volume,
            "page_start": _printed_page(article.volume, article.page_start),
            "page_end": _printed_page(article.volume, article.page_end),
            "ws_page_start": article.page_start,
            "ws_page_end": article.page_end,
            # Leaf fields are required by the viewer: scanUrl() builds
            # scans.html?vol=…&start=<leaf>&end=<leaf> for the top-of-
            # article vol:page link AND every left-margin page marker.
            # Omit them and every page-link locally clicks onto a URL
            # with start=undefined.
            "leaf_start": _leaf_for_ws(article.volume, article.page_start),
            "leaf_end": _leaf_for_ws(article.volume, article.page_end),
            "article_type": article.article_type or "article",
            "word_count": len(body.split()),
            "body": body,
            "cross_references": [],
            "contributors": [],
            "plates": [],
        }

        outpath = f"data/derived/articles/{_safe_filename(article, article.title)}"
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        tables = re.findall(r"\{\{TABLE:.*?\}TABLE\}", body, re.DOTALL)
        print(f"Wrote {outpath} ({len(body):,} chars, {len(tables)} tables)")

    finally:
        s.close()


if __name__ == "__main__":
    if "--id" in sys.argv:
        idx = sys.argv.index("--id")
        reprocess(article_id=int(sys.argv[idx + 1]))
    elif len(sys.argv) >= 3:
        reprocess(title=sys.argv[1], volume=int(sys.argv[2]))
    else:
        print("Usage: uv run python tools/reprocess_article.py JAPAN 15")
        print("       uv run python tools/reprocess_article.py --id 1462316")
