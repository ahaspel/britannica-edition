"""What's actually IN LAYOUT_WRAPPER? (the figure/layout catch-all).  Walk the
corpus, find every LAYOUT_WRAPPER element, categorize each by structural shape +
chem content, tally, and show examples — to see what's a genuine un-pairable
multi-image figure (its principled role) vs what's leaked in (chem, verse,
single-image, math, nested, text)."""
import io
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import (
    classify_article, _to_legacy_registry)
from britannica.pipeline.stages.elements._registry import TABLE_LABELS
from britannica.pipeline.stages.elements._tables import (
    _table_grid, _has_chem_brackets, _has_chem_equation_content,
    _has_chem_reaction_content)


def walk(t):
    for ce in t.values():
        yield ce
        if ce.inner_registry:
            yield from walk(ce.inner_registry)


def cats(ce):
    reg = _to_legacy_registry(ce.inner_registry) if ce.inner_registry else None
    cc = Counter(x.label for x in (ce.inner_registry or {}).values())
    nimg = cc.get("IMAGE", 0)
    nfig = sum(cc.get(l, 0) for l in cc if l in TABLE_LABELS or "FIGURE" in l)
    inner = ce.inner_text or ""
    chem = bool(reg and (_has_chem_brackets(reg)
                or _has_chem_equation_content(ce.raw or "")
                or _has_chem_reaction_content(inner)))
    if chem:
        return "CHEM"
    if cc.get("POEM", 0) >= 1 and nimg == 0:
        return "VERSE (poem, no img)"
    if cc.get("MATH", 0) >= 2 or "<math" in inner.lower():
        return "MATH"
    if nimg >= 2:
        return "multi-image figure (≥2 img)"
    if nimg == 1:
        return "single-image figure (1 img)"
    if nfig >= 2:
        return "nested figure-group"
    grid = _table_grid(inner)
    if grid and all(len([c for c in r if c.strip()]) <= 1 for r in grid):
        return "single-column / text"
    return "other (multi-cell, no img)"


def main():
    s = SessionLocal()
    from sqlalchemy import or_
    arts = (s.query(Article).join(ArticleSegment,
            ArticleSegment.article_id == Article.id)
            .filter(or_(ArticleSegment.segment_text.like("%{|%"),
                        ArticleSegment.segment_text.like("%<table%")))
            .distinct().order_by(Article.volume, Article.page_start).all())
    by = Counter()
    ex = {}
    ex_other = []
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
            if ce.label != "LAYOUT_WRAPPER":
                continue
            c = cats(ce)
            by[c] += 1
            ex.setdefault(c, []).append((a.volume, a.page_start, a.title[:24]))
            if c == "other (multi-cell, no img)":
                snip = " ".join((ce.inner_text or "").split())[:150]
                ex_other.append((a.volume, a.page_start, a.title[:24], snip))
    print(f"\n=== LAYOUT_WRAPPER contents ({sum(by.values())} total) ===")
    for c, n in by.most_common():
        print(f"  {n:5}  {c}")
    print("\n=== 'other' inner snippets (hunting predicate-missed chem) ===")
    for v, p, t, snip in ex_other[:19]:
        print(f"\n   {v:02d}-{p:04d} {t}\n     {snip}")


if __name__ == "__main__":
    main()
