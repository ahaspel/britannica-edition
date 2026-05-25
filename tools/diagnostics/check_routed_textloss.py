"""Content-preservation gate for the MATH/CHEM `<table>` routing: for each
`<table>` element that now routes to MATH_LAYOUT_*/CHEMISTRY_LAYOUT, compare OLD
(`_process_html_table` = the prior «HTMLTABLE) vs NEW (the routed producer) at
the WORD level, and report any that LOSE real words.  Catches the BLINDNESS
tall-brace-style degradation if it drops content."""
import io
import re
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import (
    classify_article, _to_legacy_registry)
from britannica.pipeline.stages.elements import _classify_table, _PRODUCER_DISPATCH
from britannica.pipeline.stages.elements._tables import _process_html_table

TT = lambda s: s
TARGETS = {"MATH_LAYOUT_EQUATIONS", "MATH_LAYOUT_TOKENS", "CHEMISTRY_LAYOUT", "SINGLE_COLUMN_TABLE", "VERSE_TABLE"}
_WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]{2,}")
_PAGE = re.compile(r"\x01[^\x01]*\x01")
_MARK = frozenset("""math htmltable chem table tr td th caption width align
colspan rowspan style class border nbsp vert big sub sup""".split())


def words(t):
    return Counter(w for w in _WORD.findall(_PAGE.sub(" ", t).lower())
                   if w not in _MARK)


def walk(t):
    for ce in t.values():
        yield ce
        if ce.inner_registry:
            yield from walk(ce.inner_registry)


def main():
    s = SessionLocal()
    arts = (s.query(Article).join(ArticleSegment,
            ArticleSegment.article_id == Article.id)
            .filter(ArticleSegment.segment_text.like("%<table%"))
            .distinct().order_by(Article.volume, Article.page_start).all())
    tally = Counter()
    losers = []
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
            if not (ce.raw or "").lstrip().lower().startswith("<table"):
                continue
            reg = _to_legacy_registry(ce.inner_registry) if ce.inner_registry else None
            label = _classify_table(ce.raw, ce.inner_text, reg)
            if label not in TARGETS:
                continue
            try:
                old = _process_html_table(ce.raw, ce.inner_text, TT, reg)
                new = _PRODUCER_DISPATCH[label](ce.raw, ce.inner_text, TT, None, reg)
            except Exception as e:  # noqa: BLE001
                tally[f"{label} ERROR:{type(e).__name__}"] += 1
                continue
            tally[label] += 1
            lost = words(old) - words(new)
            if lost:
                losers.append((sum(lost.values()), label,
                               f"{a.volume:02d}-{a.page_start:04d} {a.title[:22]}",
                               dict(lost.most_common(8))))
    print("\n=== <table> MATH/CHEM routed (by label) ===")
    for k, n in tally.most_common():
        print(f"  {n:4}  {k}")
    print(f"\n=== word-loss cases ({len(losers)}) ===")
    for cnt, label, title, lost in sorted(losers, key=lambda x: x[0], reverse=True)[:20]:
        print(f"  [{label}] {title}  lost {cnt}: {lost}")


if __name__ == "__main__":
    main()
