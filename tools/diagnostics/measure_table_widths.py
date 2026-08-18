"""Measure rendered widths of every «TABLE» marker corpus-wide.

The wide-table treatment (Expand-button figure) used to key on COLUMN COUNT
(cols ≥ 10) — a proxy that fails both ways: ten narrow columns fit fine, and
five columns of long text overflow (CONSTELLATION).  Like the math pipeline
(measure_math_widths → annotate_math_markers → «MATH[fs=N]), the decision is
now a MEASURED FACT:

  * each unique table span renders via the REAL `decode_inline` inside a
    590px `.body-text` host carrying the viewer's own stylesheet
    (590px = the .body-text content box at every desktop viewport);
  * the BROWSER's table layout decides the WIDTH: what a table cannot compress
    below is a fact about it, and that fact — `w` — is all this stores.  Whether
    the width costs the reader anything is policy, and it lives with the cache's
    owner (`table_widths.is_wide`, limit 751px = the card's content edge, past
    which the page really does clip).  Measuring against the 590px box instead
    put an Expand button on 471 of 920 spans that lost the reader nothing;
  * results cache by span hash (`data/derived/table_widths.json`) — the
    source is static, so subsequent runs measure only new/changed tables.

`annotate_table_markers.py` then stamps `«TABLE[cols:N|wide|…]` from the
cache, and the render wraps exactly the tables that measured wide.

  uv run python tools/diagnostics/measure_table_widths.py            # all
  uv run python tools/diagnostics/measure_table_widths.py --limit 50 # probe
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

from britannica.markers import (  # noqa: E402
    iter_table_spans, strip_table_wide, table_cols)
from britannica.export.corpus import load_corpus  # noqa: E402
from britannica.table_widths import (  # noqa: E402
    CACHE_PATH as CACHE, WIDE_LIMIT, is_wide, span_key)

ARTS = Path("data/derived/articles")
VIEWER_HTML = Path("tools/viewer/viewer.html")

BODY_WIDTH = 590        # px — the .body-text content box the span renders into.
                        # NOT the wide threshold: what the page can actually SHOW
                        # is `table_widths.WIDE_LIMIT` (751px, the card edge).


def _viewer_css() -> str:
    html = VIEWER_HTML.read_text(encoding="utf-8")
    return "\n".join(re.findall(r"<style>([\s\S]*?)</style>", html))


def collect() -> dict[str, dict]:
    """hash -> {span, cols, samples} over the whole corpus.

    Plates are skipped whole: their tables are a LAYOUT device (legend
    grids on a full-margin page), never annotated wide, so measuring them
    is browser time spent on spans no consumer reads."""
    out: dict[str, dict] = {}
    # TOTAL read: a file this cannot parse RAISES rather than vanishing from the
    # measurement — an unmeasured span is a cache miss downstream, and a cache
    # miss is what silently stripped 194 Expand hints on 2026-08-16.
    for f, d in sorted(load_corpus(ARTS)[0].items()):
        if d.get("article_type") == "plate":
            continue
        for _a, span in iter_table_spans(d.get("body") or ""):
            k = span_key(span)
            e = out.setdefault(k, {"span": strip_table_wide(span),
                                   "cols": 0, "samples": []})
            e["cols"] = table_cols(span) or e["cols"]
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
                # Store the MEASUREMENT only.  Whether it counts as wide is
                # policy (`table_widths.is_wide`), and policy must not be
                # frozen into a cache that costs a browser run to rebuild.
                cache[k] = {"w": w,
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
    wide = [e for e in in_corpus if is_wide(e)]
    was_wide = [e for e in in_corpus if e["cols"] >= 10]
    flips_off = sum(1 for e in in_corpus if e["cols"] >= 10 and not is_wide(e))
    flips_on = sum(1 for e in in_corpus if e["cols"] < 10 and is_wide(e))
    print(f"measured {len(in_corpus)} corpus tables: {len(wide)} wide "
          f"at WIDE_LIMIT={WIDE_LIMIT}px (cols-proxy said {len(was_wide)}); "
          f"proxy fixed: {flips_off} narrow-but-cols>=10, "
          f"{flips_on} wide-but-cols<10")


if __name__ == "__main__":
    main()
