"""Step 4: how many prose links does longest-resolving-prefix recover that
the extractor's _TARGET_TAIL span guess misses?  For each article, compare
the set of resolved target ids from the current extract_xrefs against the
set found by scanning see/cf/compare triggers and taking the longest prefix
after the trigger that resolves against the index.  Reports the net-new.

NOTE: an upper bound — a prefix that happens to resolve isn't always a real
reference; treat the number as "candidates recovered", to be confirmed.

    uv run python tools/diagnostics/measure_prefix_recovery.py 1
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, SourcePage, CrossReference
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.elements import (
    ElementContext, process_elements_tree)
from britannica.pipeline.stages.resolve_xrefs import (
    build_resolution_index, resolve_one)
from britannica.xrefs.extractor import extract_xrefs, _strip_markers
from britannica.xrefs.normalizer import normalize_xref_target

_TRIGGER = re.compile(r"\b(?:[Ss]ee\s+also|[Ss]ee|[Cc]f\.|[Cc]ompare)\s+")


def walk_body(session, article):
    segs = (session.query(ArticleSegment)
            .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == article.id)
            .order_by(ArticleSegment.sequence_in_article)
            .add_columns(SourcePage.page_number).all())
    if not segs:
        return ""
    joined = "".join(s.segment_text or "" for s, pn in segs)
    ctx = ElementContext(volume=article.volume, page_number=segs[0][1])
    return process_elements_tree(joined, ctx)[0] if joined else ""


def _resolve(text, aid, idx):
    nt = normalize_xref_target(text)
    if not nt:
        return None
    xr = CrossReference(article_id=aid, surface_text=text,
                        normalized_target=nt, xref_type="see")
    return resolve_one(xr, idx)[0]


def current_ids(body, aid, idx):
    out = set()
    for m in extract_xrefs(body):
        xr = CrossReference(article_id=aid, surface_text=m["surface_text"],
                            normalized_target=m["normalized_target"],
                            xref_type=m["xref_type"])
        r = resolve_one(xr, idx)[0]
        if r is not None:
            out.add(r)
    return out


def prefix_ids(stripped, aid, idx):
    out = set()
    for m in _TRIGGER.finditer(stripped):
        after = stripped[m.end(): m.end() + 80]
        words = re.findall(r"[\w'’.\-]+", after)[:6]
        for k in range(len(words), 0, -1):
            r = _resolve(" ".join(words[:k]), aid, idx)
            if r is not None:
                out.add(r)
                break
    return out


def main():
    vol = int(sys.argv[1])
    session = SessionLocal()
    arts = (session.query(Article).filter(Article.volume == vol)
            .order_by(Article.id).all())
    print(f"walking {len(arts)} articles...", flush=True)
    override = {a.id: walk_body(session, a) for a in arts}
    idx = build_resolution_index(session.query(Article).all(), corpus=override)

    cur_total = recovered = 0
    for a in arts:
        body = override[a.id]
        cur = current_ids(body, a.id, idx)
        pre = prefix_ids(_strip_markers(body), a.id, idx)
        cur_total += len(cur)
        recovered += len(pre - cur)

    print(f"\nvol {vol}: {cur_total} targets resolved today; "
          f"longest-prefix adds {recovered} net-new candidates")


if __name__ == "__main__":
    main()
