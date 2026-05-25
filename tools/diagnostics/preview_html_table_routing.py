"""ROUTING-FLIP PREVIEW for the `<table>` path (Phase 2 step 3 dry run).

Today `<table>` flatly -> HTML_TABLE (`_derive_html_tag_label`).  Step 3 routes
it through the shape classifiers (`_classify_table`) instead, so disguised
non-tables (figure/verse/chem/math/single-col) LEAVE the table path.  This
script previews that flip WITHOUT changing routing: for every element currently
labeled HTML_TABLE, it computes
  * shape()      -- the content-based oracle (what it REALLY is), and
  * flip_label   -- what `_classify_table` WOULD assign,
then cross-tabulates oracle x flip_label so we can see, per disguised shape,
whether the shape classifiers route it away — and where genuine grids land
(they must NOT fall to the DATA_TABLE catch-all; the `<table>` genuine-grid
home is HTML_TABLE).  Non-plate, flushed."""
import io
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import or_
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import (
    classify_article, _to_legacy_registry,
)
from britannica.pipeline.stages.elements import _classify_table
from britannica.pipeline.stages.elements._tables import (
    _table_grid, _chem_row_is_reaction,
)


def walk(t):
    for ce in t.values():
        yield ce
        if ce.inner_registry:
            yield from walk(ce.inner_registry)


def child_counts(ce):
    c = Counter()
    if ce.inner_registry:
        for x in ce.inner_registry.values():
            c[x.label] += 1
    return c


def shape(ce):
    cc = child_counts(ce)
    if cc.get("IMAGE", 0) >= 1:
        return "FIGURE"
    if cc.get("POEM", 0) >= 1:
        return "VERSE"
    grid = _table_grid(ce.inner_text)
    for row in grid:
        if _chem_row_is_reaction(" ".join(row)):
            return "CHEM"
    if cc.get("MATH", 0) >= 2 or "<math" in ce.inner_text.lower():
        return "MATH"
    if grid and all(len([c for c in row if c.strip()]) <= 1 for row in grid):
        return "SINGLE-COLUMN"
    return "genuine grid"


def flip(ce):
    """What _classify_table would assign if `<table>` were routed through it."""
    try:
        reg = _to_legacy_registry(ce.inner_registry) if ce.inner_registry else None
        return _classify_table(ce.raw, ce.inner_text, reg)
    except Exception as e:  # noqa: BLE001
        return f"ERROR:{type(e).__name__}"


def main():
    s = SessionLocal()
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(ArticleSegment.segment_text.like("%<table%"))
            .distinct().order_by(Article.volume, Article.page_start).all())
    cross = Counter()           # (oracle_shape, flip_label) -> n
    ex = {}
    cur = None
    for a in arts:
        if a.article_type == "plate":
            continue
        if a.volume != cur:
            cur = a.volume
            print(f"  vol {cur}", flush=True)
        segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                .order_by(ArticleSegment.sequence_in_article).all())
        body = "\n\n".join(x.segment_text or "" for x in segs)
        try:
            _ph, tree = classify_article(body)
        except Exception:
            continue
        for ce in walk(tree):
            if ce.label != "HTML_TABLE":
                continue
            sh = shape(ce)
            fl = flip(ce)
            cross[(sh, fl)] += 1
            ex.setdefault((sh, fl), []).append(
                (a.volume, a.page_start, a.title[:22]))

    print("\n=== HTML_TABLE routing-flip preview (oracle shape -> flip label) ===")
    shapes = ["FIGURE", "VERSE", "CHEM", "MATH", "SINGLE-COLUMN", "genuine grid"]
    for sh in shapes:
        sub = {k: v for k, v in cross.items() if k[0] == sh}
        tot = sum(sub.values())
        if not tot:
            continue
        print(f"\n[{sh}]  ({tot})")
        for (s_, fl), n in sorted(sub.items(), key=lambda x: -x[1]):
            print(f"    {n:5}  -> {fl}")
    # surface the worrying cells with examples
    print("\n--- examples for review ---")
    TABLE_LIKE = {"DATA_TABLE", "COMPLEX_HTML", "HTML_TABLE"}
    for (sh, fl), n in sorted(cross.items(), key=lambda x: -x[1]):
        # interesting = disguised non-table NOT leaving, or genuine grid leaving
        bad = ((sh != "genuine grid" and fl in TABLE_LIKE)
               or (sh == "genuine grid" and fl not in TABLE_LIKE)
               or fl.startswith("ERROR"))
        if not bad:
            continue
        print(f"[{sh} -> {fl}]  ({n})")
        for v, p, t in ex[(sh, fl)][:4]:
            print(f"   {v:02d}-{p:04d} {t}")


if __name__ == "__main__":
    main()
