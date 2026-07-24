"""Re-annotate «TABLE[…]» markers in exported article JSONs with the measured
wide-table fact.

Runs AFTER ``measure_table_widths.py`` has refreshed
``data/derived/table_widths.json``.  Walks every article, finds each table
span, looks up its measured width, and stamps `«TABLE[cols:N|wide|…]` when
the table overflows the 590px body column (the render's Expand treatment keys
on this param — the cols≥10 proxy is gone).  A span with no cache entry, or
one that measured as fitting, is rewritten WITHOUT the param — the script is
also the hint-stripper, so re-annotation is idempotent (the math annotator's
pattern).

Pure text transform on the exported body — no re-render here; the caller
re-renders (post_export renders after annotating; the standalone main()
re-renders only the articles whose markers changed).

  uv run python tools/pipeline/annotate_table_markers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

ARTS = Path("data/derived/articles")
CACHE = Path("data/derived/table_widths.json")

_OPEN_RE = re.compile(r"«TABLE\[cols:(\d+)(\|wide)?")


def annotate_body(body: str, cache: dict) -> str:
    """Stamp/strip the `wide` param on every table span per the cache."""
    sys.path.insert(0, "tools/diagnostics")
    from measure_table_widths import _balanced_spans, span_key
    out = body
    # Process spans back-to-front so replacements don't shift later offsets.
    spans = []
    i = 0
    for span in _balanced_spans(body):
        a = out.index(span, i)
        spans.append((a, span))
        i = a + len(span)
    for a, span in reversed(spans):
        entry = cache.get(span_key(span))
        wide = bool(entry and entry.get("wide"))
        new = _OPEN_RE.sub(
            lambda m: f"«TABLE[cols:{m.group(1)}" + ("|wide" if wide else ""),
            span, count=1)
        if new != span:
            out = out[:a] + new + out[a + len(span):]
    return out


def annotate_payloads(payloads: dict) -> int:
    """The post-export hook: annotate every payload body in place.
    Returns the number of articles whose body changed."""
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    n = 0
    for d in payloads.values():
        body = d.get("body") or ""
        new = annotate_body(body, cache)
        if new != body:
            d["body"] = new
            n += 1
    return n


def main() -> None:
    """Standalone: annotate the on-disk corpus and re-render what changed."""
    from britannica.render.article import render_article
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if not cache:
        print("no table_widths.json cache — run measure_table_widths.py first")
        return
    changed = scanned = 0
    for f in ARTS.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "body" not in d:
            continue
        scanned += 1
        body = d.get("body") or ""
        new = annotate_body(body, cache)
        if new == body:
            continue
        d["body"] = new
        if d.get("rendered_html"):
            d["rendered_html"] = render_article(d,
                                                target="site")
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        changed += 1
        if changed % 200 == 0:
            print(f"  annotated + re-rendered {changed}…", flush=True)
    print(f"scanned {scanned} articles; annotated + re-rendered {changed}")


if __name__ == "__main__":
    main()
