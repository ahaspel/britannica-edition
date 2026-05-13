"""Final body-text cleanup applied during article export.

These are pure ``body -> body`` regex normalizations that patch
residual markup the upstream transform stages occasionally leak: stray
table attributes, orphan double-pipes, etc.  They depend only on the
single article's body, so they run as the last transformation in
``export_articles_to_json`` (``tools/pipeline/postprocess.py``
re-exports ``clean_body`` as a standalone safety-net script for
already-written JSON files).

History / direction: this pass used to have ~15 sub-passes.  An audit
(``tools/_scratch/_audit_clean_body.py`` / ``_audit_clean_body_passes.py``)
plus full-corpus runs found 12 fired on zero articles and were
deleted; ``img_widthpx_caption`` was moved to its producer
(``_sanitize_caption`` in ``article_json.py`` now rejects ``x90px``
"captions"); codepoint normalization + blank-line collapse moved into
``_transform_text_v2`` and ``parse_plate``; bare-wiki-table cleanup
(``{|`` / ``|-`` / ``|}``) and the ``_wrap_orphan_tables`` defensive
fallback fired on zero articles in the 2026-05-13 audit and were
deleted (JESUS CHRIST's leaked ``\\x01PAGE:\\x01{|cellpadding=…`` slips
past the line anchor and is handled separately via the
noinclude-layout-table fix in transform).  What's left is being
migrated to its producers the same way — leaked-HTML-attr stripping
into the table/HTML-table/IMG-caption code, orphan double-pipes and
pipe-only lines into the table extractor's empty-cell handling —
after which ``clean_body`` goes away.  Surviving passes: leaked-HTML-
attr stripping (the ``\\s*=`` is load-bearing — without it ``class``
matches "Classics", ``width``/``height``/etc. match any word with
that prefix, eating real content); orphan double-pipe stripping;
pipe-only-line stripping.
"""

from __future__ import annotations

import re


def clean_body(body: str) -> str:
    """Clean residual markup issues from article body text."""
    # Leaked HTML table attributes (colspan, rowspan, style, etc.) —
    # both pipe-delimited (|colspan="3"|) and inside IMG captions.
    # The "\s*=" is load-bearing: without it, the bare keyword "class"
    # matches the word "Classics", "width"/"border"/"height"/"style"/
    # "align" match any word with that prefix, and the [^|\n]*\| then
    # eats real content up to the next pipe (e.g. it ate every
    # "Class N." in the ZOOLOGY taxonomy and mangled EDUCATION's
    # «LN:Classics|…»).  HTML attributes always have "="; words don't.
    body = re.sub(
        r"\|\s*(?:colspan|rowspan|style|align|valign|width|class|bgcolor|"
        r"cellpadding|cellspacing|border|height)\s*=[^|\n]*\|",
        "| ", body, flags=re.IGNORECASE,
    )

    # Stray pipe separators outside tables.  Preserve pipes inside
    # {{TABLE:...}TABLE} and {{VERSE:...}VERSE} blocks.
    parts = re.split(
        r"(\{\{TABLE.*?\}TABLE\}|\{\{VERSE:.*?\}VERSE\})",
        body, flags=re.DOTALL,
    )
    for i in range(0, len(parts), 2):
        # Strip orphaned grid separators (|| ||)
        parts[i] = re.sub(r"\|\|\s*\|\|", "", parts[i])
        # Strip lines that are only pipes and whitespace
        parts[i] = re.sub(r"^\|[\s|]*$", "", parts[i], flags=re.MULTILINE)
    body = "".join(parts)

    return body.strip()
