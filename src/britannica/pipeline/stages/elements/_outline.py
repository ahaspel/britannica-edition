"""Outline / hierarchical list detection and rendering.

Recognizes indented prose blocks that the source treats as hierarchical
lists (`:`-prefix runs, `{{em|N}}` templates, `&emsp;` runs) and emits
an OUTLINE marker that the viewer renders as nested ``<ul>``.

Public dispatch entry: ``_extract_outlines`` (called during extraction),
``_process_outline`` (called during reassembly).
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.elements._registry import ElementRegistry


_LEADING_PLACEHOLDER_RE = re.compile(r"^\x03ELEM:\d+\x03")  # leading extracted-element placeholder (the page break is now a PAGE element)


def _strip_leading_placeholder(line: str) -> str:
    """Drop a leading extracted-element placeholder so indent detection
    sees the visible content.  A page break that falls at a list-line
    start is now a PAGE element, so the line begins with that element's
    placeholder; the recognizer steps past it to reach the `:` exactly
    as it would past any element a line happens to begin with.  The
    placeholder rides through untouched and is substituted back after."""
    return _LEADING_PLACEHOLDER_RE.sub("", line)


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
    """Find runs of visually-indented hierarchical content and replace
    each with an OUTLINE placeholder.

    Detection signal:
      • 4+ consecutive non-empty lines, each carrying a visual-indent
        marker (`:`-prefix, `{{em|N}}` / `{{gap}}` template, or
        leading `&emsp;`/`&nbsp;` entity run) OR being a bare-emphasis
        hierarchy label (`'''Foo.'''`, `''Bar.''`, `{{sc|Baz.}}`)
      • 2+ DISTINCT indent depths in the run (it's hierarchical, not
        a flat list — a flat list renders fine as a table or `<ol>`)
      • at least one bold/italic/sc emphasis token in the run

    `<poem>` / `<math>` / `<ref>` content is already placeholdered by
    the time this runs, so verse stanzas with `{{em|N}}` indent and
    multi-line math expressions don't trigger detection.

    Captures: ARACHNIDA Tabular Classification, ZOOLOGY taxonomies
    (~10 pages in vol 28), botanical/lichen taxonomies, BIBLE Apocrypha
    listing, SANSKRIT phonology, EYE disease classification, etc. —
    ~30 pages corpus-wide.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not _outline_is_list_shaped(lines[i]):
            out.append(lines[i])
            i += 1
            continue

        block_start = i
        block_lines: list[str] = []
        depths: set[int] = set()
        has_emphasis = False
        while i < len(lines):
            line = lines[i]
            if _outline_is_list_shaped(line):
                d = _outline_indent_depth(line)
                if d is None:
                    # Bare-emphasis line — top-level (depth 0).
                    depths.add(0)
                else:
                    depths.add(d)
                block_lines.append(line)
                _ll = line.lower()
                if (
                    "'''" in line or "''" in line
                    or "«B»" in line or "«I»" in line
                    or "{{sc|" in _ll or "{{csc|" in _ll
                    or "{{asc|" in _ll or "{{small-caps|" in _ll
                    or "{{uc|" in _ll or "{{lc|" in _ll
                    or "<i>" in _ll or "<b>" in _ll or "<em>" in _ll
                ):
                    has_emphasis = True
                i += 1
                continue
            stripped = line.rstrip()
            if not stripped:
                # Blank line: continue if the next non-blank rejoins.
                j = i + 1
                while j < len(lines) and not lines[j].rstrip():
                    j += 1
                if j < len(lines) and _outline_is_list_shaped(lines[j]):
                    block_lines.extend(lines[i:j])
                    i = j
                    continue
                break
            break

        non_empty = [ln for ln in block_lines if ln.strip()]
        if (
            len(non_empty) >= 4
            and len(depths) >= 2
            and has_emphasis
        ):
            block_text = "\n".join(block_lines).rstrip()
            placeholder = registry.add("OUTLINE", block_text)
            out.append(placeholder)
        else:
            out.extend(block_lines)
            if i == block_start:
                if not block_lines:
                    out.append(lines[i])
                    i += 1

    return "\n".join(out)


def _process_outline(inner: str) -> str:
    """Convert a `:`-indented outline block into an OUTLINE marker.

    Output format:
        «OUTLINE:
        N|content
        N|content
        …
        «/OUTLINE»

    where ``N`` is the source indent depth (number of leading `:` —
    bare emphasis lines get depth 0).  Content's inline markers (italic/
    bold/sc/footnotes, links) were extracted by the walker and ride
    through as placeholders that ``produce_tree`` substitutes.  Viewer.html maps the marker to a nested
    ``<ul>`` keyed on indent depth (densely re-ranked so 0/2/3/4/6/8
    source depths become 0/1/2/3/4/5 nesting levels).
    """
    items: list[tuple[int, str]] = []
    for raw_line in inner.split("\n"):
        line = raw_line.rstrip()
        if not line:
            continue
        # Lift any leading element placeholder so it survives in the
        # rendered item — a page break landing at a list-line start is
        # itself a PAGE element now — but doesn't interfere with the
        # indent-prefix stripping below.
        page_marker = ""
        pm = _LEADING_PLACEHOLDER_RE.match(line)
        if pm:
            page_marker = pm.group(0)
            line = line[pm.end():]
        depth = _outline_indent_depth(line)
        if depth is None:
            # Bare-emphasis line (top-level hierarchy label).
            depth = 0
            content = line.strip()
        else:
            # Strip the indent marker(s) from the content.
            content = re.sub(r"^:+", "", line)
            content = re.sub(
                r"^\s*(?:\{\{em\|[0-9.]+\}\}|\{\{(?:em|gap)\}\})\s*",
                "", content,
            )
            content = re.sub(
                r"^\s*(?:&(?:emsp|nbsp|ensp|thinsp);)+\s*",
                "", content,
            )
            content = content.lstrip()
        # Strip trailing `<br>` line-end (typesetter break, not
        # visible content) — applies to both branches.
        content = re.sub(r"<br\s*/?>\s*$", "", content, flags=re.IGNORECASE)
        content = content.rstrip()
        content = page_marker + content
        if not content:
            continue
        # Run content through the inline-marker transform so italic /
        # bold / sc / fn / link templates become «I»…«/I» / «B»… etc.
        # Don't run `_clean_text` — that would strip the markers we
        # want the viewer to convert to <i>/<b>/<span class="sc">.
        rendered = content.strip()
        if not rendered:
            continue
        # Collapse trailing `\n` and inner whitespace runs.
        rendered = re.sub(r"\s+", " ", rendered)
        items.append((depth, rendered))

    if not items:
        return ""

    body = "\n".join(f"{d}|{c}" for d, c in items)
    return f"«OUTLINE:\n{body}\n«/OUTLINE»"
