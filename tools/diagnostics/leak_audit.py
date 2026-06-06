"""leak_audit.py — find ALL residual markup in the FINAL transform output.

STANDALONE BY DESIGN: the definition of "a leak" lives here (a self-contained
scanner), not in any pipeline cleaner/stripper — so deleting the dead producers
and the soon-to-be-dead body-text passes can never blind this audit.  It reads the
REAL `_transform_text_v2` output with NO toggles (unlike `figure_leak_attribution`,
which flips the soon-dead `_EMIT_STYLE_WRAPPERS`).

A leak = any SOURCE markup or INTERNAL sentinel that survived into final output:
raw `{{template}}`, `[[wikilink]]`, `<htmltag>`, `&entity;`, raw `'''`/`''`, and the
`\x01`/`\x03`/`\x05`/`\x06` sentinels.  Producer markers (`{{IMG:…}}`, `{{TABLE…}}`,
`{{verse:…}}`, and every `«…»`) are the FINAL form, not leaks.

  uv run python tools/diagnostics/leak_audit.py                # full corpus
  uv run python tools/diagnostics/leak_audit.py --volume 5     # one volume
  uv run python tools/diagnostics/leak_audit.py --top 40 --samples
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

# Producer markers that legitimately use `{{…}}` — the FINAL form, not leaks.
_PRODUCER_PREFIX = ("img:", "table", "verse:")
_TEMPLATE_RE = re.compile(r"\{\{\s*([^|}\n]{1,40})")
_WIKILINK_RE = re.compile(r"\[\[\s*([^\]|\n]{1,30})")
_HTMLTAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b")
_ENTITY_RE = re.compile(r"&([a-zA-Z]{2,}|#\d+);")
_SENTINELS = (("\x01", "ctrl"), ("\x03", "placeholder"),
              ("\x05", "FMT"), ("\x06", "LNK"))

# Final-form constructs to MASK before scanning — the viewer's rendered output, NOT
# leaks: rendered tables (their <td>/<tr> are HTML by design), «…» markers, image and
# verse markers, and the \x01PAGE sentinels the export consumes for page numbers.
_TABLE_BLOCK_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)
_MARKER_RE = re.compile(r"«[^»]*»")
_IMG_MARKER_RE = re.compile(r"\{\{IMG:[^{}]*\}\}", re.IGNORECASE)
_VERSE_MARKER_RE = re.compile(r"\{\{verse:.*?\}\}", re.IGNORECASE | re.DOTALL)
_PAGE_RE = re.compile(r"\x01PAGE:\d+\x01")


def _mask_final_form(text: str) -> str:
    prev = None
    while prev != text:                 # iterate for nested tables
        prev = text
        text = _TABLE_BLOCK_RE.sub(" ", text)
    for rx in (_MARKER_RE, _IMG_MARKER_RE, _VERSE_MARKER_RE, _PAGE_RE):
        text = rx.sub(" ", text)
    return text


def find_leaks(text: str) -> Counter:
    """`category:detail` → residual-markup leaks in the FINAL output, AFTER masking the
    final-form constructs (rendered tables, «…» markers, image/verse markers, page
    sentinels) — so a rendered table's <td> isn't miscounted as a leak."""
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
    except Exception as e:  # a crash is itself a leak we must see
        return aid, Counter({f"crash:{type(e).__name__}": 1})
    return aid, find_leaks(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, default=None,
                    help="audit one volume; omit for full corpus")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--samples", action="store_true",
                    help="show example article ids per leak")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    corpus = [it for it in load_corpus()
              if args.volume is None or it[1] == args.volume]
    if args.limit:
        corpus = corpus[:args.limit]

    t0 = time.perf_counter()
    total: Counter = Counter()
    by_cat: Counter = Counter()
    samples: dict[str, list] = defaultdict(list)
    n_art = n_leaky = 0
    with Pool(max(1, cpu_count() - 1)) as pool:
        for aid, leaks in pool.imap_unordered(_work, corpus, chunksize=64):
            n_art += 1
            if leaks:
                n_leaky += 1
                total += leaks
                for k, v in leaks.items():
                    by_cat[k.split(":", 1)[0]] += v
                    if args.samples and len(samples[k]) < 5:
                        samples[k].append(aid)
    dt = time.perf_counter() - t0

    scope = f"vol {args.volume}" if args.volume is not None else "full corpus"
    print(f"scope: {scope}   {dt:.1f}s")
    print(f"articles: {n_art}   leaky: {n_leaky} "
          f"({100 * n_leaky // max(1, n_art)}%)   leak hits: {sum(total.values())}")
    print("--- by category ---")
    for cat, n in by_cat.most_common():
        print(f"{n:8d}  {cat}")
    print(f"--- top {args.top} leaks ---")
    for k, v in total.most_common(args.top):
        ex = ("   e.g. " + ", ".join(map(str, samples[k]))) if args.samples else ""
        print(f"{v:8d}  {k}{ex}")


if __name__ == "__main__":
    main()
