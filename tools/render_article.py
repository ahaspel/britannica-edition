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

from britannica.db.models import Article
from britannica.db.session import SessionLocal
from britannica.export.article_json import (
    _safe_filename, export_articles_to_json,
)
from britannica.pipeline.stages.transform_articles import walk_article


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

        # Mirror production EXACTLY: assemble_and_export walks every article —
        # plates included — through walk_article (segment-join with the carried
        # «PAGE» markers, footer strip, the ONE element walk, title split).  No
        # manual concatenation, no plate special-case, no transform shim.
        body = walk_article(session, article)
        print(f"[{time.time()-t0:4.1f}s] Walked → {len(body):,} chars")
        # No xref resolution.  A single-article re-render is for LOOKING at
        # layout / producer output, not the cross-reference web — and resolving
        # «LN» means loading the whole corpus (37k rows) to build the title
        # index, a 4-minute tax on a 0.4s walk.  Skip it; the export strips the
        # unresolved «LN» markers to their display text.
    finally:
        session.close()

    export_articles_to_json(
        article.volume, out_dir,
        body_override={article.id: body},
        link_index=None,   # look-render: skip xref resolution (see above)
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
