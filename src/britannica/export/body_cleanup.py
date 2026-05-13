"""Final body-text cleanup applied during article export.

These are pure ``body -> body`` regex normalizations that patch
residual markup the upstream transform stages occasionally leak:
codepoint normalization, stray table attributes, orphaned pipe-rows,
blank-line collapse, etc.  They depend only on the single article's
body, so they run as the last transformation in ``export_articles_to_json``
(``tools/pipeline/postprocess.py`` re-exports ``clean_body`` as a
standalone safety-net script for already-written JSON files).

History / direction: this pass used to have ~15 sub-passes.  An audit
(``tools/_scratch/_audit_clean_body.py``) plus a ``--full`` corpus run
found 8 fired on zero articles (the transform/elements refactor through
Step 2 eliminated everything they targeted) and were deleted; one more
(``img_widthpx_caption``) was moved to its producer
(``_sanitize_caption`` in ``article_json.py`` now rejects ``x90px``
"captions").  What's left is being migrated to its producers the same
way — leaked-HTML-attr stripping into the table/HTML-table/IMG-caption
code, bare-wiki-table removal into transform's noinclude handling,
orphan-pipe scrubbing into the table/plate extractors — after which
``replace_print_artifacts`` and the blank-line collapse move into
transform and ``clean_body`` goes away.  Surviving passes: codepoint
normalization; leaked-HTML-attr stripping (the ``\\s*=`` is load-bearing
— without it ``class`` matches "Classics", ``width``/``height``/etc.
match any word with that prefix, eating real content); bare-wiki-table
removal (can still eat prose glued onto a malformed ``{|`` opener — the
JESUS CHRIST noinclude-layout-table case); orphan pipe-row
scrubbing/wrapping; blank-line collapse.
"""

from __future__ import annotations

import re

from britannica.cleaners.unicode import replace_print_artifacts


def clean_body(body: str) -> str:
    """Clean residual markup issues from article body text."""
    # Normalize transcription-artifact codepoints (fullwidth = + - < >,
    # ligature glyphs ℔ ℥ ℈, dingbat ✕) to modern ASCII / Latin-1 forms.
    body = replace_print_artifacts(body)

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

    # Bare wiki table markup that escaped extraction.  Line-anchor the
    # `{|` opener: in wikitext `{|` only opens a table at column 0, so a
    # real leaked opener is at a line start — a mid-line `{|` is always
    # LaTeX inside a «MATH:…« block (`\frac{|\partial f}`) or similar,
    # and the old un-anchored `\{\|[^\n]*\n?` ate from there to end of
    # line, swallowing the rest of the «MATH:» block (INFINITESIMAL
    # CALCULUS §40).
    body = re.sub(r"(?m)^\s*\{\|[^\n]*\n?", "", body)
    body = re.sub(r"^\|-[a-z].*$", "", body, flags=re.MULTILINE | re.IGNORECASE)
    body = re.sub(r"^\|\}\s*$", "", body, flags=re.MULTILINE)

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

    # Wrap orphaned pipe-delimited data runs in TABLE markers.
    parts = re.split(
        r"(\{\{TABLE.*?\}TABLE\}|\{\{VERSE:.*?\}VERSE\})",
        body, flags=re.DOTALL,
    )
    for i in range(0, len(parts), 2):
        parts[i] = _wrap_orphan_tables(parts[i])
    body = "".join(parts)

    # Collapse excessive blank lines
    body = re.sub(r"\n{3,}", "\n\n", body)

    return body.strip()


def _wrap_orphan_tables(text: str) -> str:
    """Find runs of pipe-separated lines and wrap in {{TABLE:...}TABLE}."""
    lines = text.split("\n")
    result = []
    table_lines = []

    def flush_table():
        if len(table_lines) >= 2:
            cleaned = []
            for line in table_lines:
                # Strip leading |
                line = line.strip()
                if line.startswith("|"):
                    line = line[1:].strip()
                cleaned.append(line)
            result.append("{{TABLE:" + "\n".join(cleaned) + "}TABLE}")
        else:
            result.extend(table_lines)

    pending_blanks = []
    for line in lines:
        stripped = line.strip()
        # A table line: starts with | and has pipe separators
        is_table_line = (
            stripped.startswith("|")
            and stripped.count("|") >= 1
            and not stripped.startswith("|}")
            and not stripped.startswith("|+")
            and len(stripped) > 3  # avoid bare | lines
        )
        if is_table_line:
            # Absorb any pending blank lines into the table run
            if table_lines and pending_blanks:
                table_lines.extend(pending_blanks)
            pending_blanks = []
            table_lines.append(line)
        elif stripped == "" and table_lines:
            # Blank line while in a table run — hold it pending
            pending_blanks.append(line)
        else:
            if table_lines:
                flush_table()
                table_lines = []
            # Pending blanks weren't followed by a table line — emit them
            result.extend(pending_blanks)
            pending_blanks = []
            result.append(line)

    if table_lines:
        flush_table()
    result.extend(pending_blanks)

    return "\n".join(result)
