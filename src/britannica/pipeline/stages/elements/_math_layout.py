"""Math / equation layout detection and rendering.

Wiki tables that are spatial math layouts (equation systems,
determinants, matrices) rather than tabular data.

A math-layout table is one where the wiki ``{|…|}`` exists for visual
positioning of math content, not to express tabular structure.  The
math content arrives in one of three encodings:

* **tokens** — cells contain raw math tokens (italicised letters,
  subscripts, operators).  Pre-LaTeX-style transcription as seen on
  ALGEBRAIC FORMS.  Rendered as KaTeX ``\\begin{aligned}`` /
  ``\\begin{vmatrix}``.
* **math_blocks** — cells contain ``<math>…</math>`` elements (which
  reach this stage as registered MATH placeholders).  Pure LaTeX
  transcription as seen on DIFFERENCES, CALCULUS OF.  Rendered as
  one paragraph per row, each holding the math placeholder.
* **html_wrapper** — wikitable wraps an inner HTML ``<table>`` whose
  content is the actual math layout (poems of equations,
  rowspan-based fractions, ``{{Polytonic|…}}`` templates).  The outer
  wikitable's only job is positioning the math block alongside an
  equation-number cell.  Seen on INTERPOLATION p738/p739 and
  HYDRAULICS p120.  Rendered as paragraphs, letting the inner
  HTML_TABLE handle the math.

The three encodings share a structural signature: the wiki table has
no data-table markers (``class=wikitable``, ``border=N``, ``rules=``,
``<ref>``), and its rows are math content in some form.  Detection
and dispatch are unified in :func:`_math_table_kind` /
:func:`_process_math_table_layout`; legacy split detectors and
handlers (``_is_math_layout`` / ``_is_equation_layout`` /
``_process_math_layout_table`` / ``_process_equation_layout``) are
kept as thin wrappers for incoming callers.

Public entry points:
- ``_math_table_kind`` — return one of "tokens", "math_blocks",
  "html_wrapper", or None.  Consumed by ``_classify_table``.
- ``_process_math_table_layout`` — unified renderer, dispatched from
  ``_process_element``.
- ``_is_math_dominant_layout`` — separate predicate for the rowspan
  exception in ``_classify_table``; unchanged.
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.elements._registry import ElementRegistry, _PH
from britannica.pipeline.stages.elements._tables import (
    _CELL_ATTR_RE,
    parse_wiki_table,
)


_MATH_CELL_RE = re.compile(
    r"^(?:"
    r"''[A-Za-z]''"
    r"|<su[pb]>[^<]{1,8}</su[pb]>"
    r"|\{\{Greek\|[^}]{1,8}\}\}"
    r"|\{\{sfrac\|[^}]{1,20}\}\}"
    r"|\{\{[A-Za-z]+\s*\|[^}]{1,30}\}\}"
    r"|[0-9]+"
    r"|[+\-=＝×·()/., −÷≠≤≥≡→]"
    r"|&nbsp;|&minus;|&emsp;|&ensp;|&thinsp;"
    r"|<br\s*/?>"
    r")+$",
    re.IGNORECASE,
)


def _parse_math_layout_cells(inner: str) -> list[str] | None:
    """Return list of cell content strings for a candidate math-layout
    table, or None if the table has a header (``!`` sigil) row."""
    cells: list[str] = []
    for line in inner.split("\n"):
        s = line.strip()
        if not s or s.startswith("|+") or s == "|}" or s.startswith("|-"):
            continue
        if s.startswith("!"):
            return None  # header row disqualifies
        if not s.startswith("|"):
            continue
        body = s[1:]
        body = re.sub(r"\{\{[^}]*\}\}",
                      lambda m: m.group(0).replace("|", "\x04"), body)
        for chunk in body.split("||"):
            if "|" in chunk:
                _, _, content = chunk.rpartition("|")
            else:
                content = chunk
            content = content.replace("\x04", "|").strip()
            content = re.sub(r"<span\s[^>]*>|</span>", "", content)
            if content:
                cells.append(content)
    return cells


def _is_math_layout(raw: str, inner: str) -> bool:
    """Detect tables that hold math content as positional layout
    (equation systems, determinants, matrices) rather than prose data.

    Seen on ALGEBRAIC FORMS (vol 1 p624+): transcribers used
    ``{|{{ts|…}}|}`` wikitables to align successive terms of an
    equation system or the cells of a determinant.  Rendering such
    tables as HTML data-tables gives a wholly wrong visual result —
    they should go through KaTeX as ``\\begin{aligned}`` /
    ``\\begin{vmatrix}`` blocks instead.

    Requires:
      * No ``class=wikitable``/``border=N``/``rules=`` data signal.
      * No ``<ref>`` footnotes (those don't appear in math layouts).
      * No header row (no ``!`` sigil cell).
      * Every cell matches the narrow math-token regex.
      * ≥ 2 cells with a strong math signature (``<su[pb]>`` tag, or
        an arithmetic operator joining operands).
    """
    header = raw.split("\n", 1)[0]
    if re.search(r'class\s*=\s*"?[^"\s]*(?:wikitable|tablecolhd)',
                 header, re.IGNORECASE):
        return False
    if re.search(r'border\s*=\s*"?[1-9]|rules\s*=',
                 header, re.IGNORECASE):
        return False
    if re.search(r"<ref[\s>]", raw, re.IGNORECASE):
        return False
    cells = _parse_math_layout_cells(inner)
    if cells is None or len(cells) < 2:
        return False
    if any(len(c) > 250 for c in cells):
        return False
    if not all(_MATH_CELL_RE.match(c) for c in cells):
        return False
    strong = 0
    for c in cells:
        if re.search(r"<su[pb]>", c):
            strong += 1
        elif re.search(
                r"[+\-−=＝×÷]\s*(?:''|[0-9(])", c):
            strong += 1
    return strong >= 2


def _math_cell_to_latex(content: str) -> str:
    """Convert a wikitext math cell to LaTeX token sequence."""
    # Strip {{ts|…}} styling leftovers
    content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*\|?\s*", "", content)
    # Italic letter run: ''xyz'' → xyz
    content = re.sub(r"''([A-Za-z]+)''", r"\1", content)
    # Sub/sup
    content = re.sub(r"<sub>([^<]+)</sub>", r"_{\1}",
                     content, flags=re.IGNORECASE)
    content = re.sub(r"<sup>([^<]+)</sup>", r"^{\1}",
                     content, flags=re.IGNORECASE)
    # Greek template: keep the character (KaTeX renders Unicode Greek)
    content = re.sub(r"\{\{Greek\|([^}]+)\}\}", r"\1",
                     content, flags=re.IGNORECASE)
    content = content.replace("＝", "=")   # fullwidth =
    content = content.replace("−", "-")   # unicode minus
    content = content.replace("×", r"\times ")
    content = content.replace("·", r"\cdot ")
    content = re.sub(r"<span[^>]*>|</span>", "", content)
    content = re.sub(r"&nbsp;|&emsp;|&ensp;|&thinsp;", " ", content)
    content = re.sub(r"\s+", " ", content).strip()
    return content


def _process_math_layout_table(raw: str) -> str:
    """Emit a math-layout wikitable as a KaTeX math block.

    Table parsing is shared with the other wiki-table paths
    (``parse_wiki_table``); the math-layout specialisation is
    ``_math_cell_to_latex`` per cell + ``\\begin{aligned}`` /
    ``\\begin{vmatrix}`` wrapping depending on whether the rows are
    equations (share an ``=`` column) or a matrix/determinant grid.
    """
    _, parsed_rows = parse_wiki_table(raw)
    rows: list[list[str]] = []
    for parsed_row in parsed_rows:
        row_cells = [
            _math_cell_to_latex(content)
            for _sep, _attr, content in parsed_row
            if content
        ]
        if row_cells:
            rows.append(row_cells)
    if not rows:
        return ""
    is_eqn = any("=" in "".join(row) for row in rows)
    if is_eqn:
        lines = []
        for row in rows:
            line = " ".join(row).strip()
            # Align on first = → &=
            line = re.sub(r"^(.*?)=(.*)$", r"\1 &= \2", line, count=1)
            lines.append(line)
        latex = ("\\begin{aligned}\n" + " \\\\\n".join(lines)
                 + "\n\\end{aligned}")
    else:
        lines = [" & ".join(row) for row in rows]
        latex = ("\\begin{vmatrix}\n" + " \\\\\n".join(lines)
                 + "\n\\end{vmatrix}")
    from britannica.math_widths import scale_hint
    # Canonicalise whitespace so the hash matches `_process_math`'s
    # form and the offline width cache.
    latex = re.sub(r"\s+", " ", latex).strip()
    hint = scale_hint(latex)
    if hint:
        return f"\n\n«MATH[{hint}]:{latex}«/MATH»\n\n"
    return f"\n\n«MATH:{latex}«/MATH»\n\n"


def _is_math_dominant_layout(
    raw: str, inner: str, inner_registry: ElementRegistry | None
) -> bool:
    """Detect equation-system tables whose only non-math content is
    decorative brace / equation-number cells with rowspan/colspan.

    The rowspan-first guard in `_classify_table` defends against
    `{{Ts}}`-induced phantom-cell misclassification of real data tables;
    this exception lets through tables that are unambiguously math
    layouts: ≥75% of registered child elements are MATH placeholders,
    no other element type contributes content (no IMAGE, REF, TABLE,
    POEM children), no header (`!`) row, no explicit data-table class
    (wikitable / tablecolhd / border) on the `{|` header, and ≤1 plain
    cell with substantive alphabetic prose (≥3 letters).  Tables like
    BARTON BEDS / PONTOON have decorative `\\Big\\}` MATH brackets but
    the bulk of their cells are plain-text data — those must NOT be
    treated as math layouts even though every registered child is MATH.
    """
    if inner_registry is None:
        return False
    elements = list(inner_registry.elements.values())
    if not elements:
        return False
    math_ct = sum(1 for t, _ in elements if t == "MATH")
    if math_ct < 2 or math_ct < len(elements) * 0.75:
        return False
    # Disqualifying child types — a real data table that happens to
    # have a few <math> cells (chemistry / physics tables) usually
    # also carries images, refs, or nested tables.
    for t, _ in elements:
        if t in {"IMAGE", "IMAGE_FLOAT", "REF", "TABLE", "HTML_TABLE",
                 "POEM"}:
            return False
    if re.search(r"^\s*!", raw, re.MULTILINE):
        return False
    # Explicit data-table class / border / rules in the {| header is a
    # definitive signal — never treat such a table as math layout.
    header = raw.split("\n", 1)[0]
    if (re.search(r'border\s*=\s*"?[1-9]', header, re.IGNORECASE)
            or re.search(r'rules\s*=', header, re.IGNORECASE)
            or re.search(r'class\s*=\s*"?[^"\s]*'
                         r'(?:wikitable|tablecolhd|border)',
                         header, re.IGNORECASE)):
        return False
    # Substantive-prose check: count non-MATH cells (cells with no
    # placeholder) that carry ≥3 alphabetic characters after styling
    # is stripped.  ≥2 such cells means the MATH children are
    # decorative bracket symbols, not the table's main payload.
    prose_cells = 0
    _ATTR_ONLY = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)\s*=",
        re.IGNORECASE,
    )
    for raw_row in re.split(r"\|-[^\n]*", inner):
        protected = re.sub(r"\{\{[^}]*\}\}",
                           lambda m: m.group(0).replace("|", "\x04"),
                           raw_row)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+"
                           + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"),
                           protected)
        for cell in re.findall(r"\|([^|\n]*)", protected):
            s = cell.replace("\x04", "|").strip()
            if not s or s in ("}", "{|"):
                continue
            if _PH in s:
                continue
            if _ATTR_ONLY.match(s):
                continue
            stripped = re.sub(r"\{\{[^{}]*\}\}", "", s)
            stripped = re.sub(r"<[^>]+>", "", stripped)
            stripped = re.sub(r"&[a-zA-Z]+;", "", stripped)
            if len(re.sub(r"[^A-Za-z]", "", stripped)) >= 3:
                prose_cells += 1
                if prose_cells >= 2:
                    return False
    return True


def _is_equation_layout(inner: str, inner_registry: ElementRegistry | None) -> bool:
    """Detect wiki tables used for equation alignment, not data display.

    Three signatures:
      1. Mostly MATH placeholders (from <math> tags in cells)
      2. ``{{sfrac}}`` template + ``(N)`` numeric label cell — equation
         systems written with `{{sfrac}}` instead of `<math>` (ORDNANCE
         p244 shrinkage equations).  At least one row must combine the
         two markers; the (N) label is the distinctive equation-number
         signature that data tables don't use.
      3. Mostly empty spacer cells without cell-level align attributes
    """
    # Check 1: majority MATH placeholders
    if _PH in inner and inner_registry:
        math_ct = sum(1 for lbl in inner_registry.labels.values() if lbl == "MATH")
        if math_ct >= 2 and math_ct >= len(inner_registry.labels) * 0.5:
            return True
    # Check 2: sfrac-template equations with parenthesized numeric labels.
    # Walk row-by-row looking for the combination `{{sfrac|…}}` content
    # AND a final `|(N)` or `|(N).` cell.  Any row matching is enough —
    # data tables that happen to contain a sfrac fraction don't also
    # carry equation-number labels.
    if re.search(r"\{\{sfrac\|", inner, re.IGNORECASE):
        for row in re.split(r"\|-[^\n]*", inner):
            has_sfrac = bool(re.search(r"\{\{sfrac\|", row, re.IGNORECASE))
            has_eqn_label = bool(re.search(r"\|\s*\(\d+[a-z]?\)\.?\s*$",
                                           row, re.MULTILINE))
            if has_sfrac and has_eqn_label:
                return True
    # Check 3: spacer-heavy alignment (>50% empty cells).
    # Data tables use cell-level align/valign attributes; equation layout never does.
    if re.search(r'\balign\s*=', inner, re.IGNORECASE):
        return False
    # Need _extract_cells logic inline — lightweight version for detection only
    raw_rows = re.split(r"\|-[^\n]*", inner)
    total_cells = 0
    empty_cells = 0
    for raw_row in raw_rows:
        # Simple cell split (no text_transform needed for counting)
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), raw_row)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)
        raw_cells = re.findall(r"\|([^|\n]*)", protected)
        _ATTR = re.compile(
            r"^(?:colspan|rowspan|width|style|align|valign|class|"
            r"cellpadding|nowrap|border|bgcolor|height)[\s=|]", re.IGNORECASE)
        for c in raw_cells:
            s = c.replace("\x04", "|").strip()
            if s in ("}", "{|") or (s and _ATTR.match(s)):
                continue
            total_cells += 1
            if not s:
                empty_cells += 1
    if total_cells >= 4 and empty_cells > total_cells * 0.5:
        return True
    return False


def _process_equation_layout(inner: str, text_transform) -> str:
    """Process an equation-layout table: join each row's content cells
    into one line, then emit each row as its own paragraph.

    These are wiki tables used for visual alignment of equations, not
    for tabular data.  Table parsing is shared with the other wiki-
    table paths (``parse_wiki_table``); the equation-layout
    specialisation is the post-processing: one line per row, then
    ``\\n\\n``-paragraph wrap so each equation reaches the viewer as
    its own paragraph (otherwise leading/trailing prose glues to the
    first/last equation and kills display-mode rendering —
    METEOROLOGY Margules energy equations).
    """
    _, parsed_rows = parse_wiki_table(inner)
    lines: list[str] = []
    for parsed_row in parsed_rows:
        cells: list[str] = []
        for _sep, _attr, content in parsed_row:
            if not content or content in ("}", "{|"):
                continue
            # Cells whose content is itself a bare attribute keyword
            # (no `|attr|content` separator in source) are malformed —
            # drop rather than render the keyword as prose.
            stripped = re.sub(
                r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", content).strip()
            if not stripped or _CELL_ATTR_RE.match(stripped):
                continue
            cells.append(text_transform(stripped))
        if cells:
            lines.append(" ".join(cells))
    return ("\n\n" + "\n\n".join(lines) + "\n\n") if lines else ""


# ── Unified math-table-layout detector + dispatch ────────────────────────

# Math-content signals inside an HTML <table> child.  When the outer
# wikitable's role is just positioning, the inner HTML table holds the
# real math (poem of equations, rowspan fractions, Greek templates).
_HTML_MATH_SIGNALS = re.compile(
    r"<math|\\frac|\\sum|\\int|\\partial|\\sqrt|"
    r"\{\{Polytonic\||\{\{sfrac\||\{\{brace2\||"
    r"<su[pb]\s*>",
    re.IGNORECASE,
)


# An actual inline-math signal in a cell: sub/sup (HTML tags, EB templates,
# or Unicode super/subscripts) or an arithmetic operator standing before an
# operand.  Used to gate the otherwise content-free "spacer-heavy" math
# fallback so it stops claiming data / list / legend / outline / verse tables.
_INLINE_MATH_SIGNAL = re.compile(
    r"<su[pb]\b"                                  # <sub> / <sup>
    r"|\{\{\s*su[pb]\b"                           # {{sub}} / {{sup}}
    r"|[⁰-ₜ]"                           # Unicode super/subscripts
    r"|[+−=＝×÷±]\s*(?:''|[0-9(]|«I)",  # op+operand
)


def _math_table_kind(
    raw: str, inner: str, inner_registry: ElementRegistry | None
) -> str | None:
    """Classify a wikitable as a math layout, returning the encoding
    or None.

    Encodings (the same shape, three transcription styles):
      - ``"tokens"``     — cells hold raw math tokens.
      - ``"math_blocks"`` — cells hold ``<math>`` placeholders.
      - ``"html_wrapper"`` — wikitable wraps an HTML ``<table>`` whose
                             content is the math (Type C).

    Shared disqualifiers (any of these → not a math layout):
      * ``class=wikitable`` / ``class=tablecolhd`` / ``class=…border``
      * ``border=N≥1`` on the header
      * ``rules=`` styling
      * ``<ref>`` footnotes
    """
    header = raw.split("\n", 1)[0]
    if re.search(r'class\s*=\s*"?[^"\s]*(?:wikitable|tablecolhd|border)',
                 header, re.IGNORECASE):
        return None
    if re.search(r'border\s*=\s*"?[1-9]|rules\s*=',
                 header, re.IGNORECASE):
        return None
    if re.search(r"<ref[\s>]", raw, re.IGNORECASE):
        return None

    # math_blocks: majority MATH placeholders (was _is_equation_layout
    # check 1).
    if _PH in inner and inner_registry:
        math_ct = sum(1 for lbl in inner_registry.labels.values()
                       if lbl == "MATH")
        if math_ct >= 2 and math_ct >= len(inner_registry.labels) * 0.5:
            return "math_blocks"

    # html_wrapper: a single HTML_TABLE child whose raw content carries
    # math signals.  The outer wikitable is just positioning around
    # that HTML table (and an equation-number cell, typically).
    if inner_registry:
        for ph, label in inner_registry.labels.items():
            if label != "HTML_TABLE":
                continue
            eraw = inner_registry.elements[ph][1]
            if _HTML_MATH_SIGNALS.search(eraw):
                return "html_wrapper"

    # tokens: every cell matches the math-token regex, ≥2 cells have
    # strong math signal (was _is_math_layout).
    cells = _parse_math_layout_cells(inner)
    if cells is not None and len(cells) >= 2:
        if (all(len(c) <= 250 for c in cells)
                and all(_MATH_CELL_RE.match(c) for c in cells)):
            strong = sum(
                1 for c in cells
                if re.search(r"<su[pb]>", c)
                or re.search(r"[+\-−=＝×÷]\s*(?:''|[0-9(])", c))
            if strong >= 2:
                return "tokens"

    # Falling-back legacy checks from _is_equation_layout: sfrac+(N)
    # equation-number combo, spacer-heavy alignment.  Kept as part of
    # the unified detector so existing routes don't regress.
    if re.search(r"\{\{sfrac\|", inner, re.IGNORECASE):
        for row in re.split(r"\|-[^\n]*", inner):
            has_sfrac = bool(re.search(
                r"\{\{sfrac\|", row, re.IGNORECASE))
            has_eqn_label = bool(re.search(
                r"\|\s*\(\d+[a-z]?\)\.?\s*$", row, re.MULTILINE))
            if has_sfrac and has_eqn_label:
                return "math_blocks"
    # Spacer-heavy alignment layout: many empty cells used to align an
    # equation across columns.  GATED on an actual inline-math signal —
    # the empty-cell ratio alone is content-FREE and mis-claimed 28
    # data/list/legend/outline/taxonomy/verse tables (debt tables, name
    # lists, SKULL's anatomy legend, REVELATION's outline, the WRIT poem,
    # …) as math.  Signal-bearing math layouts are already caught by the
    # MATH-child / tokens / sfrac paths above; this fallback only ever
    # needs to add the spacer-heavy ones that ALSO carry inline math
    # markup, so requiring the signal drops exactly the over-claims.
    if (not re.search(r"\balign\s*=", inner, re.IGNORECASE)
            and _INLINE_MATH_SIGNAL.search(inner)):
        raw_rows = re.split(r"\|-[^\n]*", inner)
        total_cells = 0
        empty_cells = 0
        for raw_row in raw_rows:
            protected = re.sub(
                r"\{\{[^}]*\}\}",
                lambda m: m.group(0).replace("|", "\x04"), raw_row)
            protected = re.sub(
                re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                lambda m: m.group(0).replace("|", "\x04"), protected)
            for c in re.findall(r"\|([^|\n]*)", protected):
                s = c.replace("\x04", "|").strip()
                if s in ("}", "{|"):
                    continue
                if s and re.match(
                    r"^(?:colspan|rowspan|width|style|align|valign|"
                    r"class|cellpadding|nowrap|border|bgcolor|height)"
                    r"[\s=|]", s, re.IGNORECASE):
                    continue
                total_cells += 1
                if not s:
                    empty_cells += 1
        if total_cells >= 4 and empty_cells > total_cells * 0.5:
            return "math_blocks"

    return None


def _process_math_table_layout(
    raw: str, inner: str, inner_registry: ElementRegistry | None,
    text_transform,
) -> str:
    """Render a math-layout wikitable.

    Dispatches on encoding:

    * ``tokens``     → KaTeX ``\\begin{aligned}`` / ``\\begin{vmatrix}``
                       via :func:`_process_math_layout_table`.
    * ``math_blocks`` → row-per-paragraph emission via
                        :func:`_process_equation_layout` — the math
                        placeholders in each cell get substituted by
                        the parent.
    * ``html_wrapper`` → identical to ``math_blocks`` — the cell-per-
                         paragraph emission lets the inner HTML_TABLE
                         placeholder substitute through to the viewer
                         as-is, with the equation-number cell emitted
                         as an adjacent paragraph.
    """
    kind = _math_table_kind(raw, inner, inner_registry)
    if kind == "tokens":
        return _process_math_layout_table(raw)
    if kind in ("math_blocks", "html_wrapper"):
        return _process_equation_layout(inner, text_transform)
    return ""  # unreachable when dispatched from _classify_table
