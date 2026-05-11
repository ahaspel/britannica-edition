"""Final body-text cleanup applied during article export.

These are pure ``body -> body`` regex normalizations that patch
residual markup the upstream transform stages occasionally leak:
codepoint normalization, stray table attributes, orphaned pipe-rows,
blank-line collapse, etc.  They depend only on the single article's
body, so they run as the last transformation in ``export_articles_to_json``
(``tools/pipeline/postprocess.py`` re-exports ``clean_body`` as a
standalone safety-net script for already-written JSON files).
"""

from __future__ import annotations

import re

from britannica.cleaners.unicode import replace_print_artifacts


def clean_body(body: str) -> str:
    """Clean residual markup issues from article body text."""
    # Normalize transcription-artifact codepoints (fullwidth = + - < >,
    # ligature glyphs ℔ ℥ ℈, dingbat ✕) to modern ASCII / Latin-1 forms.
    body = replace_print_artifacts(body)
    # Leaked HTML table attributes (colspan, rowspan, nowrap, etc.)
    # Both pipe-delimited (|colspan="3"|) and inline (nowrap|text)
    body = re.sub(
        r"\|\s*(?:colspan|rowspan|style|align|valign|width|class|bgcolor|"
        r"cellpadding|cellspacing|border|height)[^|\n]*\|",
        "| ", body, flags=re.IGNORECASE,
    )
    # Inline nowrap (nowrap|text or nowrap\n)
    body = re.sub(r"nowrap\|", "", body)
    body = re.sub(r"nowrap\n", "\n", body)

    # Garbled table attributes embedded in text
    body = re.sub(r"(?:wisth|wdith|width)\s*=\s*\d+\|", "", body)

    # Strip width directives masquerading as image captions (x125px, x310px)
    body = re.sub(r"(\{\{IMG:[^|}]+)\|x\d+px\}\}", r"\1}}", body)

    # Leaked image layout directives: img float|..., figure|image=..., FI|file=...
    body = re.sub(
        r"(?:img float|figure|FI)\s*\|[^\n]*(?:\|file\s*=[^\n]+)?",
        "", body, flags=re.IGNORECASE,
    )
    # Leaked image alignment prefixes (right|, left|, center|) at line starts
    body = re.sub(r"^(?:right|left|center)\|", "", body, flags=re.MULTILINE | re.IGNORECASE)

    # Table attributes leaked inside {{TABLE:...}TABLE} markers
    body = re.sub(
        r"\{\{TABLE:(?:cellspacing|cellpadding|rules|border)[^}]*\}TABLE\}",
        "", body,
    )
    # Clean {ts|... and similar leaked table style prefixes inside TABLE
    body = re.sub(r"\{\{TABLE:\{[^}]*\}\}TABLE\}", "", body)
    # Strip leading attribute lines (title="...", class="...", etc.) from TABLE content
    body = re.sub(
        r"(\{\{TABLE:)\s*(?:title|class|style|align|rules|cellspacing|cellpadding|border|width)="
        r"[^\n]*\n",
        r"\1", body, flags=re.IGNORECASE,
    )

    # Bare wiki table markup
    body = re.sub(r"\{\|[^\n]*\n?", "", body)
    body = re.sub(r"^\|-[a-z].*$", "", body, flags=re.MULTILINE | re.IGNORECASE)
    body = re.sub(r"^\|\}\s*$", "", body, flags=re.MULTILINE)

    # Stray pipe separators outside tables
    # Preserve pipes inside {{TABLE:...}TABLE} and {{VERSE:...}VERSE} blocks
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

    # Bare HTML tags (not inside markers)
    body = re.sub(
        r"</?(?:s|small|big|center|div|span|font)\b[^>]*>",
        "", body, flags=re.IGNORECASE,
    )

    # Stray [[ ]] wikilink brackets
    body = re.sub(r"\[\[(?:Author|Category|File|Image):[^\]]*\]\]", "", body)

    # Stray close braces not part of a marker
    parts = re.split(
        r"(\{\{(?:TABLE|IMG|VERSE|FN).*?\}(?:TABLE|VERSE)\}|\}\})",
        body, flags=re.DOTALL,
    )
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("}}", "")
    body = "".join(parts)

    # (Table-pipe normalization and blank-row collapse for {{TABLE:}
    # blocks used to live here; the table renderer — _emit_table_marker
    # in elements/_tables.py — now emits canonical form directly, so
    # these passes were redundant.  Header tables {{TABLEH:} were never
    # covered here anyway (the old \{\{TABLE:(.*?)\}TABLE\} regex didn't
    # match {{TABLEH:}); normalizing those too is a burndown item.)

    # Wrap orphaned pipe-delimited data runs in TABLE markers.
    # These are tabular lines (3+ pipes) not already inside a TABLE block.
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
