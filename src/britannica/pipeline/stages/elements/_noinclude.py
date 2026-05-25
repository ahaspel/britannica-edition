"""NOINCLUDE element handler.

`<noinclude>…</noinclude>` is a Wikisource page container.  It is HETEROGENEOUS:
usually page-quality / running-header chrome (NOT article content), but
occasionally it carries a real cross-page table marker — EB1911 puts a table's
`{|` opener in one page's header-noinclude and the `|}` closer in a later page's
footer-noinclude so each page displays standalone.

Because disposition needs looking INSIDE the block, it can't be blanket-stripped
at step-1 (that's a content decision) — so the walker carries the block raw and
this producer is its sole consumer ([[consumed-markers-to-producers]]).  It
mirrors the old `detect_boundaries._strip_noinclude_preserve_tables`: keep any
`{|`/`|}` table markers, drop the chrome.

NOTE (B3 follow-up): the kept `{|`/`|}` are emitted as text by this producer,
which runs AFTER the element-walk — so a cross-page table is NOT re-paired into a
single TABLE by this step alone.  Today noinclude is stripped upstream before the
walk, so this producer is a no-op (0 noinclude in segments).  When B3 makes the
super-walker carry noinclude into segments, the cross-page-table PAIRING must be
solved then (hoist the `{|`/`|}` to the body so the table-walker pairs them, or
recognize the table marker at walk time).  The chrome case (the overwhelming
majority) is fully handled here.
"""

from __future__ import annotations

import re

# A `{|` opener up to end-of-line or the next `<` (mirrors detect_boundaries).
_TABLE_OPEN = re.compile(r"(?:^|\n)\s*\{\|[^\n<]*")
# A `|}` on its own (not the `|}}` that closes an empty-arg template).
_TABLE_CLOSE = re.compile(r"(?:^|\n)\s*\|\}(?!\})")


def _process_noinclude(raw: str) -> str:
    """Drop page-chrome, keep cross-page `{|`/`|}` table markers.  Renders to ""
    for the chrome case (the common one)."""
    # Peel the tags first so the line-anchored table regexes match a `{|`
    # that sits immediately after `<noinclude>` as well as one on its own line.
    inner = re.sub(r"^\s*<noinclude>", "", raw, flags=re.IGNORECASE)
    inner = re.sub(r"</noinclude>\s*$", "", inner, flags=re.IGNORECASE)
    kept = [m.group(0).strip() for m in _TABLE_OPEN.finditer(inner)]
    if _TABLE_CLOSE.search(inner):
        kept.append("|}")
    return ("\n" + "\n".join(kept) + "\n") if kept else ""
