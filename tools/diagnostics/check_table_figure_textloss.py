"""Per-<table>-figure TEXT-preservation check, by flipped label (the check that
should have gated step 2 — `check_table_figure_producer` only checked IMAGES and
missed legend-text loss).  For each <table>-shaped element, compare OLD
(`_process_html_table`, today's real producer) vs NEW (the producer for the label
`_classify_table`/icl assigns), at the WORD level, and tally word-loss by label
so we can tell which figure shapes are text-safe to route away and which are not.
Non-plate.  Run with the flip either in or out — it recomputes the label itself."""
import io
import re
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import (
    classify_article, _to_legacy_registry,
)
from britannica.pipeline.stages.elements import _classify_table, _PRODUCER_DISPATCH
from britannica.pipeline.stages.elements._tables import _process_html_table

TT = lambda s: s
_WORD = re.compile(r"[A-Za-zÀ-ÿ]{2,}")
_PAGE = re.compile(r"\x01[^\x01]*\x01")
_MARK = frozenset("""img legend htmltable chem math verse pre outline page fn ln
sh sc br td tr th table vert nbsp emsp ensp width height align valign colspan
rowspan left right top bottom middle style class border bgcolor color nowrap px
center span div""".split())


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
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(ArticleSegment.segment_text.like("%<table%"))
            .distinct().order_by(Article.volume, Article.page_start).all())
    by_label = Counter()
    loss_by_label = Counter()
    lost_words_by_label = Counter()
    examples = {}
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
            if not ce.inner_registry:
                continue
            if Counter(x.label for x in ce.inner_registry.values()).get("IMAGE", 0) < 1:
                continue
            reg = _to_legacy_registry(ce.inner_registry)
            label = _classify_table(ce.raw, ce.inner_text, reg)
            disp = _PRODUCER_DISPATCH.get(label)
            if disp is None:
                continue
            try:
                old = _process_html_table(ce.raw, ce.inner_text, TT, reg)
                new = disp(ce.raw, ce.inner_text, TT, None, reg)
            except Exception:
                continue
            by_label[label] += 1
            lost = words(old) - words(new)
            if lost:
                loss_by_label[label] += 1
                lost_words_by_label[label] += sum(lost.values())
                ex = examples.setdefault(label, [])
                if len(ex) < 4:
                    ex.append((a.volume, a.page_start, a.title[:24],
                               sum(lost.values()), dict(lost.most_common(6))))

    print("\n=== <table> figure elements by flipped label: text-loss tally ===")
    for lbl, n in by_label.most_common():
        lossn = loss_by_label[lbl]
        print(f"  {lbl:26}  total={n:4}  lose-text={lossn:4}  "
              f"lost-word-instances={lost_words_by_label[lbl]}")
    print("\n=== examples ===")
    for lbl in loss_by_label:
        print(f"\n[{lbl}]")
        for v, p, t, cnt, lost in examples[lbl]:
            print(f"  {v:02d}-{p:04d} {t}  lost {cnt}: {lost}")


if __name__ == "__main__":
    main()
