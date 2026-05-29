"""Raw, recursive figure-component extraction — the ICL analog of
`_table_decompose`.

Given a figure table's RAW bytes, return its components — image(s),
caption, attribution, legend, footnote.  The point is the RECURSION:
when a cell holds a nested ``{|…|}`` that is itself a figure-table
(e.g. image + attribution), recurse to GATHER that inner table's
components as components of THIS figure, then merge with the outer's
own cells.  This is the fix for the figure family's central bug
(MARSUPIALIA): the walker/classifier *finalized* the nested table as a
terminal child, short-circuiting the outer figure's extraction.  Here
the extractor owns the recursion and gathers components instead.

`_assemble_figure_parts` (the assembler) is UNCHANGED — it already
produces a correct figure given correct components.  All the work is
getting extraction right.

Status: additive / inert.  Not wired into any producer yet; exercised
only by direct-feed unit tests until the gate + producers migrate onto
it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

TextTransform = Callable[[str], str]

_IMAGE_NS_LINK_RE = re.compile(r"\[\[(?:File|Image):[^\]]*\]\]", re.IGNORECASE)
_IMAGE_FILENAME_RE = re.compile(
    r"\[\[(?:File|Image):([^\]|]+)", re.IGNORECASE)
_REF_RE = re.compile(r"<ref\b[^>]*>.*?</ref>", re.DOTALL | re.IGNORECASE)
# A `Fig. N.` / `Plate N.` / `{{sc|Fig.}}` caption opener.
_FIG_MARKER_RE = re.compile(
    r"\{\{\s*(?:sc|csc|SC)\s*\|\s*(?:Fig|Plate)s?\.?"
    r"|(?<![A-Za-z])(?:Fig|Plate)s?\.?\s*\d",
    re.IGNORECASE)
# Attribution credit phrasing — "From X", "After X", "by permission",
# "Photo, …".  Conservative: only the recognised credit openers.
_ATTRIBUTION_RE = re.compile(
    r"^\s*(?:from\b|after\b|photo\b|reduced from\b|by permission\b|"
    r"copied from\b|redrawn\b)",
    re.IGNORECASE)


@dataclass
class FigureComponents:
    images: list[str] = field(default_factory=list)       # filenames
    caption_parts: list[str] = field(default_factory=list)
    attribution_parts: list[str] = field(default_factory=list)
    legend_lines: list[str] = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)     # raw <ref>…


def _peel_table(raw: str) -> str:
    """Strip the outer ``{|…|}`` (wiki) or ``<table>…</table>`` (HTML)
    delimiters, returning the inner content (nested tables intact)."""
    s = raw.strip()
    if s.startswith("{|"):
        s = re.sub(r"^\{\|[^\n]*\n?", "", s)
        return re.sub(r"\n?\|\}\s*$", "", s)
    m = re.match(r"<table\b[^>]*>", s, re.IGNORECASE)
    if m:
        return re.sub(r"</table>\s*$", "", s[m.end():], flags=re.IGNORECASE)
    return s


def extract_figure_components(
    raw: str, text_transform: TextTransform,
) -> FigureComponents:
    """Extract a figure's components from its RAW bytes, recursing into
    nested figure-tables to gather (not finalize) their components."""
    comps = FigureComponents()
    _gather(_peel_table(raw), comps, text_transform)
    return comps


def _gather(inner: str, comps: FigureComponents, tt: TextTransform) -> None:
    from britannica.pipeline.stages.elements._table_decompose import (
        extract_wiki_rows, find_nested_table_spans,
    )
    _caption, rows = extract_wiki_rows(inner)
    for _row_attrs, cells in rows:
        for _sep, _attr, content in cells:
            _gather_cell(content, comps, tt)


def _gather_cell(content: str, comps: FigureComponents,
                 tt: TextTransform) -> None:
    from britannica.pipeline.stages.elements._table_decompose import (
        find_nested_table_spans,
    )
    content = content.strip()
    if not content:
        return

    # Nested table → two cases (no-drop both ways):
    #   * contains an image → it's a sub-figure CONTAINER: RECURSE to gather
    #     its components (image + attribution + …) into THIS figure.
    #   * no image → it's a LEGEND (a table inside a figure is a key);
    #     everything in it goes to legend.  Matches production's
    #     TABLE-child legend signal; the structural baseline.
    spans = find_nested_table_spans(content)
    for start, end in reversed(spans):
        nested_raw = content[start:end]
        if _IMAGE_NS_LINK_RE.search(nested_raw):
            _gather(_peel_table(nested_raw), comps, tt)
        else:
            _gather_legend_table(nested_raw, comps, tt)
        content = content[:start] + content[end:]
    content = content.strip()
    if not content:
        return

    # Footnotes — carry the raw <ref> through; strip from the typed text.
    refs = _REF_RE.findall(content)
    if refs:
        comps.footnotes.extend(refs)
        content = _REF_RE.sub("", content).strip()
        if not content:
            return

    # Image at this level.
    img = _IMAGE_FILENAME_RE.search(content)
    if img:
        comps.images.append(img.group(1).strip())
        content = _IMAGE_NS_LINK_RE.sub("", content).strip()
        if not content:
            return

    # Drop non-content noise — `<br>`, spacer entities (`&emsp;`), bare
    # punctuation — left over after pulling images/refs.  Only substantive
    # text (some alphanumeric) is a real caption/attribution/legend.
    content = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE).strip()
    if not _has_text(content):
        return

    # Type the remaining prose: caption (Fig./Plate. marker), attribution
    # (credit phrasing), else caption.
    if _FIG_MARKER_RE.search(content):
        marker = _FIG_MARKER_RE.search(content)
        before = content[:marker.start()].strip()
        after = content[marker.start():].strip()
        if before and _ATTRIBUTION_RE.match(before):
            comps.attribution_parts.append(_clean(tt(before)))
        elif before:
            comps.caption_parts.append(_clean(tt(before)))
        if after:
            comps.caption_parts.append(_clean(tt(after)))
    elif _ATTRIBUTION_RE.match(content):
        comps.attribution_parts.append(_clean(tt(content)))
    else:
        comps.caption_parts.append(_clean(tt(content)))


def _gather_legend_table(table_raw: str, comps: FigureComponents,
                         tt: TextTransform) -> None:
    """A no-image nested table inside a figure is a LEGEND — every row
    becomes a legend line (cells joined, so `|A.||text` → "A. text").
    No grammar inspection: a table here IS a legend (the structural rule)."""
    from britannica.pipeline.stages.elements._table_decompose import (
        extract_wiki_rows,
    )
    _caption, rows = extract_wiki_rows(_peel_table(table_raw))
    for _attrs, cells in rows:
        line = " ".join(
            _clean(tt(c)) for _s, _a, c in cells if _has_text(c)).strip()
        if line:
            comps.legend_lines.append(line)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _has_text(s: str) -> bool:
    """True iff `s` carries substantive text — some alphanumeric remains
    after stripping HTML entities and inline markers.  Filters spacer
    cells (`&emsp;`), bare `<br>` runs, and punctuation-only leftovers."""
    s = re.sub(r"&[a-zA-Z]+;|&#\d+;", "", s)
    s = re.sub(r"«/?[A-Z]+»", "", s)
    return bool(re.search(r"[A-Za-z0-9]", s))
