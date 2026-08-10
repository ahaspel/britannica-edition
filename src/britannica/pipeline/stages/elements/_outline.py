"""Outline / hierarchical list detection and rendering.

Recognizes indented prose blocks that the source treats as hierarchical
lists (`:`-prefix runs, `{{em|N}}` templates, `&emsp;` runs) and emits
an OUTLINE marker that the viewer renders as nested ``<ul>``.

Public entry points: ``_extract_outlines`` (bounds recognition, mints the
«OUTLINE» placeholder) and ``recognize_outline`` (the decomposer's item split).
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.elements._registry import ElementRegistry


# Both are consumed ONLY via `.match(line, pos)` in `_split_leading_noncontent`,
# which anchors at `pos` — so neither carries a `^` (a `^` binds to the true string
# start and would never match at an offset, stopping the scan at the first prefix).
_LEADING_PLACEHOLDER_RE = re.compile(r"\x03ELEM:\d+\x03")   # extracted-element placeholder
# Leading NON-CONTENT that must not count as indent: the raw page-position
# sentinel and `{{nop}}`, the no-op a transcriber writes to force the break.
_LEADING_NONCONTENT_RE = re.compile(r"\x01PAGE:\d+\x01|\{\{\s*nop\s*\}\}")


def _strip_leading_placeholder(line: str) -> str:
    """Drop leading NON-CONTENT so indent detection sees the visible content.

    A page break at a list-line start must not change the line's indent profile.
    The outline is the one shape that reads its structure FROM that profile, so a
    position marker sitting in front of the `:` makes the line unrecognizable and
    the mark renders as literal text — BIRD p.978's `:::` above "Sub-order 7", and
    16 more like it (GASTROPODA's `:Fam. 29.`, FUNGI's `: Class II.`).

    Three forms of the same nothing, and all three occur:
      * an extracted-element PLACEHOLDER — when this runs after extraction;
      * the raw PAGE SENTINEL — `_walk_outline` runs this scan as a PRE-PASS on
        raw text, before the balanced walk extracts anything, so at that point
        the page break has not become a placeholder yet;
      * `{{nop}}` — MediaWiki's force-a-break no-op, which a transcriber puts
        immediately before a page break for exactly that reason.
    They stack (`{{nop}}` then sentinel), so strip to a fixed point.  This decides
    only what the recognizer LOOKS at; it moves no bytes."""
    return _split_leading_noncontent(line)[1]


def _split_leading_noncontent(line: str) -> tuple[str, str]:
    """`(non-content prefix, rest)`.  ONE splitter for both jobs — deciding what
    the recognizer looks at (rest), and rebuilding an item's content
    (prefix + rest) — so the inspect path and the mutate path cannot disagree
    about where content starts.

    The prefix is CARRIED, never dropped: it holds the page-position sentinel that
    anchors the scan link for that page.  Stripping it to make the colons reachable
    would trade a broken outline for a lost page marker."""
    i, n = 0, len(line)
    while i < n:
        for rx in (_LEADING_PLACEHOLDER_RE, _LEADING_NONCONTENT_RE):
            m = rx.match(line, i)
            if m and m.end() > i:
                i = m.end()
                break
        else:
            break
    return line[:i], line[i:]


def _outline_indent_depth(line: str) -> int | None:
    """Compute the visual-indent depth of `line`, or None if no indent
    marker is present.

    Recognized markers:
      • Leading `:`-prefix block (depth = colon count)
      • `{{em|N}}` template (depth = ceil(N))
      • Bare `{{em}}` / `{{gap}}` template (depth = 1)
      • Leading `&emsp;` / `&nbsp;` / `&ensp;` / `&thinsp;` entity run
        (depth = number of entities)
    """
    line = _strip_leading_placeholder(line)
    m = re.match(r"^(:+)", line)
    if m:
        return len(m.group(1))
    m = re.match(r"^\s*\{\{em\|([0-9.]+)\}\}", line)
    if m:
        try:
            return max(1, int(float(m.group(1))))
        except ValueError:
            return 1
    if re.match(r"^\s*\{\{(?:em|gap)\}\}", line):
        return 1
    m = re.match(r"^\s*((?:&(?:emsp|nbsp|ensp|thinsp);)+)", line)
    if m:
        return len(re.findall(r"&[a-z]+;", m.group(1)))
    return None


def _outline_is_bare_emphasis(line: str) -> bool:
    """A standalone bold / italic / sc line acts as a top-level
    hierarchy label (depth 0) within an outline — e.g. ARACHNIDA's
    ``''Grade A. ANOMOMERISTICA.''`` which sits between `::`-indented
    Sub-Class lines."""
    s = _strip_leading_placeholder(line).strip()
    if not s:
        return False
    # Accept both raw wikitext `'''…'''` / `''…''` and the post-
    # clean_pages marker forms `«B»…«/B»` / `«I»…«/I»`.  By the time
    # outlines are extracted, the source has been through
    # `_convert_quote_runs` so the marker forms are what we see in
    # practice; the raw forms are kept for safety / tests that bypass
    # clean_pages.
    return bool(
        re.fullmatch(r"'''[^\n]+'''[.,]?", s)
        or re.fullmatch(r"''[^\n]+''[.,]?", s)
        or re.fullmatch(r"«B»[^«\n]+«/B»[.,]?", s)
        or re.fullmatch(r"«I»[^«\n]+«/I»[.,]?", s)
        or re.fullmatch(r"\{\{sc\|[^{}]+\}\}[.,]?", s, re.IGNORECASE)
    )


# Range-style header: `N–M.—TITLE.<br />` (GEM plate captions, similar
# numbered-section openers).  Acts as a top-level label (depth 0) for
# the indented numbered items that follow.  Required to be SHORT and
# end with `<br />` so prose paragraphs that happen to start with
# `1–5.` don't false-match.
_OUTLINE_RANGE_HEADER_RE = re.compile(
    r"^\d+\s*[–—\-]\s*\d+\s*\.\s*[—–\-]+\s*[A-Z][^<\n]{0,80}<br\s*/?>\s*$",
    re.IGNORECASE,
)


def _outline_is_list_shaped(line: str) -> bool:
    if _outline_indent_depth(line) is not None:
        return True
    if _outline_is_bare_emphasis(line):
        return True
    if _OUTLINE_RANGE_HEADER_RE.match(_strip_leading_placeholder(line).strip()):
        return True
    return False


def _extract_outlines(
    text: str,
    registry: ElementRegistry,
) -> str:
    """Replace each `:`-anchored indent block with an OUTLINE placeholder, copying
    every other byte of `text` VERBATIM.  This is BOUNDS ONLY — the block's item and
    level splitting is the decomposer's job (`recognize_outline`), not this scan's.

    `:` is the unambiguous anchor: a block that contains ANY `:`-prefixed line is an
    outline (a lone `:` line included — that is the leak fix); a run with no `:` (pure
    {{em}}/&emsp;/bare-emphasis) is left as prose, since those signals only mean
    "level" INSIDE a `:`-anchored outline, where the decomposer reads them.  `_skip`
    steps over a construct whole, so a raw multi-line <math>/<poem> around a `:` line
    neither fools the scan nor ends a logical line early.
    """
    out: list[str] = []
    n = len(text)
    pos = 0
    while pos < n:
        le = _logical_line_end(text, pos)
        if _outline_is_list_shaped(text[pos:le]):
            end, has_colon = _indent_block_extent(text, pos)
            if has_colon:
                out.append(registry.add("OUTLINE", text[pos:end]))
                pos = end
                continue
        seg_end = le + 1 if le < n else n           # this line and its newline, verbatim
        out.append(text[pos:seg_end])
        pos = seg_end
    return "".join(out)


def _logical_line_end(text: str, i: int) -> int:
    """Index of the newline ending the logical line at `i` (or `len(text)`).  A newline
    INSIDE a construct doesn't count — `_skip` steps over `{{…}}`/`[[…]]`/`<math>`/
    `{|…|}` whole."""
    from britannica.pipeline.stages.elements._table_fold import _skip
    n = len(text)
    while i < n:
        j = _skip(text, i)
        if j > i:
            i = j
            continue
        if text[i] == "\n":
            return i
        i += 1
    return n


def _indent_block_extent(text: str, start: int) -> tuple[int, bool]:
    """From an indent line at `start`, return `(end, has_colon)` — the end index of the
    maximal run of contiguous indent lines (a blank line continues the run only if an
    indent line resumes after it) and whether any line in the run is `:`-prefixed."""
    def _is_colon(line: str) -> bool:
        return bool(re.match(r"^:+", _strip_leading_placeholder(line)))

    n = len(text)
    le = _logical_line_end(text, start)
    has_colon = _is_colon(text[start:le])
    end = le
    pos = le + 1 if le < n else n
    while pos < n:
        le = _logical_line_end(text, pos)
        line = text[pos:le]
        if _outline_is_list_shaped(line):
            has_colon = has_colon or _is_colon(line)
            end = le
            pos = le + 1 if le < n else n
            continue
        if not line.strip():                        # blank — continue only if the run resumes
            q = pos
            while q < n:
                lq = _logical_line_end(text, q)
                if text[q:lq].strip():
                    break
                q = lq + 1 if lq < n else n
            if q < n and _outline_is_list_shaped(text[q:_logical_line_end(text, q)]):
                pos = q
                continue
        break
    return end, has_colon


# ── Recursive recognition — the balanced-markup replacement ──────────────────
# `recognize_outline` is the twin of `_split_cells`: walk the block, jump every
# construct WHOLE via `_skip` (so a multi-line <math> on an indented line stays
# inside its item instead of shattering), and open a new item at each logical
# line's indent signal.  Depth is the existing colon-primary `_outline_indent_
# depth`.  No gate, no flatten — the classifier nests and recurses these items
# exactly as it does a table's rows and cells.

_INDENT_MARKER_RE = re.compile(
    r"^\s*(?::+|\{\{em(?:\|[0-9.]+)?\}\}|\{\{gap\}\}"
    r"|(?:&(?:emsp|ensp|nbsp|thinsp);)+|\s)+")


def _split_logical_lines(block: str) -> list[str]:
    """Split `block` on newlines EXCEPT those inside a construct — `_skip` steps
    over `{{…}}`/`[[…]]`/`<math>`/`{|…|}` whole, so a multi-line math expression
    on an indented line stays ONE logical line rather than many."""
    from britannica.pipeline.stages.elements._table_fold import _skip
    n, start, i, lines = len(block), 0, 0, []
    while i < n:
        j = _skip(block, i)
        if j > i:
            i = j
            continue
        if block[i] == "\n":
            lines.append(block[start:i])
            start = i + 1
        i += 1
    if start < n:
        lines.append(block[start:])
    return lines


def _outline_item_depth(line: str) -> int:
    """An outline item's nesting depth = the SUM of its leading indent units — each
    `:`, each `&emsp;`/`&ensp;`/`&nbsp;`/`&thinsp;`, and `{{em|N}}` as N.  Summing, not
    first-signal, is what lets a `:&emsp;&emsp;&emsp;` sub-case nest UNDER its plain-`:`
    sibling even where the source mixes colon and entity indent (ALGEBRA's (b) rows)."""
    m = _INDENT_MARKER_RE.match(_strip_leading_placeholder(line))
    if not m:
        return 1
    s = m.group(0)
    em = len(re.findall(r"&(?:emsp|ensp|nbsp|thinsp);", s))       # undecoded entities
    em += sum(1 for c in s if ord(c) in (0x2003, 0x2002, 0x00a0, 0x2009))     # decoded em/en/nbsp/thin
    for m2 in re.finditer(r"\{\{em\|([0-9.]+)\}\}", s):
        em += max(1, int(float(m2.group(1))))
    em += len(re.findall(r"\{\{(?:em|gap)\}\}", s))               # bare {{em}}/{{gap}} = 1 each
    return max(s.count(":"), 1) + (1 if em >= 2 else 0)


def recognize_outline(block: str) -> list[tuple[int, str]]:
    """Chop an indent block into `[(depth, content)]` items — the twin of
    `recognize_table`'s cell split.  A line carrying an indent signal opens an
    item at its depth; a bare-emphasis line is a depth-0 label; a signal-less
    line is a continuation of the item above.  Content keeps its raw markers so
    the classifier can recurse them (a `:<math>…` item's math becomes a child)."""
    items: list[tuple[int, str]] = []
    for line in _split_logical_lines(block):
        if not line.strip():
            continue
        depth = _outline_indent_depth(line)
        if depth is None:
            if _outline_is_bare_emphasis(line):
                items.append((0, line.strip()))
            elif items:                       # continuation of the item above
                d, c = items[-1]
                items[-1] = (d, (c + "\n" + line.strip()).strip())
            else:
                items.append((0, line.strip()))
        else:
            # `depth` (first-signal) only told us this IS an indent line; the NESTING
            # depth is the SUM of the leading units, so :&emsp;&emsp;&emsp; sub-cases nest.
            # Strip the indent markers from the CONTENT side only, then put the
            # non-content prefix back: the page sentinel rides INSIDE the item's
            # text, at the point the break occurs, and still renders its scan
            # link.  Dropping the prefix would lose the page marker; leaving it
            # in FRONT of the colons would leave them unstripped (the marker
            # regex is `^`-anchored), and the item would re-classify as an
            # outline of itself — an infinite descent.
            prefix, rest = _split_leading_noncontent(line)
            items.append((_outline_item_depth(line),
                          (prefix + _INDENT_MARKER_RE.sub("", rest)).strip()))
    return items
