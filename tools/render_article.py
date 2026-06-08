"""Re-render a single article's JSON with the current transform code.

Use this for fast iteration on transform / layout / element-handling
code changes: edit code, run ``render_article.py TITLE``, reload the
viewer in your browser.  Typical turnaround ~5 seconds.

This is intentionally narrow:

* No DB writes — body comes from the in-memory transform output, not
  persisted.  A subsequent full rebuild will overwrite anyway.
* No boundary / xref / contributor / image re-detection — those depend
  on volume-scope passes that don't change with transform-code edits.
  If you change ``corrections.json``, image extraction, contributor
  linking, etc., use ``tools/pipeline/rebuild_volume.py`` (which
  rebuilds the volume properly).
* No index rebuild — the viewer's article list already knows about
  this article; only its body changes.

For changes that DO affect boundaries / xrefs / images / contributors,
fall back to ``rebuild_volume.py`` (~2min per volume) or a full
rebuild.

Usage::

    uv run python tools/render_article.py LARVAL_FORMS
    uv run python tools/render_article.py "DIFFERENCES, CALCULUS OF"
    uv run python tools/render_article.py FUNGI 11   # disambiguate volume
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.export.article_json import (
    _safe_filename, export_articles_to_json,
)
from britannica.pipeline.stages.transform_articles import _transform_text_v2


def _find_article(session, title: str, volume: int | None) -> Article | None:
    title_norm = title.replace("_", " ").upper()
    q = session.query(Article)
    if volume is not None:
        q = q.filter(Article.volume == volume)
    # Exact match first.
    a = q.filter(Article.title == title_norm).first()
    if a:
        return a
    # Loose match: title containing the input.
    matches = q.filter(Article.title.ilike(f"%{title_norm}%")).all()
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Multiple matches for {title!r}:", file=sys.stderr)
        for m in matches[:20]:
            print(f"  vol {m.volume} p{m.page_start}: {m.title}",
                  file=sys.stderr)
        if len(matches) > 20:
            print(f"  ... ({len(matches) - 20} more)", file=sys.stderr)
        return None
    return None


def render(title: str, volume: int | None = None,
           out_dir: str = "data/derived/articles") -> Path | None:
    t0 = time.time()
    session = SessionLocal()
    try:
        article = _find_article(session, title, volume)
        if article is None:
            print(f"No article found for {title!r}"
                  + (f" in vol {volume}" if volume else ""),
                  file=sys.stderr)
            return None
        print(f"[{time.time()-t0:4.1f}s] {article.title} "
              f"(vol {article.volume}, p{article.page_start})")

        # Use ``segment_text`` (article-scoped, already filtered to
        # this article's portion of each page) joined with PAGE markers
        # — the same input ``transform_articles`` builds for the live
        # pipeline.  ``pg.wikitext`` is page-scoped and contains
        # adjacent articles' content too; joining those would
        # contaminate the transform output (LARVAL FORMS bug).
        import re as _re
        segs = (
            session.query(ArticleSegment)
            .join(SourcePage,
                  ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == article.id)
            .order_by(ArticleSegment.sequence_in_article)
            .add_columns(SourcePage.page_number)
            .all()
        )
        # Mirror production: segments already carry their «PAGE» marker (stamped
        # at detection) and the seam is healed upstream — just concatenate.
        joined_raw = "".join(seg.segment_text or "" for seg, page_number in segs)
        print(f"[{time.time()-t0:4.1f}s] Read {len(segs)} segments, "
              f"{len(joined_raw):,} chars")

        if article.article_type == "plate":
            from britannica.pipeline.stages.elements._figure_faithful import (
                produce_faithful_figure,
            )
            body = produce_faithful_figure(segs[0][0].segment_text or "") if segs else ""
        else:
            body = _transform_text_v2(
                joined_raw, volume=article.volume,
                page_number=segs[0][1] if segs else article.page_start,
            ) if joined_raw else ""
        print(f"[{time.time()-t0:4.1f}s] Transformed → {len(body):,} chars")
    finally:
        session.close()

    export_articles_to_json(
        article.volume, out_dir,
        body_override={article.id: body},
        only_article_id=article.id,
    )
    fn = _safe_filename(article, article.title)
    out_path = Path(out_dir) / fn
    print(f"[{time.time()-t0:4.1f}s] Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python tools/render_article.py TITLE [VOLUME]",
              file=sys.stderr)
        sys.exit(1)
    arg_title = sys.argv[1]
    arg_volume = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    if render(arg_title, arg_volume) is None:
        sys.exit(1)
