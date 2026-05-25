"""TABLE-PATH PURITY SCAN.  For everything that reaches a table producer
(DATA_TABLE -> _process_table, HTML_TABLE -> _process_html_table, COMPLEX_HTML
-> _process_complex_table), apply the strip-the-grid test: is it a genuine
load-bearing grid, or a non-table wearing table syntax?  Non-table detectors
(syntax-aware via _table_grid, so {| and <table> both work):
  FIGURE  = an IMAGE child
  VERSE   = a POEM child
  CHEM    = a row that's an element-formula reaction
  MATH    = >=2 MATH children or <math> content
  SINGLE-COLUMN = every row has <=1 content cell (really PRE text)
  else    = genuine grid
Reports per-label shape breakdown = the remaining impurity, by syntax path.
Non-plate, flushed."""
import io
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import or_
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import classify_article
from britannica.pipeline.stages.elements._tables import (
    _table_grid, _chem_row_is_reaction,
)

TABLE_PATH = {"DATA_TABLE", "HTML_TABLE", "COMPLEX_HTML"}


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
        return "FIGURE (image child)"
    if cc.get("POEM", 0) >= 1:
        return "VERSE (poem child)"
    grid = _table_grid(ce.inner_text)
    for row in grid:
        if _chem_row_is_reaction(" ".join(row)):
            return "CHEM (reaction)"
    if cc.get("MATH", 0) >= 2 or "<math" in ce.inner_text.lower():
        return "MATH"
    if grid and all(len([c for c in row if c.strip()]) <= 1 for row in grid):
        return "SINGLE-COLUMN (PRE)"
    return "genuine grid"


def main():
    s = SessionLocal()
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(or_(ArticleSegment.segment_text.like("%{|%"),
                        ArticleSegment.segment_text.like("%<table%")))
            .distinct().order_by(Article.volume, Article.page_start).all())
    by = Counter()
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
            if ce.label not in TABLE_PATH:
                continue
            sh = shape(ce)
            by[(ce.label, sh)] += 1
            ex.setdefault((ce.label, sh), []).append(
                (a.volume, a.page_start, a.title[:22]))
    print("\n=== TABLE-PATH PURITY (label x shape) ===")
    for label in ("DATA_TABLE", "COMPLEX_HTML", "HTML_TABLE"):
        sub = {k: v for k, v in by.items() if k[0] == label}
        tot = sum(sub.values())
        grid = sub.get((label, "genuine grid"), 0)
        print(f"\n{label}: {tot} total, {grid} genuine grid "
              f"({100*grid//max(1,tot)}% pure)")
        for (lbl, sh), n in sorted(sub.items(), key=lambda x: -x[1]):
            tag = "" if sh == "genuine grid" else "  <-- NON-TABLE"
            print(f"    {n:5}  {sh}{tag}")
    print("\n--- non-table examples in the table path ---")
    for (lbl, sh), n in sorted(by.items(), key=lambda x: -x[1]):
        if sh == "genuine grid":
            continue
        print(f"[{lbl} / {sh}]  ({n})")
        for v, p, t in ex[(lbl, sh)][:3]:
            print(f"   {v:02d}-{p:04d} {t}")


if __name__ == "__main__":
    main()
