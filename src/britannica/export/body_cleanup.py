"""Final body-text cleanup applied during article export.

These are pure ``body -> body`` regex normalizations that patch
residual markup the upstream transform stages occasionally leak:
codepoint normalization, stray table attributes, orphaned pipe-rows,
blank-line collapse, etc.  They depend only on the single article's
body, so they run as the last transformation in ``export_articles_to_json``
(``tools/pipeline/postprocess.py`` re-exports ``clean_body`` as a
standalone safety-net script for already-written JSON files).

History / direction: this pass used to have ~15 sub-passes.  An audit
(``tools/_scratch/_audit_clean_body.py``) over the corpus found 9 of
them fired on *zero* articles — the transform/elements refactor through
Step 2 eliminated everything they targeted — so they were deleted.
What remains is being migrated to its producers (HTML-attr stripping
into the table/HTML-table/IMG-caption code; ``replace_print_artifacts``
and the blank-line collapse into transform), after which ``clean_body``
goes away entirely.  Until then, the surviving passes are: codepoint
normalization, leaked-HTML-attr stripping (still has a known
false-match bug on words like "Classics" — burndown), bare-wiki-table
removal (can eat prose glued onto a malformed ``{|`` opener — burndown),
orphan pipe-row scrubbing/wrapping, and blank-line collapse.
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

    # MediaWiki image size param (`x90px`) that the image extractor
    # stored as a "caption" and the export-stage _patch_img then wrote
    # into the body as `{{IMG:fn|x90px}}`.  Only ever fires on the
    # post-_patch_img body, never on raw article.body — the producer
    # fix lives in _sanitize_caption / extract_images, and this pass
    # goes once that's done.
    body = re.sub(r"(\{\{IMG:[^|}]+)\|x\d+px\}\}", r"\1}}", body)

    # Bare wiki table markup that escaped extraction.
    body = re.sub(r"\{\|[^\n]*\n?", "", body)
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
