"""walker_snapshot.py — snapshot / diff the REAL `_transform_text_v2` output to
regression-check a recognizer or producer change.

Stores an md5 for EVERY article (so any unexpected change anywhere is caught) plus
the full output for articles whose raw bears one of the recognizers under test (so
the actual before/after diff can be shown).  Edit `_AFFECTED` to scope a given run.

  uv run python tools/diagnostics/walker_snapshot.py save snap_before.json
  # ...edit the recognizers...
  uv run python tools/diagnostics/walker_snapshot.py save snap_after.json
  uv run python tools/diagnostics/walker_snapshot.py diff snap_before.json snap_after.json
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")))

# Articles whose raw bears one of the migrated templates — full output is kept
# for these so their diffs are inspectable.  (Loose/over-inclusive is fine.)
_AFFECTED = re.compile(
    r"\[\[(?:File|Image):|\{\{\s*(?:raw\s+image|Css image crop)",
    re.IGNORECASE)


def _work(item):
    aid, vol, pg, raw = item
    from britannica.pipeline.stages.transform_articles import _transform_text_v2
    try:
        out = _transform_text_v2(raw, vol, pg)
    except Exception as e:                      # a crash is a change we must see
        out = f"__CRASH__{type(e).__name__}: {e}"
    h = hashlib.md5(out.encode("utf-8", "replace")).hexdigest()
    return aid, h, (out if _AFFECTED.search(raw) else None)


def save(outfile):
    from multiprocessing import Pool, cpu_count
    from _corpus_cache import load_corpus
    res = {}
    with Pool(max(1, cpu_count() - 1)) as pool:
        for aid, h, out in pool.imap_unordered(_work, load_corpus(), chunksize=64):
            res[aid] = [h, out]
    json.dump(res, open(outfile, "w", encoding="utf-8"), ensure_ascii=False)
    aff = sum(1 for v in res.values() if v[1] is not None)
    print(f"snapshot {len(res)} articles ({aff} template-bearing) -> {outfile}")


def _first_diff(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    s = max(0, i - 50)
    return a[s:i + 90], b[s:i + 90]


def diff(fa, fb):
    a = json.load(open(fa, encoding="utf-8"))
    b = json.load(open(fb, encoding="utf-8"))
    changed = [k for k in a if k in b and a[k][0] != b[k][0]]
    unexpected = [k for k in changed if a[k][1] is None]
    print(f"{len(changed)} of {len(a)} articles changed output")
    print(f"  template-bearing: {len(changed) - len(unexpected)}   "
          f"UNEXPECTED (non-bearing): {len(unexpected)}")
    for k in unexpected[:15]:
        print(f"  !! UNEXPECTED change in {k}")
    shown = 0
    for k in changed:
        if a[k][1] is None or b[k][1] is None or shown >= 25:
            continue
        shown += 1
        oa, ob = _first_diff(a[k][1], b[k][1])
        print(f"=== {k}")
        print(f"  before {oa!r}")
        print(f"  after  {ob!r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("save")
    p.add_argument("outfile")
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    args = ap.parse_args()
    if args.cmd == "save":
        save(args.outfile)
    else:
        diff(args.a, args.b)
