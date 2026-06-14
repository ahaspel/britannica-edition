"""stamp_sections — the localized "dirty" major-section recognizer.

`preprocess_article` hands us the joined raw article body (title already split
off).  We recognize the **major** section headings — centered small-caps, in
their inconsistent source templates (`{{c|{{sc|…}}}}` / `{{csc|…}}` /
`{{center|N. {{sc|…}}}}`, roman in or out) — and tramp-stamp a labelled point
anchor `«SEC:slug|name»` before each, exactly the way `preprocess_article` stamps
`«TITLE»`.

ALL the messy recognition lives HERE and nowhere else (`[[feedback_producer_template]]`,
localized): the template variants, the caption gates, the whole-article *series*
test (the context that only this per-article site has), and the malformed-template
clamps.  Downstream stays clean — the walk renders the `«CTR»«SC»` heading
faithfully, the viewer iterates `«SEC»`+`«SH»` for the TOC, and `extract_xrefs`
finds the anchors already in place.

Why a point anchor and not a `«SEC»…«/SEC»` wrap: the wrap would need a `«SEC»`
bracket-node in the walk; a point anchor needs nothing — it is the nav target and
(carrying its own label) the TOC source, and the heading renders normally right
after it.
"""
import re

from britannica.util.strings import section_slug

# Centered-small-caps heading opener (the inconsistent template set).
_HEAD_OPEN = re.compile(r"\{\{\s*(csc|center|c)\s*\|", re.IGNORECASE)
# Caption look-alikes (the element's OWN content says it isn't a section).
_CAPWORD = re.compile(r"^\s*(?:Fig|Plate|Table|Pl|Diagram)\b", re.IGNORECASE)
# A numeral prefix (roman / single letter / digit + . — -) marks a section
# regardless of what follows; an UNnumbered heading is a section only if it is
# not a table caption (see _find_heads).
_NUMERAL = re.compile(r"^\s*(?:[IVXLCDM]+|[A-Z]|\d+)\s*[.—\-]")
_ROMAN_PREFIX = re.compile(r"^\s*(?:[IVXLCDM]+|[A-Z]|\d+)\s*[.—\-]+\s*")
# Zero-width things that may sit between the block boundary and the heading
# (a `{{anchor}}`, `{{clear}}`, or a page marker) — stepped over for the
# block-start test.
_PREHEAD = re.compile(
    r"\{\{\s*anchor\b[^}]*\}\}|\{\{\s*clear\s*\}\}|\x01PAGE:\d+\x01|\s+",
    re.IGNORECASE)
_SC_UNWRAP = re.compile(r"\{\{\s*c?sc\s*\|([^{}]*)\}\}", re.IGNORECASE)
_MARKER = re.compile(r"«/?[A-Za-z]+(?:\[[^\]]*\])?»")


def _balanced_end(s: str, i: int) -> int:
    """Index just past the `}}` closing the `{{` at i (handles nesting); -1 if
    the braces never balance (malformed source)."""
    depth, j, n = 0, i, len(s)
    while j < n - 1:
        two = s[j:j + 2]
        if two == "{{":
            depth += 1; j += 2
        elif two == "}}":
            depth -= 1; j += 2
            if depth == 0:
                return j
        else:
            j += 1
    return -1


def _visible(inner: str) -> str:
    """The heading's display text: unwrap `{{sc|…}}`, drop markers/HTML."""
    inner = _SC_UNWRAP.sub(r"\1", inner)
    inner = _MARKER.sub("", inner)
    inner = re.sub(r"<[^>]+>", "", inner)
    return inner.replace(" ", " ").strip()


def _find_heads(raw: str) -> list[tuple[int, str]]:
    """`(start, name)` for the major-section headings — the series, gated.

    Returns `[]` unless at least TWO survive (a lone centered-small-caps block
    is a one-off / caption, not a section — a false section is worse than a
    miss)."""
    heads: list[tuple[int, str]] = []
    for m in _HEAD_OPEN.finditer(raw):
        nl = raw.rfind("\n", 0, m.start())
        before = _PREHEAD.sub("", raw[nl + 1:m.start()])
        if before and before[-1] not in "}>":
            continue  # not at a block start (after ws/anchors + a block-closer)
        end = _balanced_end(raw, m.start())
        clamped = end < 0
        if clamped:  # malformed braces → clamp the heading at its line
            end = raw.find("\n", m.start())
            if end < 0:
                end = len(raw)
        full = raw[m.start():end]
        kind = m.group(1).lower()
        if kind in ("c", "center") and "{{sc" not in full.lower():
            continue  # centering without small-caps → not a heading
        if "[[File:" in full or "{{IMG" in full:
            continue  # image, not a heading
        inner = raw[m.end():end]
        inner = inner[:-2] if inner.endswith("}}") else inner.rstrip("}")
        name = _visible(inner).split("\n")[0].strip()  # clamp malformed names
        name = name.replace("»", "").replace("|", "/")
        if not name or _CAPWORD.match(name):
            continue  # caption (Fig./Plate./Table.)
        if not _NUMERAL.match(name):
            after = raw[end:end + 40].lstrip()
            if after.startswith("{|") or after.lower().startswith("<table"):
                continue  # unnumbered + leads a table → table caption
        heads.append((m.start(), name))
    return heads if len(heads) >= 2 else []


def stamp_sections(raw: str) -> str:
    """Insert a labelled point anchor `«SEC:slug|name»` before each recognized
    major-section heading.  Idempotent-safe: only ever inserts before a heading
    template, never inside one."""
    heads = _find_heads(raw)
    if not heads:
        return raw
    out = raw
    for start, name in reversed(heads):  # tail-first so positions stay valid
        slug = section_slug(_ROMAN_PREFIX.sub("", name))
        out = out[:start] + f"«SEC:{slug}|{name}»" + out[start:]
    return out
