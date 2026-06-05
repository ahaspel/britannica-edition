"""Style-recognizer campaign meter: with the four body-text style emitters
disabled (`body_text._EMIT_STYLE_WRAPPERS = False`), capture EVERY `{{Ts}}`
that still reaches `_strip_templates`, with ~110 chars of enclosing context, so
we can see WHICH path leaks it.  Runs on the saved leaker ids (fast).

  uv run python tools/diagnostics/emitter_meter.py        # all samples, grouped
"""
from __future__ import annotations
import io, json, re, sys
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))
from _corpus_cache import load_corpus
LEAKERS = ROOT / "tools" / "_scratch" / "ts_leakers.json"

_TS = re.compile(r"\{\{\s*ts\b", re.IGNORECASE)
_HITS: list[str] = []


def _bin(pre: str) -> str:
    if re.search(r"<t[dh]\b[^>]*$", pre): return "<td/<th cell"
    if re.search(r"<tr\b[^>]*$", pre): return "<tr row"
    if re.search(r"\{\|[^\n]*$", pre): return "{| wiki-opener"
    if re.search(r"(?:^|\n)[!|][^\n]*$", pre): return "wiki !/| cell"
    if re.search(r"colspan|rowspan|scope=|valign=", pre): return "bare cell-attr"
    if re.search(r"\{\{\s*(?:left|right|center|block\w*|float\w*)\b[^{}]*$", pre,
                 re.IGNORECASE): return "{{left/right/center tmpl"
    if re.search(r"<p\b[^>]*$", pre): return "<p paragraph"
    if re.search(r"<div\b[^>]*$", pre): return "<div"
    if re.search(r"<span\b[^>]*$", pre): return "<span"
    return "OTHER (standalone)"


def _init():
    from britannica.pipeline.stages.transform_articles import body_text as BT
    from britannica.pipeline.stages.transform_articles import _transform_text_v2 as _tx2
    BT._EMIT_STYLE_WRAPPERS = False
    _strip_re = BT._STRIP_TEMPLATES_RE
    _orig = BT._strip_templates

    def _spy(text: str) -> str:
        prev, t = None, text
        while prev != t:
            prev = t
            for m in re.finditer(_strip_re, t):
                tok = m.group(0)
                nm = re.match(r"\{\{\s*([^|}\n]*)", tok)
                if nm and nm.group(1).strip().lower() == "ts":
                    pre = t[max(0, m.start() - 110):m.start()]
                    _HITS.append((_bin(pre), pre, tok))
            t = re.sub(_strip_re, "", t)
        return _orig(text)
    BT._strip_templates = _spy
    globals()["_tx"] = _tx2


def _work(item):
    aid, vol, pg0, raw = item
    _HITS.clear()
    try:
        _tx(raw, vol, pg0)
    except Exception:
        pass
    return aid, list(_HITS)


def main():
    ids = set(json.loads(LEAKERS.read_text()))
    corpus = [r for r in load_corpus() if r[0] in ids]
    with Pool(max(1, cpu_count() - 1), initializer=_init) as pool:
        results = pool.map(_work, corpus)
    by_bin: dict[str, list] = defaultdict(list)
    for aid, hits in results:
        for b, pre, tok in hits:
            by_bin[b].append((aid, pre, tok))
    total = sum(len(v) for v in by_bin.values())
    print(f"=== EMITTER-DISABLED Ts LEAKS: {total} in {len(corpus)} articles ===\n")
    for b in sorted(by_bin, key=lambda k: -len(by_bin[k])):
        rows = by_bin[b]
        print(f"\n#### {b}  ({len(rows)})")
        for aid, pre, tok in rows:
            ctx = (pre[-78:] + "⟦" + tok + "⟧").replace("\x01", "§").replace("\n", "\\n")
            print(f"   [{aid}] …{ctx}")


if __name__ == "__main__":
    main()
