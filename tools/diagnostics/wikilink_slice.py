"""wikilink_slice.py — give the leaking-`[[wikilink]]` bucket a SHAPE.

The leak audit reports ~3,982 raw `[[…]]` surviving into final output (the single
biggest BROKEN category).  But "wikilink" is not one thing: a plain `[[Article]]`
cross-reference (should become «LN»), a `[[Author:Jan Hus]]` namespace link, a
`[[1911 Encyclopædia Britannica/Foo]]` self-reference, and a `[[Bible (King
James)/…]]` scripture link are four different producers.  This slices the bucket so
the work can be scoped.

Reuses leak_audit's `_mask_final_form` so we count only the SURVIVORS (markers,
images, tables, page sentinels already masked) — exactly the audit's leak set.

  uv run python tools/diagnostics/wikilink_slice.py
  uv run python tools/diagnostics/wikilink_slice.py --volume 5
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool, cpu_count

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")))
from _corpus_cache import load_corpus       # noqa: E402

# Final-form masks (inlined from leak_audit so we count only SURVIVORS —
# importing it double-wraps sys.stdout, which closes the buffer on GC).
_MARKER_RE = re.compile(r"«[^»]*»")
_IMG_MARKER_RE = re.compile(r"\{\{IMG:[^{}]*\}\}", re.IGNORECASE)
_VERSE_MARKER_RE = re.compile(r"\{\{verse:.*?\}\}", re.IGNORECASE | re.DOTALL)
_PAGE_RE = re.compile(r"\x01PAGE:\d+\x01")


def _mask_balanced_tables(text: str) -> str:
    low = text.lower()
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        k = low.find("<table", i)
        if k < 0:
            out.append(text[i:])
            break
        out.append(text[i:k])
        depth, j, found = 0, k, False
        while j < n:
            if low.startswith("<table", j):
                depth += 1
                j += 6
            elif low.startswith("</table>", j):
                depth -= 1
                j += 8
                if depth == 0:
                    found = True
                    break
            else:
                j += 1
        if found:
            out.append(" ")
            i = j
        else:
            out.append(text[k:k + 6])
            i = k + 6
    return "".join(out)


def _mask_final_form(text: str) -> str:
    text = _mask_balanced_tables(text)
    for rx in (_MARKER_RE, _IMG_MARKER_RE, _VERSE_MARKER_RE, _PAGE_RE):
        text = rx.sub(" ", text)
    return text


# Full target (slot 0 of the link), before the optional `|display`.
_WIKILINK_RE = re.compile(r"\[\[\s*([^\]|\n]+?)\s*(?:\|[^\]]*)?\]\]")


def _bucket(target: str) -> str:
    """Classify one leaking link target into a producer-shaped bucket."""
    t = target.strip()
    low = t.lower()
    if (low.startswith("1911 encyclop") or low.startswith("eb1911")
            or low.startswith("encyclopædia britannica")):
        return "self-ref:1911-EB"
    if ":" in t:                                  # namespace / interwiki prefix
        pre = t.split(":", 1)[0].strip().lower()
        if pre and " " not in pre and len(pre) <= 18:
            return f"ns:{pre}"
    if "bible" in low or "king james" in low:
        return "scripture"
    if "/" in t:
        return "subpage"
    return "plain-article"


def _work(item):
    aid, vol, pg, raw = item
    from britannica.pipeline.stages.elements import (
        ElementContext, process_elements)
    try:
        out = process_elements(raw, ElementContext(volume=vol, page_number=pg))
    except Exception:
        return Counter(), {}
    out = _mask_final_form(out)
    c: Counter = Counter()
    samples: dict[str, list] = defaultdict(list)
    for m in _WIKILINK_RE.finditer(out):
        b = _bucket(m.group(1))
        c[b] += 1
        if len(samples[b]) < 6:
            samples[b].append(m.group(1).strip()[:44])
    return c, samples


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, default=None)
    args = ap.parse_args()
    corpus = [it for it in load_corpus()
              if args.volume is None or it[1] == args.volume]

    t0 = time.perf_counter()
    total: Counter = Counter()
    samp: dict[str, list] = defaultdict(list)
    with Pool(max(1, cpu_count() - 1)) as pool:
        for c, s in pool.imap_unordered(_work, corpus, chunksize=64):
            total.update(c)
            for k, v in s.items():
                for x in v:
                    if len(samp[k]) < 6:
                        samp[k].append(x)
    dt = time.perf_counter() - t0

    print(f"leaking wikilinks: {sum(total.values())}   ({dt:.1f}s, "
          f"{len(corpus)} articles)")
    print("--- by bucket ---")
    for k, n in total.most_common():
        print(f"{n:6d}  {k:22s} e.g. {', '.join(samp[k][:4])}")


if __name__ == "__main__":
    main()
