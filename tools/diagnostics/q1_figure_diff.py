"""Q1 of the producer collapse: does `process_elements` handle everything the
figure producer's `render_markers`/`decompose` does?

For every figure-family element in the corpus, compare:
  A = produce_faithful_figure(raw)                       # current
  B = process_elements(raw, _apply_markup, ctx,          # candidate
                       _allow_figure=False)              # peel-for-comparison
Run with emitters ON, so a styled wrapper becomes «DIV» on BOTH sides — any
divergence is then a REAL structural gap in process_elements (a Q1 violation),
not the styled win (which is the separate Q2 payoff, invisible here).

  uv run python tools/diagnostics/q1_figure_diff.py        # summary + save diverging
  uv run python tools/diagnostics/q1_figure_diff.py show N  # print N diverging cases
"""
from __future__ import annotations
import io, json, re, sys
from collections import Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))
from _corpus_cache import load_corpus
OUT = ROOT / "tools" / "_scratch" / "q1_diverging.json"

FIG_LABELS = {
    "FIGURE", "IMAGE", "RAW_IMAGE", "PLAIN_IMAGE", "DJVU_CROP",
    "LAYOUT_WRAPPER", "UNPAIRED_FIGURE_GROUP", "FIGURE_GROUP",
    "CAPTIONED_FIGURE", "CAPTIONED_FIGURE_INLINE",
    "LEGENDED_FIGURE", "LEGENDED_FIGURE_BESIDE", "LEGENDED_FIGURE_CHILD",
}


def _norm(s: str) -> str:
    # collapse whitespace runs so spacing differences don't mask structure
    return re.sub(r"\s+", " ", s).strip()


def _work(item):
    aid, vol, pg0, raw = item
    from britannica.pipeline.stages.elements._classifier import classify_article
    from britannica.pipeline.stages.elements import (
        ElementContext, process_elements)
    from britannica.pipeline.stages.elements._figure_faithful import (
        produce_faithful_figure)
    from britannica.pipeline.stages.transform_articles.body_text import _apply_markup
    ctx = ElementContext(volume=vol, page_number=pg0)
    rows = []
    figs = []

    def collect(tree):
        for _ph, ce in tree.items():
            if ce.label in FIG_LABELS:
                figs.append(ce.raw)
            elif ce.inner_registry:
                collect(ce.inner_registry)
    try:
        _ph, tree = classify_article(raw)
        collect(tree)
    except Exception as e:
        return aid, [("CLASSIFY_ERR", str(e)[:80], "", "")]
    for fr in figs:
        try:
            a = produce_faithful_figure(fr)
        except Exception as e:
            rows.append(("RENDER_ERR", str(e)[:80], fr[:120], ""))
            continue
        try:
            b = process_elements(fr, _apply_markup, ctx, _allow_figure=False)
        except Exception as e:
            rows.append(("PE_ERR", str(e)[:80], fr[:120], ""))
            continue
        if _norm(a) != _norm(b):
            rows.append(("DIFF", fr[:160], a, b))
    return aid, rows


def main():
    corpus = list(load_corpus())
    with Pool(max(1, cpu_count() - 1)) as pool:
        results = pool.map(_work, corpus, chunksize=8)
    diverging = []
    kinds = Counter()
    total_figs = 0
    for aid, rows in results:
        for kind, *rest in rows:
            kinds[kind] += 1
            if kind == "DIFF":
                diverging.append({"aid": aid, "raw": rest[0],
                                  "render": rest[1], "pe": rest[2]})
    # count total figures examined (re-derive cheaply from the kinds + matches
    # is awkward; just report divergences)
    print(f"=== Q1 figure diff: {len(corpus)} articles ===")
    for k, n in kinds.most_common():
        print(f"  {n:6d}  {k}")
    OUT.write_text(json.dumps(diverging), encoding="utf-8")
    print(f"\n  saved {len(diverging)} diverging cases → {OUT.name}")


def show(n):
    data = json.loads(OUT.read_text(encoding="utf-8"))
    for d in data[:n]:
        print("=" * 70, f"\n[{d['aid']}] RAW:", repr(d["raw"][:200]))
        print("--- render_markers (A) ---"); print(repr(d["render"][:600]))
        print("--- process_elements (B) ---"); print(repr(d["pe"][:600]))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    else:
        main()
