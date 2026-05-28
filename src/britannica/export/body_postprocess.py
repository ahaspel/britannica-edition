"""Body-text post-processing helpers used by the article exporter.

These run after the elements/transform pipeline has produced an
article body in marker form (``«B»…«/B»``, ``«LN:…«/LN»``,
``\\x01PAGE:N\\x01`` etc.) and before the final JSON payload is written.

Each function takes a string (or pre-compiled regex) and returns a
string or computed range list.  No DB access, no shared mutable
state — they can be called from any layer that already owns the body.
"""

from __future__ import annotations

import re

from britannica.markers import strip_page_markers


# `_strip_redundant_title` removed: title chop-up happens at source in
# detect_boundaries — `_extract_bold_delimited_title` + `produce_title`
# extract the title from the article opening and leave a clean body in
# segment_text.  Stale DB rows persisted before the chop-up fix will
# display the title-bold in their body until re-detected; that's a
# known transition cost, not something to sweep.


# Structured-content spans we must not wrap inside (breaking them
# would corrupt table / math / preformatted rendering).  Footnotes
# are intentionally NOT protected — their prose deserves the same
# cross-reference treatment as the main body.
_PROTECTED_SPAN_RES = (
    re.compile(r"«LN:.*?«/LN»", re.DOTALL),
    re.compile(r"«HTMLTABLE:.*?«/HTMLTABLE»", re.DOTALL),
    re.compile(r"«MATH:.*?«/MATH»", re.DOTALL),
    re.compile(r"«OUTLINE:.*?«/OUTLINE»", re.DOTALL),
    re.compile(r"«PLATE_OUTLINE:.*?«/PLATE_OUTLINE»", re.DOTALL),
)


def _protected_ranges(body: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for pat in _PROTECTED_SPAN_RES:
        for m in pat.finditer(body):
            ranges.append((m.start(), m.end()))
    return ranges


_BIBLIOGRAPHIC_PATTERNS = (
    # Year citations: ", 1901" or "(1901)" — typical author / work refs.
    re.compile(r"[,(]\s*1[6-9]\d{2}\b"),
    re.compile(r"[,(]\s*20\d{2}\b"),
    # Page / volume / issue markers: "pp. 5-10", "vol. iii", "no. 12".
    re.compile(r"\b(?:pp?\.|vol\.|no\.)\s*[ivxlcdm\d]", re.IGNORECASE),
    # "Letters, i. 268" — roman-or-arabic numeral + dot + arabic.
    re.compile(r",\s*(?:[ivxlcdm]+|\d+)\.\s*\d+", re.IGNORECASE),
    # Journal-abbreviation pattern: "Quart. Jour.", "Ann. Mag.", etc.
    re.compile(r"\b[A-Z][a-z]{2,}\.\s+[A-Z][a-z]{2,}\."),
)


def _looks_bibliographic(surface: str) -> bool:
    """Cheap heuristic: does this (See …) / (See also …) surface look
    like a bibliographic citation rather than an article reference?

    The extractor's own _is_bibliographic filter catches most, but
    some slip through (e.g., "(See Pocock, Quart. Jour. Micr. Sci.,
    1901.)" resolves POCOCK to the admiral article — wrong).
    Refuse to wrap these at the body level even if the resolver hit.
    """
    if not surface:
        return False
    for pat in _BIBLIOGRAPHIC_PATTERNS:
        if pat.search(surface):
            return True
    return False


def _clean_surface_for_matching(surface: str) -> str:
    """Strip «X» markers and PAGE markers so the surface_text can be
    located against an export-stage body that may have markers
    interleaved."""
    s = re.sub(r"«/?[A-Z]+(?::[^«»]*)?»", "", surface)
    s = strip_page_markers(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
