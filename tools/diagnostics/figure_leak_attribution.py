"""Test the hypothesis: with the style emitters OFF, what fraction of the raw
`{{template` leaks live inside FIGURE output (render_markers) vs prose?

If render_markers is the roach motel, most leaks should attribute to figures —
because it flattens figure prose through `_tt_br` instead of recursing the
stylers as elements.  Run with emitters disabled corpus-wide.

  uv run python tools/diagnostics/figure_leak_attribution.py
"""
from __future__ import annotations
import io, os, re, sys
from collections import Counter
from multiprocessing import Pool, cpu_count

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
from _corpus_cache import load_corpus  # noqa: E402

LEAK_RE = re.compile(r"\{\{\s*([A-Za-z][\w. -]*?)\s*[|}]")
FIG_LABELS = {
    "FIGURE", "IMAGE", "RAW_IMAGE", "PLAIN_IMAGE", "DJVU_CROP", "IMAGE_FLOAT",
    "LAYOUT_WRAPPER", "UNPAIRED_FIGURE_GROUP", "FIGURE_GROUP",
    "CAPTIONED_FIGURE", "CAPTIONED_FIGURE_INLINE",
    "LEGENDED_FIGURE", "LEGENDED_FIGURE_BESIDE", "LEGENDED_FIGURE_CHILD",
}


def _work(item):
    aid, vol, pg, raw = item
    import britannica.pipeline.stages.transform_articles.body_text as bt
    bt._EMIT_STYLE_WRAPPERS = False
    from britannica.pipeline.stages.transform_articles import _transform_text_v2
    from britannica.pipeline.stages.elements._classifier import classify_article
    from britannica.pipeline.stages.elements._figure_faithful import (
        produce_faithful_figure)
    try:
        out = _transform_text_v2(raw, vol, pg)
    except Exception:
        return (0, 0, Counter(), Counter())
    total = Counter(n.strip().lower() for n in LEAK_RE.findall(out))
    if not total:
        return (0, 0, Counter(), Counter())
    figc = Counter()
    try:
        _ph, tree = classify_article(raw)

        def collect(t):
            for _k, ce in t.items():
                if ce.label in FIG_LABELS:
                    yield ce.raw
                if ce.inner_registry:
                    yield from collect(ce.inner_registry)
        for fr in collect(tree):
            try:
                fo = produce_faithful_figure(fr)
            except Exception:
                continue
            figc.update(n.strip().lower() for n in LEAK_RE.findall(fo))
    except Exception:
        pass
    return (sum(total.values()), sum(figc.values()), total, figc)


def main():
    corpus = list(load_corpus())
    with Pool(max(1, cpu_count() - 1)) as pool:
        res = pool.map(_work, corpus, chunksize=8)
    total = sum(r[0] for r in res)
    fig = sum(min(r[1], r[0]) for r in res)  # figure leaks can't exceed total
    total_c, fig_c = Counter(), Counter()
    for _t, _f, tc, fc in res:
        total_c.update(tc)
        fig_c.update(fc)
    print(f"=== --no-emitters leak attribution ({len(corpus)} articles) ===")
    print(f"total raw {{{{template leaks:  {total}")
    print(f"inside figure output:       {fig}  ({100*fig/max(1,total):.0f}%)")
    print("\ntop leak templates  (figure-output count / total count):")
    for name, tc in total_c.most_common(16):
        print(f"  {fig_c[name]:5d} / {tc:5d}   {{{{{name}")


if __name__ == "__main__":
    main()
