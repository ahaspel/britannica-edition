"""Measure rendered widths of every «TABLE» marker corpus-wide.

The wide-table treatment (Expand-button figure) used to key on COLUMN COUNT
(cols ≥ 10) — a proxy that fails both ways: ten narrow columns fit fine, and
five columns of long text overflow (CONSTELLATION).  Like the math pipeline
(measure_math_widths → annotate_math_markers → «MATH[fs=N]), the decision is
now a MEASURED FACT:

  * each unique table span renders via the REAL `decode_inline` inside a
    590px `.body-text` host carrying the viewer's own stylesheet
    (590px = the fixed .body-text content width at every desktop viewport);
  * the BROWSER's table layout decides "fits": a table it can compress into
    the column is not wide, one it can't (unbreakable content) is;
  * results cache by span hash (`data/derived/table_widths.json`) — the
    source is static, so subsequent runs measure only new/changed tables.

`annotate_table_markers.py` then stamps `«TABLE[cols:N|wide|…]` from the
cache, and the render wraps exactly the tables that measured wide.

  uv run python tools/diagnostics/measure_table_widths.py            # all
  uv run python tools/diagnostics/measure_table_widths.py --limit 50 # probe
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

ARTS = Path("data/derived/articles")
CACHE = Path("data/derived/table_widths.json")
VIEWER_HTML = Path("tools/viewer/viewer.html")

BODY_WIDTH = 590        # px — .body-text content width (fixed at all viewports)
TOLERANCE = 2           # px — sub-pixel/border slack before "doesn't fit"

TABLE_OPEN, TABLE_CLOSE = "«TABLE[", "«/TABLE»"
_WIDE_PARAM_RE = re.compile(r"(«TABLE\[cols:\d+)\|wide")


def _balanced_spans(body: str):
    """Top-level «TABLE[…]…«/TABLE» spans (balanced, nested-safe)."""
    i = 0
    while True:
        a = body.find(TABLE_OPEN, i)
        if a == -1:
            return
        depth, j = 0, a
        n = len(body)
        end = None
        while j < n:
            if body.startswith(TABLE_OPEN, j):
                depth += 1
                j += len(TABLE_OPEN)
            elif body.startswith(TABLE_CLOSE, j):
                depth -= 1
                j += len(TABLE_CLOSE)
                if depth == 0:
                    end = j
                    break
            else:
                j += 1
        if end is None:
            return
        yield body[a:end]
        i = end


def span_key(span: str) -> str:
    """Cache identity: the span with any `wide` annotation stripped, so
    re-measuring an annotated corpus is idempotent."""
    return hashlib.sha256(
        _WIDE_PARAM_RE.sub(r"\1", span).encode("utf-8")).hexdigest()


def _viewer_css() -> str:
    html = VIEWER_HTML.read_text(encoding="utf-8")
    return "\n".join(re.findall(r"<style>([\s\S]*?)</style>", html))


def collect() -> dict[str, dict]:
    """hash -> {span, cols, samples} over the whole corpus."""
    out: dict[str, dict] = {}
    for f in ARTS.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for span in _balanced_spans(d.get("body") or ""):
            k = span_key(span)
            e = out.setdefault(k, {"span": _WIDE_PARAM_RE.sub(r"\1", span),
                                   "cols": 0, "samples": []})
            m = re.match(r"«TABLE\[cols:(\d+)", span)
            if m:
                e["cols"] = int(m.group(1))
            if len(e["samples"]) < 3:
                e["samples"].append(f.name)
    return out


def render_span(span: str) -> str:
    from britannica.render.article import RenderContext
    from britannica.render.inline import decode_inline
    ctx = RenderContext(volume=0, scan_url="scans.html", unproofed_pages={})
    return decode_inline(span, escape=True, ctx=ctx)


HARNESS = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="card"><div class="body-text" id="host"
  style="width:{width}px; margin:0"></div></div></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--remeasure", action="store_true",
                    help="ignore the cache and measure everything")
    args = ap.parse_args()

    cache: dict[str, dict] = {}
    if CACHE.exists() and not args.remeasure:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))

    tables = collect()
    todo = {k: v for k, v in tables.items() if k not in cache}
    if args.limit:
        todo = dict(list(todo.items())[:args.limit])
    print(f"corpus tables: {len(tables)} unique; cached: "
          f"{sum(1 for k in tables if k in cache)}; to measure: {len(todo)}")
    if not todo:
        _summarize(cache, tables)
        return

    from playwright.sync_api import sync_playwright
    css = _viewer_css()
    measured = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_content(HARNESS.format(css=css, width=BODY_WIDTH))
        items = list(todo.items())
        BATCH = 40
        for i in range(0, len(items), BATCH):
            chunk = items[i:i + BATCH]
            htmls = []
            for _k, e in chunk:
                try:
                    htmls.append(render_span(e["span"]))
                except Exception:
                    htmls.append("")          # render crash → measure as 0
            widths = page.evaluate(
                """(htmls) => htmls.map(h => {
                     const host = document.getElementById('host');
                     host.innerHTML = h;
                     const t = host.querySelector('table');
                     const w = t ? Math.ceil(t.getBoundingClientRect().width)
                                 : 0;
                     const over = Math.ceil(host.scrollWidth);
                     host.innerHTML = '';
                     return Math.max(w, over);
                   })""", htmls)
            for (k, e), w in zip(chunk, widths):
                cache[k] = {"w": w, "wide": w > BODY_WIDTH + TOLERANCE,
                            "cols": e["cols"], "samples": e["samples"]}
            measured += len(chunk)
            if measured % 400 == 0 or measured == len(items):
                print(f"  measured {measured}/{len(items)}", flush=True)
                CACHE.write_text(json.dumps(cache), encoding="utf-8")
        browser.close()
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    _summarize(cache, tables)


def _summarize(cache: dict, tables: dict) -> None:
    in_corpus = [cache[k] for k in tables if k in cache]
    wide = [e for e in in_corpus if e["wide"]]
    was_wide = [e for e in in_corpus if e["cols"] >= 10]
    flips_off = sum(1 for e in in_corpus if e["cols"] >= 10 and not e["wide"])
    flips_on = sum(1 for e in in_corpus if e["cols"] < 10 and e["wide"])
    print(f"measured {len(in_corpus)} corpus tables: {len(wide)} wide "
          f"(cols-proxy said {len(was_wide)}); proxy fixed: "
          f"{flips_off} narrow-but-cols>=10, {flips_on} wide-but-cols<10")


if __name__ == "__main__":
    main()
