"""leak_audit.py — find BROKEN markup in the FINAL transform output.

STANDALONE BY DESIGN: the definition of "a leak" lives here (a self-contained
scanner), not in any pipeline cleaner/stripper — so deleting dead producers can
never blind this audit.  It reads the REAL `_transform_text_v2` output, no toggles.

A "leak" is source markup or an internal sentinel that SURVIVED into final output.
But survival means two very different things, and the headline must not conflate
them:

  BROKEN     — content that lost its meaning / went unprocessed: raw non-producer
               `{{template}}`, raw `[[wikilink]]`, the internal `\\x01`/`\\x03`/…
               sentinels, raw `'''`/`''` wikiformat, a producer crash, and semantic
               HTML that should be a marker (`<ref>`/`<math>`/`<poem>`/…).  THIS is
               the number to drive toward zero.
  RENDERABLE — valid HTML the viewer decodes correctly: `&entity;` and inline
               formatting tags (`<sub>`/`<sup>`/`<br>`/`<i>`/…).  These survive but
               render fine; carrying them as markers instead is an architectural
               to-do, NOT breakage.  Reported separately so they can't drown the
               broken signal (`&nbsp;`+`<sub>`+`<sup>` alone were 195k of the old,
               useless, 230k headline).

Masking is STRUCTURAL: rendered `<table>…</table>` are masked by a BALANCED,
depth-aware scan — not a non-greedy `.*?` regex whose match boundary shifts on
unrelated edits and counts byte-identical tables as new leaks (the bug that flagged
a whole table as +441 when nothing in it changed).  Then «…» markers, image/verse
markers, and page sentinels are masked.

  uv run python tools/diagnostics/leak_audit.py                # full corpus
  uv run python tools/diagnostics/leak_audit.py --volume 5     # one volume
  uv run python tools/diagnostics/leak_audit.py --top 40 --samples
  uv run python tools/diagnostics/leak_audit.py --renderable   # also list render bucket
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
from _corpus_cache import load_corpus  # noqa: E402

_PRODUCER_PREFIX = ("img:", "table", "verse:")
_TEMPLATE_RE = re.compile(r"\{\{\s*([^|}\n]{1,40})")
_WIKILINK_RE = re.compile(r"\[\[\s*([^\]|\n]{1,30})")
_HTMLTAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b")
_ENTITY_RE = re.compile(r"&([a-zA-Z]{2,}|#\d+);")
_SENTINELS = (("\x01", "ctrl"), ("\x03", "placeholder"),
              ("\x05", "FMT"), ("\x06", "LNK"), ("\x07", "SH"))

_MARKER_RE = re.compile(r"«[^»]*»")
_IMG_MARKER_RE = re.compile(r"\{\{IMG:[^{}]*\}\}", re.IGNORECASE)
_VERSE_MARKER_RE = re.compile(r"\{\{verse:.*?\}\}", re.IGNORECASE | re.DOTALL)
_PAGE_RE = re.compile(r"\x01PAGE:\d+\x01")

# HTML tags the viewer decodes as-is — surviving them is cosmetic, not breakage.
# Everything NOT in this set (e.g. `ref`, `math`, `poem`, `score`, `hiero`) is a
# semantic construct that should have become a marker → BROKEN.
_RENDER_TAGS = frozenset((
    "sub sup br i b em strong small big u s span div p tt code cite var samp "
    "kbd abbr blockquote ol ul li dl dt dd hr"
).split())


def _is_renderable(key: str) -> bool:
    cat, _, detail = key.partition(":")
    if cat == "entity":
        return True
    if cat == "htmltag":
        return detail in _RENDER_TAGS
    return False  # template / wikilink / sentinel / wikifmt / crash → broken


def _mask_balanced_tables(text: str) -> str:
    """Mask every rendered `<table>…</table>` by a BALANCED depth scan (handles
    nesting).  An unbalanced `<table` with no matching close is LEFT as a leak —
    not masked to end-of-text — so it surfaces as the real problem it is."""
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
            out.append(" ")          # whole balanced table is final-form → masked
            i = j
        else:
            out.append(text[k:k + 6])  # unbalanced: leave `<table` as a leak
            i = k + 6
    return "".join(out)


def _mask_final_form(text: str) -> str:
    text = _mask_balanced_tables(text)
    for rx in (_MARKER_RE, _IMG_MARKER_RE, _VERSE_MARKER_RE, _PAGE_RE):
        text = rx.sub(" ", text)
    return text


def find_leaks(text: str) -> Counter:
    """`category:detail` → residual markup, AFTER masking the final-form constructs."""
    text = _mask_final_form(text)
    c: Counter = Counter()
    for m in _TEMPLATE_RE.finditer(text):
        name = m.group(1).strip().lower()
        if not name.startswith(_PRODUCER_PREFIX):
            c[f"template:{name[:22]}"] += 1
    for m in _WIKILINK_RE.finditer(text):
        c[f"wikilink:{m.group(1).strip().lower()[:18]}"] += 1
    for m in _HTMLTAG_RE.finditer(text):
        c[f"htmltag:{m.group(1).lower()}"] += 1
    for m in _ENTITY_RE.finditer(text):
        c[f"entity:{m.group(1).lower()}"] += 1
    if "'''" in text:
        c["wikifmt:'''"] += text.count("'''")
    for ch, nm in _SENTINELS:
        n = text.count(ch)
        if n:
            c[f"sentinel:{nm}"] += n
    return c


def _work(item):
    aid, vol, pg, raw = item
    from britannica.pipeline.stages.transform_articles import _transform_text_v2
    try:
        out = _transform_text_v2(raw, vol, pg)
    except Exception as e:  # a crash is the most broken leak of all
        return aid, Counter({f"crash:{type(e).__name__}": 1})
    return aid, find_leaks(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, default=None,
                    help="audit one volume; omit for full corpus")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--samples", action="store_true",
                    help="show example article ids per broken leak")
    ap.add_argument("--renderable", action="store_true",
                    help="also list the renderable (viewer-decoded) bucket")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    corpus = [it for it in load_corpus()
              if args.volume is None or it[1] == args.volume]
    if args.limit:
        corpus = corpus[:args.limit]

    t0 = time.perf_counter()
    total: Counter = Counter()
    samples: dict[str, list] = defaultdict(list)
    n_art = n_broken = 0
    with Pool(max(1, cpu_count() - 1)) as pool:
        for aid, leaks in pool.imap_unordered(_work, corpus, chunksize=64):
            n_art += 1
            if any(not _is_renderable(k) for k in leaks):
                n_broken += 1
            for k, v in leaks.items():
                total[k] += v
                if args.samples and not _is_renderable(k) and len(samples[k]) < 5:
                    samples[k].append(aid)
    dt = time.perf_counter() - t0

    broken = sum(v for k, v in total.items() if not _is_renderable(k))
    render = sum(v for k, v in total.items() if _is_renderable(k))
    scope = f"vol {args.volume}" if args.volume is not None else "full corpus"
    print(f"scope: {scope}   {dt:.1f}s   articles: {n_art}")
    print(f"BROKEN: {broken}   (in {n_broken} articles, "
          f"{100 * n_broken // max(1, n_art)}%)"
          f"   |   renderable (viewer-decoded): {render}")
    print("--- broken by category ---")
    cats: Counter = Counter()
    for k, v in total.items():
        if not _is_renderable(k):
            cats[k.split(":", 1)[0]] += v
    for cat, n in cats.most_common():
        print(f"{n:8d}  {cat}")
    print(f"--- top {args.top} broken leaks ---")
    shown = 0
    for k, v in total.most_common():
        if _is_renderable(k):
            continue
        ex = ("   e.g. " + ", ".join(map(str, samples[k]))) if args.samples else ""
        print(f"{v:8d}  {k}{ex}")
        shown += 1
        if shown >= args.top:
            break
    if args.renderable:
        print("--- renderable bucket (cosmetic / architectural, not breakage) ---")
        rcats: Counter = Counter()
        for k, v in total.items():
            if _is_renderable(k):
                rcats[k] += v
        for k, n in rcats.most_common(args.top):
            print(f"{n:8d}  {k}")


if __name__ == "__main__":
    main()
