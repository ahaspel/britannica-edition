"""Math / equation layout detection and rendering.

Wiki tables that are spatial math layouts (equation systems,
determinants, matrices) rather than tabular data.  Detection and
rendering live here; classification dispatch is in __init__.

Public entry points:
- ``_is_math_layout`` / ``_is_math_dominant_layout`` / ``_is_equation_layout``
  — predicates consumed by ``_classify_table``
- ``_process_math_layout_table`` / ``_process_equation_layout``
  — renderers dispatched from ``_process_element``
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.elements._registry import ElementRegistry, _PH


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

    Equation system (rows share ``=`` column): ``\\begin{aligned}…\\end{aligned}``.
    Otherwise (matrix/determinant): ``\\begin{vmatrix}…\\end{vmatrix}``.
    """
    inner = re.sub(r"^\{\|[^\n]*\n?", "", raw)
    inner = re.sub(r"\n?\|\}\s*$", "", inner)
    raw_rows = re.split(r"^\|-[^\n]*$", inner, flags=re.MULTILINE)
    rows: list[list[str]] = []
    for raw_row in raw_rows:
        row_cells: list[str] = []
        for line in raw_row.split("\n"):
            s = line.strip()
            if not s or s.startswith("|+") or s == "|}":
                continue
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
                if content:
                    row_cells.append(_math_cell_to_latex(content))
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
        math_ct = sum(1 for _, (t, _) in inner_registry.elements.items() if t == "MATH")
        if math_ct >= 2 and math_ct >= len(inner_registry.elements) * 0.5:
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
    """Process an equation-layout table: join each row's content cells into one line.

    These are wiki tables used for visual alignment of equations,
    not for tabular data.  Each row becomes a single text line.
    """
    inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]", re.IGNORECASE)

    def _extract_cells(row_text):
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), row_text)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)
        raw_cells = re.findall(r"\|([^|\n]*)", protected)
        raw_cells = [c.replace("\x04", "|") for c in raw_cells]
        cells = []
        for c in raw_cells:
            s = c.strip()
            if s in ("}", "{|"):
                continue
            # Strip cell-styling templates before the attribute test so
            # cells like `{{Ts|ac}} colspan=2` are recognized as
            # attribute-only rather than rendered with `colspan=2`
            # surviving into prose output.
            test = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", s).strip()
            if not test or _ATTR.match(test):
                continue
            cells.append(text_transform(s) if s else " ")
        return cells

    raw_rows = re.split(r"\|-[^\n]*", inner)
    lines = []
    for raw_row in raw_rows:
        cells = _extract_cells(raw_row)
        content = [c for c in cells if c.strip()]
        if content:
            lines.append(" ".join(content))
    # Wrap with paragraph boundaries so each row reaches the viewer as
    # its own paragraph — otherwise leading/trailing prose in the
    # surrounding sentence glues to the first/last equation and kills
    # display-mode rendering (METEOROLOGY Margules energy equations).
    return ("\n\n" + "\n\n".join(lines) + "\n\n") if lines else ""
