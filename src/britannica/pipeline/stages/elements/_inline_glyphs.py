"""Detect bare `[[File:X|size]]` refs in prose context and emit them as
the unified `{{IMG:X|align=inline|…}}` marker — inline is just another
image alignment (folded in from the former `{{IMG-INLINE:}}` marker).

This is the POSITIONAL detector: deciding "inline" requires the
surrounding prose context, which the isolated element producer never
sees, so it can't live in the producer.  Per the stupid-walker rule,
location-dependent logic belongs in scoped preprocessing — and running
pre-extraction on the full raw text is also what lets it catch inline
glyphs ANYWHERE (body, footnotes, poems), not just top-level.  The
marker itself is built with the same `build_img_marker` every image
producer uses, so encoding/rendering are unified.

Routing decision is by structural signals, not size heuristics:

  * **Inside `{|…|}` or `<table>…</table>`** — skip.  Caught by the
    wikitable extractor downstream; carries adjacent-cell captions or
    chemistry-bracket glyph processing.  (CHEM_BRACKET and
    TABLE_FIGURE buckets in the audit.)
  * **File link with an inline caption** (plain-text param) — skip.
    Block figure with its own caption.  (CAPTIONED.)
  * **File link with a layout keyword** (`right`/`left`/`thumb`/…) —
    skip.  Block figure.  (BLOCK_LAYOUT.)
  * **File link alone on its source line** — skip.  Captionless block
    figure stranded between paragraphs.  (STRANDED.)
  * **File link mid-prose-line** — emit `{{IMG:fn|align=inline|…}}`.
    (INLINE_GLYPH — 337 refs corpus-wide per the audit.)

See `tools/_scratch/audit_image_routing.py` for the per-bucket counts.
"""
from __future__ import annotations

import re

from britannica.pipeline.stages.elements._image import (
    _parse_image_size,
    build_img_marker,
)

_FILE_RE = re.compile(
    r"\[\[(?:File|Image):([^\]]+)\]\]",
    re.IGNORECASE,
)

_LAYOUT_KEYWORDS = frozenset({
    "right", "left", "center", "centre",
    "thumb", "thumbnail",
    "frame", "framed", "frameless",
    "border", "none",
})

_SIZE_PARAM_RE = re.compile(r"^\d+(?:x\d+)?px$|^x\d+px$", re.IGNORECASE)


def _table_ranges(text: str) -> list[tuple[int, int]]:
    """Byte-ranges covered by `{|…|}` wikitables and `<table>` HTML.
    Template-body-aware: `{{Ts|vmi|}}` inner pipes don't fake-close
    the table."""
    ranges: list[tuple[int, int]] = []
    i = 0
    n = len(text)
    while i < n - 1:
        if text[i:i + 2] == "{|":
            start = i
            depth = 1
            j = i + 2
            while j < n - 1 and depth > 0:
                if text[j:j + 2] == "{{":
                    tdepth = 1
                    j += 2
                    while j < n - 1 and tdepth > 0:
                        if text[j:j + 2] == "{{":
                            tdepth += 1
                            j += 2
                        elif text[j:j + 2] == "}}":
                            tdepth -= 1
                            j += 2
                        else:
                            j += 1
                    continue
                if text[j:j + 2] == "{|":
                    depth += 1
                    j += 2
                elif text[j:j + 2] == "|}":
                    depth -= 1
                    j += 2
                else:
                    j += 1
            ranges.append((start, j))
            i = j
        else:
            i += 1
    for m in re.finditer(
        r"<table\b[^>]*>.*?</table\s*>", text,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        ranges.append((m.start(), m.end()))
    # Float-positioned <div> and <span> wrappers are block-layout
    # figures (e.g. `<div style="float:right;">&nbsp;[[File:Fig3|250px]]
    # <br>{{Fs|92%|{{sc|Fig.}} 3.—…}}</div>` — the captioned-figure
    # pattern in ACCUMULATOR).  Treat as block-wrapper so contained
    # file refs aren't promoted to inline.
    for m in re.finditer(
        r"<(div|span)\b[^>]*style\s*=\s*\"[^\"]*float\s*:[^\"]*\""
        r"[^>]*>.*?</\1\s*>",
        text, flags=re.DOTALL | re.IGNORECASE,
    ):
        ranges.append((m.start(), m.end()))
    return ranges


def _in_any(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in ranges)


def _classify_params(params: list[str]) -> tuple[bool, bool, str]:
    """Return (has_caption, has_layout, size_hint)."""
    has_caption = False
    has_layout = False
    size_hint = ""
    for p in params:
        p = p.strip()
        if not p:
            continue
        lower = p.lower()
        if lower in _LAYOUT_KEYWORDS:
            has_layout = True
            continue
        if lower == "upright" or lower.startswith("upright="):
            continue
        if _SIZE_PARAM_RE.match(lower):
            size_hint = lower
            continue
        if "=" in p:  # link=, alt=, …
            continue
        has_caption = True
    return (has_caption, has_layout, size_hint)


_PROSE_PUNCT = ",.;:?!—–-()'\""


def _is_inline_line(text: str, ref_start: int, ref_end: int) -> bool:
    """The file ref is immediately adjacent to prose on its own line.

    A char counts as prose if it's alphanumeric or a piece of sentence
    punctuation (`,`, `.`, `;`, `:`, `?`, `!`, `—`, `–`, `-`, `(`,
    `)`, `'`, `"`).  Whitespace within the same line (`' '`/`\\t`) is
    transparent; `\\n` terminates the search (the ref's prose context
    must be on the same line, NOT across structural boundaries).

    Either-side acceptance covers the alphabet-glyph article (vol 1
    p768) where each glyph sits at the start of its own wikitext line
    but is immediately followed by `, and also as` continuation prose
    on the same line.  Conversely, block figures wrapped in
    `{{center|\\n[[File:X|800px]]\\n}}` or
    `\\n\\n[[File:X|220px]]\\n\\n` fail both sides because they're
    isolated by newlines from any prose char."""
    # Walk back, skipping intra-line whitespace; stop at \n or BOL.
    i = ref_start - 1
    while i >= 0 and text[i] in " \t":
        i -= 1
    if i >= 0 and text[i] != "\n":
        if text[i].isalnum() or text[i] in _PROSE_PUNCT:
            return True

    # Walk forward, skipping intra-line whitespace; stop at \n or EOF.
    j = ref_end
    while j < len(text) and text[j] in " \t":
        j += 1
    if j < len(text) and text[j] != "\n":
        if text[j].isalnum() or text[j] in _PROSE_PUNCT:
            return True

    return False


def promote_inline_glyphs(text: str) -> str:
    """Rewrite the in-prose-line `[[File:X|Npx]]` refs to the unified
    `{{IMG:X|align=inline|width=…|height=…}}` marker.  All other file
    refs (including captioned, layout-keyword'd, table-wrapped, and
    stranded captionless blocks) are left intact for the standard
    element pipeline."""
    ranges = _table_ranges(text)

    def _maybe_rewrite(m: re.Match) -> str:
        if _in_any(m.start(), ranges):
            return m.group(0)
        inner = m.group(1)
        parts = inner.split("|")
        filename = parts[0].strip()
        has_caption, has_layout, size_hint = _classify_params(parts[1:])
        if has_caption or has_layout:
            return m.group(0)
        if not _is_inline_line(text, m.start(), m.end()):
            return m.group(0)
        width, height = (_parse_image_size(size_hint)
                         if size_hint else (None, None))
        return build_img_marker(
            filename, align="inline", width=width, height=height)

    return _FILE_RE.sub(_maybe_rewrite, text)
