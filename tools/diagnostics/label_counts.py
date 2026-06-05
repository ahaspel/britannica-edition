"""Fast corpus-wide label-count histogram — the classification regression
meter for the flagless-recursion campaign.  Parallel `classify_article` over
the cached raw corpus; counts every ClassifiedElement label.  Robust to tree
shape changes (we count labels, not tree paths), so it cleanly answers
"did CHEM/MATH/FIGURE drop when I changed a recognizer?".

  uv run python tools/diagnostics/label_counts.py before     # → label_counts.before.json
  uv run python tools/diagnostics/label_counts.py after
  uv run python tools/diagnostics/label_counts.py --diff before after
"""
from __future__ import annotations
import io, json, sys
from collections import Counter
from multiprocessing import Pool, cpu_count
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))
from _corpus_cache import load_corpus
SCRATCH = ROOT / "tools" / "_scratch"


def _walk(tree) -> Counter:
    c: Counter = Counter()
    for _ph, ce in tree.items():
        if ce.label:
            c[ce.label] += 1
        if ce.inner_registry:
            c += _walk(ce.inner_registry)
    return c


def _work(item):
    aid, vol, pg0, raw = item
    from britannica.pipeline.stages.elements._classifier import classify_article
    try:
        _ph, tree = classify_article(raw)
        return _walk(tree)
    except Exception:
        return Counter()


def _path(tag: str) -> Path:
    return SCRATCH / f"label_counts.{tag}.json"


def diff(a: str, b: str) -> None:
    ha = Counter(json.loads(_path(a).read_text(encoding="utf-8")))
    hb = Counter(json.loads(_path(b).read_text(encoding="utf-8")))
    labels = sorted(set(ha) | set(hb))
    print(f"{'label':32s} {a:>9s} {b:>9s} {'Δ':>8s}")
    print("-" * 62)
    for lbl in labels:
        da, db = ha.get(lbl, 0), hb.get(lbl, 0)
        if da != db:
            flag = "   <-- DROP" if db < da else "   <-- rise"
            print(f"{lbl:32s} {da:9d} {db:9d} {db-da:+8d}{flag}")
    print("-" * 62)
    print(f"{'TOTAL':32s} {sum(ha.values()):9d} {sum(hb.values()):9d} "
          f"{sum(hb.values())-sum(ha.values()):+8d}")


def main():
    if sys.argv[1] == "--diff":
        diff(sys.argv[2], sys.argv[3])
        return
    tag = sys.argv[1]
    corpus = list(load_corpus())
    with Pool(max(1, cpu_count() - 1)) as pool:
        parts = pool.map(_work, corpus, chunksize=16)
    total: Counter = Counter()
    for p in parts:
        total += p
    _path(tag).write_text(json.dumps(dict(total), indent=0), encoding="utf-8")
    print(f"{tag}: {sum(total.values())} elements, {len(total)} labels "
          f"over {len(corpus)} articles → {_path(tag).name}")


if __name__ == "__main__":
    main()
