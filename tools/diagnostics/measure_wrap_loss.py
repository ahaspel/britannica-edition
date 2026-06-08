"""Step 4 baseline: how many resolved prose xrefs does the export's
re-search wrap silently drop?  For each resolved qv/see/see_also ref,
replicate _wrap_resolved_xrefs_in_body's surface re-search; count the
misses — those are resolved links that never appear in the body and that
in-place linking will recover.

    uv run python tools/diagnostics/measure_wrap_loss.py 1
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, SourcePage, CrossReference
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.elements import (
    ElementContext, process_elements_tree)
from britannica.pipeline.stages.extract_contributors import strip_attributions
from britannica.pipeline.stages.resolve_xrefs import (
    build_resolution_index, resolve_one)
from britannica.xrefs.extractor import extract_xrefs
from britannica.export.article_json import (
    _clean_surface_for_matching, _looks_bibliographic)


def walk_body(session, article):
    segs = (session.query(ArticleSegment)
            .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == article.id)
            .order_by(ArticleSegment.sequence_in_article)
            .add_columns(SourcePage.page_number).all())
    if not segs:
        return ""
    joined = "".join(s.segment_text or "" for s, pn in segs)
    if not joined:
        return ""
    ctx = ElementContext(volume=article.volume, page_number=segs[0][1])
    return process_elements_tree(strip_attributions(joined), ctx)[0]


def main():
    vol = int(sys.argv[1])
    session = SessionLocal()
    arts = (session.query(Article).filter(Article.volume == vol)
            .order_by(Article.id).all())
    print(f"walking {len(arts)} articles...", flush=True)
    override = {a.id: walk_body(session, a) for a in arts}
    idx = build_resolution_index(session.query(Article).all(), corpus=override)

    resolved_prose = 0
    dropped = 0
    for a in arts:
        body = override[a.id]
        for m in extract_xrefs(body):
            if m["xref_type"] not in ("see", "see_also", "qv"):
                continue
            xr = CrossReference(
                article_id=a.id, surface_text=m["surface_text"],
                normalized_target=m["normalized_target"],
                xref_type=m["xref_type"])
            if resolve_one(xr, idx)[0] is None:
                continue  # unresolved is a different leak
            surf = m["surface_text"] or ""
            if m["xref_type"] in ("see", "see_also") and _looks_bibliographic(surf):
                continue
            if "«LN:" in surf:
                continue  # already a link at its own site
            surface_clean = _clean_surface_for_matching(surf)
            if len(surface_clean) < 3:
                continue
            resolved_prose += 1
            if not re.search(re.escape(surface_clean), body, re.IGNORECASE):
                dropped += 1

    pct = (100 * dropped // resolved_prose) if resolved_prose else 0
    print(f"\nvol {vol}: {resolved_prose} resolved prose refs eligible to wrap, "
          f"{dropped} dropped by the re-search ({pct}%)")
    print("in-place linking recovers all of these.")


if __name__ == "__main__":
    main()
