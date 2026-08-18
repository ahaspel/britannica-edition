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
re-renders.  INVARIANT: the cache keys on the span's BYTES, so annotation
must see the FINAL body form — post_export applies ``annotate_body`` as the
``decorate`` hook inside resolve_and_render (after the «LN» targets bake,
before the render); annotating a pre-resolution body silently cache-misses
every table that contains a link.  The standalone main() operates on the
on-disk corpus, which is post-resolution by construction.

  uv run python tools/pipeline/annotate_table_markers.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

from britannica.export.corpus import load_corpus  # noqa: E402
from britannica.markers import iter_table_spans, set_table_wide  # noqa: E402
from britannica.table_widths import (  # noqa: E402
    CACHE_PATH as CACHE, is_wide, span_key)

ARTS = Path("data/derived/articles")


def annotate_body(body: str, cache: dict, plate: bool = False,
                  stats: "dict | None" = None) -> str:
    """Stamp/strip the `wide` param on every table span per the cache.

    ``plate=True`` forces the STRIP side for every span: a plate page's
    tables are strictly a LAYOUT device (they grid the figure legends), the
    plate already owns the full margins, and the Expand treatment measured
    against the 590px body column means nothing there — a plate table is
    never wide, whatever the cache measured.
    """
    out = body
    # Back-to-front, so an earlier replacement can't shift a later offset.
    for a, span in reversed(list(iter_table_spans(body))):
        if not plate and span_key(span) not in cache:
            # UNMEASURED — the cache keys on the span's BYTES, so a table whose
            # interior text moved (a re-hyphenation, an indent marker landing
            # inside it) is a cache MISS, not a narrow table.  Stripping here is
            # how the 2026-08-16 rebuild silently lost 194 Expand hints: the
            # span keeps whatever it already states, and the caller is told, so
            # a missing measurement is a number someone reads rather than a
            # button that quietly disappears ([[feedback_honesty_surface_failures]]).
            if stats is not None:
                stats["unmeasured"] = stats.get("unmeasured", 0) + 1
            continue
        entry = None if plate else cache.get(span_key(span))
        new = set_table_wide(span, is_wide(entry))
        if new != span:
            out = out[:a] + new + out[a + len(span):]
    return out


def main() -> None:
    """Standalone: annotate the on-disk corpus and re-render what changed."""
    from britannica.render.article import render_article
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if not cache:
        print("no table_widths.json cache — run measure_table_widths.py first")
        return
    changed = scanned = 0
    stats: dict = {}
    # TOTAL read — an article this cannot parse RAISES rather than going
    # un-annotated, which would look exactly like a table that measured narrow.
    for f, d in sorted(load_corpus(ARTS)[0].items()):
        scanned += 1
        body = d.get("body") or ""
        new = annotate_body(body, cache, stats=stats,
                            plate=d.get("article_type") == "plate")
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
    if stats.get("unmeasured"):
        print(f"  {stats['unmeasured']} table span(s) had NO measurement and kept "
              f"their existing hint — run measure_table_widths.py")


if __name__ == "__main__":
    main()
