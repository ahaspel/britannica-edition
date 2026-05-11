"""Stage 3: derive header (before first matter) and footer (after last).

The non-caption text bracketing the captioned-image content of a plate.
``_strip_bookend_markup`` does an aggressive cleanup beyond the standard
caption cleanup — it has to deal with template fragments and table-cell
attribute residue that show up at the edges of the plate body.
"""

from __future__ import annotations

import re

from britannica.parsers.plate.captions import _strip_caption_markup
from britannica.parsers.plate.models import CaptionFrag, ImageRef

def _strip_bookend_markup(text: str) -> str:
    """Aggressive cleanup for header/footer text — strips everything a
    caption cleanup strips, plus wiki-table row separators (``|-``),
    bare cell-attribute fragments (``|ac``, ``|valign="bottom"``),
    standalone pipe lines, AND unmatched template openings/closers
    (``{{center|`` with no nearby ``}}``, stray ``}}``).

    Bookend text often slices through the middle of a template span —
    BREWING's ``{{center|[[image:X]]…}}`` puts ``{{center|`` before the
    first matter and ``}}`` after the last.  Without unmatched-fragment
    stripping, the header would render as the literal word
    ``center`` (template name) and the footer as a stray ``}}``.
    """
    text = _strip_caption_markup(text)
    # Wiki-table cell-attribute syntax: ``align="x"``, ``colspan=2``,
    # ``width="100%"``, ``style="…"`` — these are wikitable grammar,
    # not text content.  Bookend text only ever sees them as residue
    # from cell prefixes the cell-walker didn't consume.
    text = re.sub(
        r'\b(?:align|valign|width|height|colspan|rowspan|style|class|'
        r'id|scope|bgcolor|cellpadding|cellspacing)'
        r'\s*=\s*'
        r'(?:"[^"]*"|\'[^\']*\'|[\w%#-]+)',
        "",
        text,
        flags=re.IGNORECASE,
    )
    # CSS ``property: value`` fragments left after ``style="…"`` is
    # gone or after a ``{{ts|…}}`` stripped to its last arg.  Only
    # property names that actually appear in EB1911 plate templates.
    text = re.sub(
        r'\b(?:width|height|padding|margin|border|background|color|'
        r'text-align|vertical-align|font-size|line-height|float)'
        r'(?:-(?:top|bottom|left|right|color|size|style|width|spacing|family))?'
        r'\s*:\s*'
        r'[^\s;|]+;?',
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^\s*\|\-+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|[a-zA-Z]{1,4}(?=\s|$|\|)", "", text)
    # Strip unmatched template-opener fragments: ``{{name|`` or ``{{name``
    # with no matching ``}}`` in the string.
    text = re.sub(r"\{\{[^{}|]+\|", "", text)
    text = re.sub(r"\{\{[^{}]*", "", text)
    text = re.sub(r"\}\}+", "", text)
    # Stray dashes left from ``|-`` row separators that the
    # multi-line regex above didn't catch (single-line bookend, or
    # collapsed whitespace already merged the line).
    text = re.sub(r"(?:^|\s)-(?=\s|$)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def derive_bookends(text: str, images: list[ImageRef],
                    captions: list[CaptionFrag]) -> tuple[str, str]:
    """Return ``(header, footer)`` derived from non-matter text at
    either end of the source."""
    matter_starts = (
        [r.pos for r in images]
        + [c.pos for c in captions]
    )
    matter_ends = (
        [r.end_pos for r in images]
        + [c.end_pos for c in captions]
    )
    if not matter_starts:
        cleaned = _strip_bookend_markup(text)
        return cleaned, ""
    first_pos = min(matter_starts)
    last_end = max(matter_ends)
    header = _strip_bookend_markup(text[:first_pos])
    footer = _strip_bookend_markup(text[last_end:])
    return header, footer


