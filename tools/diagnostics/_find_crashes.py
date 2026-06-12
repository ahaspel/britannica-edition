"""Surface producer crashes across the corpus.

`leak_audit.py` swallows a producer crash as a bare `crash:Type` count.  This
re-runs the SAME live transform (`process_elements(preprocess(raw), …)`) and,
for every article that throws, groups by (exception type, crash site, message)
so each distinct failure shows its traceback and a few sample articles to pull.

    uv run python tools/diagnostics/_find_crashes.py
"""
from __future__ import annotations

import io
import os
import sys
import traceback
from collections import defaultdict
from multiprocessing import Pool, cpu_count

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")))
from _corpus_cache import load_corpus  # noqa: E402


def work(item):
    aid, vol, pg, raw = item
    from britannica.pipeline.stages.elements import (
        ElementContext, process_elements)
    from britannica.pipeline.stages.preprocess import preprocess
    try:
        process_elements(preprocess(raw),
                         ElementContext(volume=vol, page_number=pg))
        return None
    except Exception as e:  # noqa: BLE001 — we WANT every throw
        return (aid, vol, pg, type(e).__name__, str(e), traceback.format_exc())


if __name__ == "__main__":
    items = list(load_corpus())
    with Pool(cpu_count()) as p:
        results = [r for r in p.imap_unordered(work, items, chunksize=200) if r]
    sigs: dict = defaultdict(list)
    for aid, vol, pg, et, em, tb in results:
        frames = [l.strip() for l in tb.splitlines()
                  if l.strip().startswith("File ")]
        last = frames[-1] if frames else "?"
        sigs[(et, last, em[:90])].append((aid, vol, pg, tb))
    print(f"TOTAL crashes: {len(results)} | distinct signatures: {len(sigs)}")
    for key, group in sorted(sigs.items(), key=lambda x: -len(x[1])):
        et, last, msg = key
        print(f"\n=== {len(group)}x  {et}: {msg}")
        print(f"    {last}")
        for line in group[0][3].strip().splitlines()[-7:]:
            print("   ", line)
        print("    samples (aid,vol,pg):",
              [(a, v, p) for a, v, p, _ in group[:6]])
