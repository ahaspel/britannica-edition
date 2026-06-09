"""Stage B of the single-pass export refactor — shadow the export off the walk.

B1: prove the body seam.  For one volume, run ``export_articles_to_json``
twice — once with the body sourced from the LIVE WALK (join segments with
page markers, ``strip_attributions``, ``process_elements_tree``), once from
the stored ``article.body`` — and diff the resulting JSON.

  * 0 differences  → the walk reproduces the export's body exactly; the seam
    is sound and the stored body is current.
  * any difference → the stored ``article.body`` is stale relative to the live
    walk.  Inspect with ``--diff N``; the divergence should be confined to the
    body-derived fields (``body`` / ``word_count`` / ``sections``), which the
    refactor legitimately freshens by always walking.

The tree from ``process_elements_tree`` is captured but unused at B1; B2+
read link / page / xref resolution off it instead of reparsing the body.

    uv run python tools/diagnostics/shadow_export.py 1
    uv run python tools/diagnostics/shadow_export.py 1 --diff 3
"""
from __future__ import annotations

import argparse
import difflib
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.export.article_json import export_articles_to_json
from britannica.pipeline.stages.elements import (
    ElementContext, process_elements_tree)


def walk_body(session, article: Article) -> tuple[str, dict]:
    """The article's body via the live walk path — the same bytes
    ``transform_articles`` writes today, sourced from the walk.  Returns
    ``(body, tree)``; the tree is for B2+ (resolution off the structure)."""
    segments = (
        session.query(ArticleSegment)
        .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
        .filter(ArticleSegment.article_id == article.id)
        .order_by(ArticleSegment.sequence_in_article)
        .add_columns(SourcePage.page_number)
        .all()
    )
    if not segments:
        return "", {}
    joined_raw = "".join(seg.segment_text or "" for seg, page_number in segments)
    if not joined_raw:
        return "", {}
    ctx = ElementContext(volume=article.volume, page_number=segments[0][1])
    return process_elements_tree(joined_raw, ctx)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("volume", type=int)
    ap.add_argument("--diff", type=int, default=0,
                    help="show up to N sample file diffs")
    args = ap.parse_args()

    session = SessionLocal()
    articles = (
        session.query(Article)
        .filter(Article.volume == args.volume)
        .order_by(Article.id)
        .all()
    )
    print(f"volume {args.volume}: {len(articles)} articles", flush=True)

    override: dict[int, str] = {}
    for i, a in enumerate(articles):
        body, _tree = walk_body(session, a)
        override[a.id] = body
        if (i + 1) % 200 == 0:
            print(f"  walked {i + 1}/{len(articles)}", flush=True)

    with tempfile.TemporaryDirectory() as td:
        walk_dir = Path(td) / "walk"
        stored_dir = Path(td) / "stored"
        export_articles_to_json(args.volume, walk_dir, body_override=override)
        export_articles_to_json(args.volume, stored_dir)

        wf = {p.name: p for p in walk_dir.glob("*.json")}
        sf = {p.name: p for p in stored_dir.glob("*.json")}
        names = sorted(set(wf) | set(sf))
        mism = 0
        shown = 0
        for n in names:
            tw = wf[n].read_text(encoding="utf-8") if n in wf else ""
            ts = sf[n].read_text(encoding="utf-8") if n in sf else ""
            if tw != ts:
                mism += 1
                if shown < args.diff:
                    shown += 1
                    print(f"\n=== {n} ===", flush=True)
                    for line in difflib.unified_diff(
                            ts.splitlines(), tw.splitlines(),
                            "stored", "walk", lineterm=""):
                        print(line, flush=True)

        print(f"\n{mism} of {len(names)} files differ "
              f"(walk-body vs stored article.body)", flush=True)


if __name__ == "__main__":
    main()
