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

from britannica.markers import strip_page_markers, strip_title_markers


def _strip_redundant_title(body: str, title: str) -> str:
    """Strip a body's leading '«B»…«/B»' title matter that duplicates the
    article title. Handles single-bold ('''PIETAS''') and multi-bold
    ('''POPILIA''' (or Popillia), '''VIA,''') forms by accumulating the
    visible text of consecutive bold + interstitial chunks and comparing
    to the article title."""
    page_m = re.match(r"^(\x01PAGE:\d+\x01)?\s*", body)
    page_prefix = page_m.group(0) if page_m else ""
    rest = body[len(page_prefix):]

    # Titles may carry `«B»`/`«I»`/`«SC»` formatting markers; strip
    # them for content comparison against the body's bold text.
    title_key = re.sub(
        r"\s+", " ",
        strip_title_markers(title).strip().rstrip(",.;:"),
    ).upper()
    bold_re = re.compile(
        r"^«B»([^«]+)«/B»"
        r"([\s,.\-–— ]*(?:\([^)]*\)|\[[^\]]*\])"
        r"[\s,.\-–— ]*|[\s,.\-–— ]+)?"
    )

    cursor = 0
    accumulated = ""
    best_end = -1
    while True:
        m = bold_re.match(rest[cursor:])
        if not m:
            break
        bold_text = m.group(1).strip().rstrip(",.;:")
        interstitial = (m.group(2) or "").strip()
        if accumulated:
            accumulated += " "
        accumulated += bold_text
        if interstitial:
            accumulated += " " + interstitial
        cursor += m.end()
        normalized = re.sub(r"\s+", " ", accumulated.rstrip(" ,.;:")).upper()
        if normalized == title_key:
            best_end = cursor
            break
        if not title_key.startswith(normalized):
            break

    if best_end < 0:
        # Fall back to single-bold strip when the article title contains
        # the first bold as a prefix (covers PIETAS / SEMMELWEISS style).
        fallback = re.match(
            r"^«B»([^«]+)«/B»"
            r"[\s,.\-–—]*",
            rest,
        )
        if fallback:
            bold = fallback.group(1).strip().rstrip(",.;:").upper()
            if (bold == title_key
                    or title_key.startswith(bold + ",")
                    or title_key.startswith(bold + " ")
                    or bold.startswith(title_key + ",")
                    or bold.startswith(title_key + " ")):
                best_end = fallback.end()

    if best_end >= 0:
        tail = re.sub(r"^[\s,.\-–— ]+", "", rest[best_end:])
        return page_prefix + tail
    return body


# Structured-content spans we must not wrap inside (breaking them
# would corrupt table / math / preformatted rendering).  Footnotes
# are intentionally NOT protected — their prose deserves the same
# cross-reference treatment as the main body.
_PROTECTED_SPAN_RES = (
    re.compile(r"«LN:.*?«/LN»", re.DOTALL),
    re.compile(r"«HTMLTABLE:.*?«/HTMLTABLE»", re.DOTALL),
    re.compile(r"«MATH:.*?«/MATH»", re.DOTALL),
    re.compile(r"«PRE:.*?«/PRE»", re.DOTALL),
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
