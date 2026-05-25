"""PRODUCER-on-<table> validation (step 2).  The classifier preview proved the
flip ROUTES <table> figures to ICL labels; this proves the (now _table_grid-
based) ICL PRODUCERS actually render those <table> figures — comparing the new
ICL-producer output against today's buried `_unwrap_html_illustration` output
for the same element, WITHOUT changing routing.

Per <table> figure element it reports:
  OLD = _unwrap_html_illustration(...)           (today's buried branch)
  NEW = <ICL producer for _classify_icl_shape>   (the flip's target)
and tallies: does NEW emit an {{IMG:}}? is OLD's image filename preserved in
NEW? (content-preservation).  Prints a few side-by-side samples.  Non-plate."""
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
from britannica.pipeline.stages.elements import (
    _classify_icl_shape, _PRODUCER_DISPATCH,
)
from britannica.pipeline.stages.elements._tables import _unwrap_html_illustration

TT = lambda s: s  # identity text_transform — enough to check structure/content


def walk(t):
    for ce in t.values():
        yield ce
        if ce.inner_registry:
            yield from walk(ce.inner_registry)


def imgs(text):
    return set(re.findall(r"\{\{IMG[^:]*:([^|}]+)", text))


def main():
    s = SessionLocal()
    arts = (s.query(Article)
            .join(ArticleSegment, ArticleSegment.article_id == Article.id)
            .filter(ArticleSegment.segment_text.like("%<table%"))
            .distinct().order_by(Article.volume, Article.page_start).all())
    tally = Counter()
    samples = []
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
            if ce.label != "HTML_TABLE" or not ce.inner_registry:
                continue
            cc = Counter(x.label for x in ce.inner_registry.values())
            if cc.get("IMAGE", 0) < 1:
                continue  # only the FIGURE shape
            reg = _to_legacy_registry(ce.inner_registry)
            icl = _classify_icl_shape(ce.raw, ce.inner_text, reg)
            if icl is None or icl not in _PRODUCER_DISPATCH:
                tally[f"no-icl-route ({icl})"] += 1
                continue
            try:
                old = _unwrap_html_illustration(ce.inner_text, TT, reg)
            except Exception as e:  # noqa: BLE001
                old = f"<<OLD-ERR:{type(e).__name__}>>"
            try:
                new = _PRODUCER_DISPATCH[icl](ce.raw, ce.inner_text, TT, None, reg)
            except Exception as e:  # noqa: BLE001
                new = f"<<NEW-ERR:{type(e).__name__}:{e}>>"
            oi, ni = imgs(old), imgs(new)
            if new.startswith("<<NEW-ERR"):
                tally["NEW-ERROR"] += 1
            elif not ni:
                tally["NEW-no-IMG"] += 1
            elif oi <= ni:
                tally["NEW>=OLD images (good)"] += 1
            else:
                tally["NEW drops some OLD image (REVIEW)"] += 1
                if len(samples) < 8:
                    samples.append((a.volume, a.page_start, a.title, icl,
                                    sorted(oi - ni), old[:300], new[:300]))

    print("\n=== producer-on-<table> tally ===")
    for k, n in tally.most_common():
        print(f"  {n:5}  {k}")
    print("\n=== samples where NEW drops an OLD image (review) ===")
    for v, p, t, icl, missing, old, new in samples:
        print(f"\n[{v:02d}-{p:04d} {t}]  icl={icl}  missing={missing}")
        print(f"  OLD: {old!r}")
        print(f"  NEW: {new!r}")


if __name__ == "__main__":
    main()
