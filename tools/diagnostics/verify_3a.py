"""Stage 3a verify: resolving «LN» off the in-memory index must equal the
stored CrossReference resolution.  Runs export_articles_to_json twice over
the SAME fresh walk-body — once with link_index (resolve_one off the index),
once without (the stored target_article_id) — and diffs the JSON.

  0 differ → resolution successfully decoupled from the stored edge.

    uv run python tools/diagnostics/verify_3a.py 1
"""
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.export.article_json import export_articles_to_json
from britannica.pipeline.stages.elements import (
    ElementContext, process_elements_tree)
from britannica.pipeline.stages.extract_contributors import strip_attributions
from britannica.pipeline.stages.resolve_xrefs import build_resolution_index


def walk_body(session, article: Article) -> str:
    segs = (
        session.query(ArticleSegment)
        .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
        .filter(ArticleSegment.article_id == article.id)
        .order_by(ArticleSegment.sequence_in_article)
        .add_columns(SourcePage.page_number)
        .all()
    )
    if not segs:
        return ""
    joined = "".join(
        f"\x01PAGE:{pn}\x01{s.segment_text or ''}" for s, pn in segs)
    if not joined:
        return ""
    ctx = ElementContext(volume=article.volume, page_number=segs[0][1])
    return process_elements_tree(strip_attributions(joined), ctx)[0]


def main() -> None:
    vol = int(sys.argv[1])
    session = SessionLocal()
    arts = (session.query(Article)
            .filter(Article.volume == vol)
            .order_by(Article.id).all())
    print(f"walking {len(arts)} articles...", flush=True)
    override = {a.id: walk_body(session, a) for a in arts}
    print("building resolution index...", flush=True)
    idx = build_resolution_index(session.query(Article).all())

    with tempfile.TemporaryDirectory() as td:
        d_idx = Path(td) / "idx"
        d_db = Path(td) / "db"
        export_articles_to_json(vol, d_idx, body_override=override, link_index=idx)
        export_articles_to_json(vol, d_db, body_override=override)
        f1 = {p.name: p.read_text(encoding="utf-8") for p in d_idx.glob("*.json")}
        f2 = {p.name: p.read_text(encoding="utf-8") for p in d_db.glob("*.json")}
        names = sorted(set(f1) | set(f2))
        mism = sum(1 for n in names if f1.get(n, "") != f2.get(n, ""))
        print(f"\n{mism} of {len(names)} files differ "
              f"(index-resolution vs stored-resolution)")


if __name__ == "__main__":
    main()
