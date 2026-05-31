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
    # Full `[[File:…|params]]` specs — filename PLUS its width/align/float
    # params, carried (not tossed) so the partition stays complete and the
    # assembler can use what the viewer renders.  See
    # [[feedback_capture_now_decide_later]].
    images: list[str] = field(default_factory=list)
    caption_parts: list[str] = field(default_factory=list)
    attribution_parts: list[str] = field(default_factory=list)
    legend_lines: list[str] = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)     # raw <ref>…


@dataclass
class Element:
    """One structurally-atomic piece of a figure cell, in the walk's ordered
    bag.  `kind` is the STRUCTURAL type — IMAGE / NESTED_TABLE / POEM / REF /
    TEXT — NOT a role.  `content` is the raw bytes; `attrs` carries the cell /
    layout attributes (cell `sep`, attribute slot, alignment) the role-
    classifier reads to decide WHERE the element belongs (CHESS: align-left
    legend vs align-right image).  The walk emits these; the role-classifier
    (`_classify_element`) assigns each to a FigureComponents part.  Step toward
    the recursive ICL producer: walk → classify(role) → produce(part) →
    compose — the same skeleton the table producer will reuse."""
    kind: str
    content: str
    attrs: dict = field(default_factory=dict)


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


# Poem mask token — `\x03`-delimited so the wiki row/cell splitters treat it
# as opaque content (carries no `|`/`!`/newline).  The `PM` infix keeps it
# distinct from `_table_decompose`'s `NT` nested-table tokens.  Same plumbing
# as `_mask_nested_tables`: protect a structural sub-unit from the cell
# splitter's newline collapse so the leaf delegate (`_emit_legend_chunk`)
# receives the poem with its line structure intact (each line = one entry).
_POEM_SENTINEL = "\x03"
_POEM_RE = re.compile(r"<poem>[\s\S]*?</poem>", re.IGNORECASE)


def _poem_token(i: int) -> str:
    return f"{_POEM_SENTINEL}PM{i}{_POEM_SENTINEL}"


def _mask_poems(text: str) -> tuple[str, list[str]]:
    """Replace each ``<poem>…</poem>`` with an opaque token, returning
    ``(masked, raw_spans)``.  No-op when there is no poem."""
    spans = list(_POEM_RE.finditer(text))
    if not spans:
        return text, []
    raw: list[str] = []
    out: list[str] = []
    last = 0
    for m in spans:
        out.append(text[last:m.start()])
        out.append(_poem_token(len(raw)))
        raw.append(m.group(0))
        last = m.end()
    out.append(text[last:])
    return "".join(out), raw


def _restore_poems(text: str, raw: list[str]) -> str:
    for i, span in enumerate(raw):
        text = text.replace(_poem_token(i), span)
    return text


def extract_figure_components(
    raw: str, text_transform: TextTransform,
) -> FigureComponents:
    """Extract a figure's components from its RAW bytes, recursing into
    nested figure-tables to gather (not finalize) their components."""
    comps = FigureComponents()
    _gather(_peel_table(raw), comps, text_transform)
    return comps


def _gather(inner: str, comps: FigureComponents, tt: TextTransform) -> None:
    from britannica.pipeline.stages.elements._tables import (
        _HTML_TABLE_TAG_RE, _html_table_grid,
    )
    # HTML `<table>` figure flavor.  `_html_table_grid` gives rows×cell-content
    # robustly (EB1911 routinely omits `</td>`/`</tr>`) and preserves cell
    # newlines, so poem legends survive with no masking.  HTML figures carry no
    # `||` multicol, so the wiki Phase-1 column-major pass doesn't apply —
    # every cell goes straight to the shared `_gather_cell`.  Same flavor
    # primitive (`_table_grid`) and cell-path production uses for `<table>`
    # figures (`_process_legended_figure_child` Phase 2).  One recursion, two
    # row-extractors: flavor is a leaf detail, everything downstream is shared.
    if _HTML_TABLE_TAG_RE.search(inner):
        for cells in _html_table_grid(inner):
            for sep, attr, content in cells:
                _gather_cell(content, {**_normalize_attrs(attr), "sep": sep},
                             comps, tt)
        return

    # ── wiki `{|` flavor ────────────────────────────────────────────────
    from britannica.pipeline.stages.elements._layout import (
        _chop_legend_entries, _collect_rowspan_legend,
        _parse_multicol_legend_rows_column_major,
        _row_has_legend_multicol_cells, _row_is_single_full_entry,
    )
    from britannica.pipeline.stages.elements._table_decompose import (
        _mask_nested_tables, _restore_nested, extract_wiki_rows,
    )
    from britannica.pipeline.stages.elements._tables import split_wiki_row

    # Mask the two sub-units that a raw `|-` split / cell split would damage:
    # nested ``{|…|}`` tables (their own `|-` rows would fragment) and
    # ``<poem>`` blocks (their entry-per-line structure would collapse).
    # Production never hits this — both are registry placeholders by the time
    # its legend code runs — so masking restores the same clean rows.  Poems
    # are masked AFTER nested tables, so a poem inside a nested table travels
    # with its (masked) table and is restored when the table is.
    masked, nested = _mask_nested_tables(inner)
    masked, poems = _mask_poems(masked)

    # ── Phase 1: multicol legend block ──────────────────────────────────
    # A multicol legend's entries run ACROSS rows (down each column), so the
    # whole block parses together — delegate to production's COMPLETE multicol
    # logic (rowspan / column-major-with-continuation / alternating-pair, all
    # in column-major reading order, NO alphabetical sort).  Delegating the
    # whole parser — not a per-row fragment — is what joins down-column
    # continuations (no truncation) and preserves reading order.  Block
    # detection mirrors `_process_legended_figure_child`.
    raw_rows = [r for r in re.split(r"\|-[^\n]*", masked) if r.strip()]
    multicol_rows: list[str] = []
    other_rows: list[str] = []
    in_block = False
    for row in raw_rows:
        if _row_has_legend_multicol_cells(
                [c for _s, _a, c in split_wiki_row(row)]):
            multicol_rows.append(row)
            in_block = True
        elif in_block and ("||" in row or _row_is_single_full_entry(row)):
            multicol_rows.append(row)
        else:
            in_block = False
            other_rows.append(row)
    if multicol_rows:
        if any(re.search(r"rowspan", r, re.IGNORECASE)
               for r in multicol_rows):
            col_pairs = _collect_rowspan_legend(multicol_rows, tt)
        else:
            col_pairs = _parse_multicol_legend_rows_column_major(
                multicol_rows, tt)
        if col_pairs:
            comps.legend_lines.extend(
                f"{lbl}. {text}" for lbl, text in col_pairs)
        else:
            pairs_per_row = [
                _chop_legend_entries(r, "||", tt) for r in multicol_rows]
            max_cols = max((len(p) for p in pairs_per_row), default=0)
            for col in range(max_cols):
                for row_pairs in pairs_per_row:
                    if col < len(row_pairs):
                        lbl, text = row_pairs[col]
                        comps.legend_lines.append(f"{lbl}. {text}")

    # ── Phase 2: every other row via the cell-based gather ──────────────
    # Image, caption, attribution, loose poems, nested-table legends, prose
    # legends.  Re-join the non-multicol rows and decompose to cells; restore
    # the masked sub-units (nested tables first, then loose poems) so each
    # cell reaches `_gather_cell` in raw form.
    _caption, rows = extract_wiki_rows("\n|-\n".join(other_rows))
    for _row_attrs, cells in rows:
        for _sep, _attr, content in cells:
            content = _restore_poems(_restore_nested(content, nested), poems)
            _gather_cell(content, {**_normalize_attrs(_attr), "sep": _sep},
                         comps, tt)


_CSC_LINE_RE = re.compile(r"^\s*\{\{\s*csc\s*\|([^{}]*)\}\}\s*$", re.IGNORECASE)
# Split a flowed legend line at a sentence/clause boundary that PRECEDES a
# label token — recovers per-entry structure when the cell splitter collapsed
# the source newlines to spaces (mirrors `_parse_prose_legend_rows`'s chunker,
# plus `;` for the `a. Hydranth; b. Hydrocaulus;` shape).
_ENTRY_BOUNDARY_RE = re.compile(
    r"(?<=[.;])\s+(?=(?:«I»)?(?:[IVX]+|[A-Za-z0-9][A-Za-z0-9.]{0,4})\s*[.,]\s)")


def _parse_legend_lines(content: str, tt: TextTransform) -> tuple[list[str], int]:
    """Ground-up linear-legend recursion: parse a legend's source into
    per-entry lines IN READING ORDER, unifying `<poem>` / `<br/>` / newline /
    collapsed-prose entries.  `<poem>`/`<br/>`/newline are uniform line
    boundaries; each line is further split at period/`;`-before-label
    boundaries (for cell-collapsed prose).  A unit whose head matches the
    legend label grammar (plain or italic) starts a new entry; `{{csc|…}}` is
    a sub-heading; a unit with NO label is a CONTINUATION of the previous
    entry — appended, NEVER dropped (the no-drop floor the production parsers
    lack: `_emit_legend_chunk` / `_parse_prose_legend_rows` silently discard
    label-less continuation lines, which is the partial-loss bug).  Returns
    `(lines, n_labelled)` so the caller can gate caption-vs-legend.  Owns the
    line structure; reuses the leaf label GRAMMAR."""
    from britannica.pipeline.stages.elements._layout import (
        _MULTICOL_FULL_ENTRY_ITALIC_RE, _MULTICOL_FULL_ENTRY_RE,
        _clean_legend_text,
    )
    text = re.sub(r"</?poem>", "\n", content, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    units: list[str] = []
    for seg in text.split("\n"):
        seg = seg.strip()
        if seg:
            units.extend(p for p in _ENTRY_BOUNDARY_RE.split(seg) if p.strip())

    out: list[str] = []
    n_labelled = 0
    for unit in units:
        unit = unit.strip()
        m_csc = _CSC_LINE_RE.match(unit)
        if m_csc:
            sub = _clean_legend_text(m_csc.group(1)).rstrip(". ")
            if sub:
                out.append(f"### {sub}.")
            continue
        label = txt = None
        if unit.startswith("«I»"):
            m = _MULTICOL_FULL_ENTRY_ITALIC_RE.match(unit)
            if m:
                label, txt = m.group(1).strip(), _clean_legend_text(tt(m.group(2)))
        else:
            cleaned = _clean_legend_text(tt(unit))
            m = _MULTICOL_FULL_ENTRY_RE.match(cleaned)
            if m:
                label, txt = m.group(1).strip(), m.group(2).strip()
        if label is not None:
            out.append(f"{label}. {txt}".rstrip())
            n_labelled += 1
            continue
        # No label → CONTINUATION of the previous entry (no-drop floor).
        cont = _clean_legend_text(tt(unit)).strip()
        if not cont:
            continue
        if out and not out[-1].startswith("###"):
            out[-1] = f"{out[-1]} {cont}".rstrip()
        else:
            out.append(cont)  # orphan leading line — keep, never drop
    return out, n_labelled


def _normalize_attrs(attr_part: str) -> dict:
    """Normalize a cell's raw attribute string into the uniform layout signals
    the role-classifier reads — ``{align, valign, width, float}``.  Reuses
    production's ``_cell_styles`` (which already parses HTML ``align=``/
    ``valign=``, inline ``style=``, and ``{{Ts|…}}`` codes into CSS
    declarations); we just lift out the four properties.  Flavor-blind: same
    result whether the attrs came from a wiki ``_attr`` slot or an HTML
    ``<td …>`` opener, so the classifier never sees which syntax produced it."""
    if not attr_part:
        return {}
    from britannica.pipeline.stages.elements._tables import _cell_styles
    out: dict = {}
    for decl in _cell_styles(attr_part, ""):
        prop, _, val = decl.partition(":")
        prop, val = prop.strip().lower(), val.strip().lower()
        if prop == "text-align" and val in ("left", "right", "center"):
            out["align"] = val
        elif prop == "vertical-align" and val in ("top", "middle", "bottom"):
            out["valign"] = val
        elif prop == "width":
            out["width"] = val
        elif prop == "float" and val in ("left", "right"):
            out["float"] = val
    # colspan/rowspan are HTML grid attrs (not CSS), so `_cell_styles`
    # doesn't surface them — lift directly.  Additive: the role-classifier
    # reads align/valign/width/float; cell producers carry the span.
    cs = re.search(r"colspan\s*=\s*[\"']?(\d+)", attr_part, re.I)
    if cs:
        out["colspan"] = cs.group(1)
    rs = re.search(r"rowspan\s*=\s*[\"']?(\d+)", attr_part, re.I)
    if rs:
        out["rowspan"] = rs.group(1)
    return out


def _walk_cell(content: str, attrs: dict) -> list[Element]:
    """The WALK: decompose ONE cell's raw bytes into an ordered bag of
    structural Elements IN SOURCE SEQUENCE.  NO role decisions, NO grouping by
    type — the walker's only job is to hand back what's there, in order; what
    each element *is* belongs to the role-classifier.  Nested tables and poems
    are masked to opaque tokens first, so the wrapper-unwrap and the scan treat
    them as single atomic units (and their inner refs/images aren't separately
    extracted), while their source position is preserved.  Then we scan left to
    right, emitting text gaps and structural spans in the order they appear."""
    from britannica.pipeline.stages.elements._table_decompose import (
        _mask_nested_tables, _restore_nested,
    )
    from britannica.pipeline.stages.elements._layout import (
        _unwrap_cell_wrappers,
    )
    content = content.strip()
    if not content:
        return []
    # Mask nested tables (their `|-` rows) and poems (their entry lines) so the
    # unwrap and the scan see them as atomic, keeping their source position.
    masked, nt_raws = _mask_nested_tables(content)
    masked, poem_raws = _mask_poems(masked)
    masked = _unwrap_cell_wrappers(masked).strip()
    if not masked:
        return []

    # Collect structural spans (positions in the masked text), then walk them
    # in source order.  Refs/images inside a masked table/poem aren't found
    # here — they travel with their (atomic) container, as they should.
    spans: list[tuple[int, int, str, str]] = []
    for m in re.finditer(r"\x03NT\d+\x03", masked):
        spans.append((m.start(), m.end(), "NESTED_TABLE",
                      _restore_nested(m.group(0), nt_raws)))
    for m in re.finditer(r"\x03PM\d+\x03", masked):
        spans.append((m.start(), m.end(), "POEM",
                      _restore_poems(m.group(0), poem_raws)))
    for m in _REF_RE.finditer(masked):
        spans.append((m.start(), m.end(), "REF", m.group(0)))
    for m in _IMAGE_NS_LINK_RE.finditer(masked):
        spans.append((m.start(), m.end(), "IMAGE", m.group(0)))
    spans.sort()

    bag: list[Element] = []
    pos = 0
    for start, end, kind, raw in spans:
        _emit_text(masked[pos:start], attrs, bag)
        bag.append(Element(kind, raw, dict(attrs)))
        pos = end
    _emit_text(masked[pos:], attrs, bag)
    return bag


def _emit_text(gap: str, attrs: dict, bag: list[Element]) -> None:
    """Emit a residual-text gap as a TEXT element iff it carries real text.
    Carries the raw (`<br/>` intact — an entry boundary for a legend ladder)
    plus a `flat` copy (`<br/>`→space) for caption/attribution typing; the cell
    attrs ride along for the role-classifier to read (CHESS)."""
    gap = gap.strip()
    if not gap:
        return
    flat = re.sub(r"<br\s*/?>", " ", gap, flags=re.IGNORECASE).strip()
    if _has_text(flat):
        bag.append(Element("TEXT", gap, {**attrs, "flat": flat}))


def _classify_element(el: Element, comps: FigureComponents,
                      tt: TextTransform) -> None:
    """The role-CLASSIFY (+ recurse/produce): assign ONE structural element to
    its figure part.  The named home for what was `_gather_cell`'s inline
    if/elif typing — including the `else → caption` catch-all the role-
    classifier will dissolve.  ICL is a FLAT bag: a nested figure-table is
    GATHERED (flattened) into this figure's parts, never kept as a hierarchy
    (that disposition is the table producer's, not ours)."""
    if el.kind == "NESTED_TABLE":
        if _IMAGE_NS_LINK_RE.search(el.content):
            _gather(_peel_table(el.content), comps, tt)     # sub-figure → gather
        else:
            _gather_legend_table(el.content, comps, tt)     # no image → legend
    elif el.kind == "POEM":
        from britannica.pipeline.stages.elements._layout import (
            _CAPTION_POEM_RE, _emit_legend_chunk,
        )
        from britannica.pipeline.stages.elements._text import _clean_text
        body = re.sub(r"</?poem>", "", el.content, flags=re.IGNORECASE).strip()
        if _CAPTION_POEM_RE.match(body):                    # caption-poem
            cap = _clean_text(tt(re.sub(r"\s*\n\s*", " ", body)))
            if cap:
                comps.caption_parts.append(cap)
        else:                                                # legend-poem
            _emit_legend_chunk(el.content, tt, comps.legend_lines)
    elif el.kind == "REF":
        comps.footnotes.append(el.content)
    elif el.kind == "IMAGE":
        comps.images.append(el.content)
    elif el.kind == "TEXT":
        _classify_text(el, comps, tt)


def _classify_text(el: Element, comps: FigureComponents,
                   tt: TextTransform) -> None:
    """Type a residual-text element: caption (Fig./Plate. marker) / attribution
    (credit phrasing) / legend (≥3-entry label ladder) / caption — the last is
    the no-drop default, i.e. the catch-all the role-classifier is meant to
    dissolve once it can read the carried attributes."""
    from britannica.pipeline.stages.elements._layout import (
        _entries_look_like_legend,
    )
    flat = el.attrs["flat"]
    if _FIG_MARKER_RE.search(flat):
        marker = _FIG_MARKER_RE.search(flat)
        before = flat[:marker.start()].strip()
        after = flat[marker.start():].strip()
        if before and _ATTRIBUTION_RE.match(before):
            comps.attribution_parts.append(_clean(tt(before)))
        elif before:
            comps.caption_parts.append(_clean(tt(before)))
        if after:
            comps.caption_parts.append(_clean(tt(after)))
        return
    if _ATTRIBUTION_RE.match(flat):
        comps.attribution_parts.append(_clean(tt(flat)))
        return
    leg_lines, n_lab = _parse_legend_lines(el.content, tt)
    entries = [tuple(ln.split(". ", 1)) for ln in leg_lines
               if not ln.startswith("###")]
    if (n_lab >= 3
            and _entries_look_like_legend([e for e in entries if len(e) == 2])):
        comps.legend_lines.extend(leg_lines)
    else:
        comps.caption_parts.append(_clean(tt(flat)))


def _gather_cell(content: str, attrs: dict, comps: FigureComponents,
                 tt: TextTransform) -> None:
    """Walk one cell into its element bag, then classify each element to its
    part — the producer's walk → classify shape at cell scope."""
    for el in _walk_cell(content, attrs):
        _classify_element(el, comps, tt)


def _gather_legend_table(table_raw: str, comps: FigureComponents,
                         tt: TextTransform) -> None:
    """A no-image nested table inside a figure is a LEGEND.  Recurse ALL
    the way down: each cell's source — interleaved `{{csc|…}}` sub-headings
    and `<poem>` entry-blocks — is parsed into per-entry legend lines +
    `### Subhead.` lines by the shared `_emit_legend_chunk` (the same
    descent production uses; its label parser handles caps / multi-char /
    subscript / italic labels).  A cell with no csc/poem falls back to its
    cleaned text as one legend line (no-drop)."""
    from britannica.pipeline.stages.elements._layout import _emit_legend_chunk
    inner = _peel_table(table_raw)
    # Feed the WHOLE inner — `_emit_legend_chunk` scans for `{{csc}}` /
    # `<poem>` itself with newlines intact, so the poem entries split per
    # line.  (Running the table cell-splitter first would merge the poem's
    # continuation lines and re-flatten it.)
    before = len(comps.legend_lines)
    _emit_legend_chunk(inner, tt, comps.legend_lines)
    if len(comps.legend_lines) > before:
        return
    # Fallback: no csc/poem in the table — gather each row's cell text as a
    # legend line (no-drop) via the cell splitter.
    from britannica.pipeline.stages.elements._table_decompose import (
        extract_wiki_rows,
    )
    _caption, rows = extract_wiki_rows(inner)
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


# ---------------------------------------------------------------------------
# Faithful figure producer (additive / inert) — the walk→translate model.
#
# Walk the figure into ordered structural Elements (no role judgment), then
# TRANSLATE each into the viewer's EXISTING marker vocabulary, in source order:
#   image          → {{IMG:..}}  (width / align / height carried; NO bundled
#                     caption — the caption is its own ordered element)
#   text           → its own style: centring → «CTR», italic / small-caps via
#                     `tt`, `<br>` / poem newlines preserved as `<br>`
#   nested legend  → «HTMLTABLE:<table>..</table>«/HTMLTABLE»; each source cell's
#     table          width / valign carried as <td style> (the viewer renders
#                     the table natively).
#
# No classification, no relocation — the producer's one job is translation into
# something the viewer reads ([[feedback_producer_regularizes_markup]]).  The
# render's remaining gaps are step-2 viewer-recognition work: a borderless
# layout-table lane (sibling of «CHEM:») and dropping the IMG figure-box /
# LEGEND-aside opinions.
# ---------------------------------------------------------------------------

_CENTER_FIGURE_RE = re.compile(r"^\s*\{\{\s*c(?:enter)?\b", re.IGNORECASE)


def _figure_bag(raw: str) -> list[Element]:
    """Walk a figure's RAW bytes into ordered structural Elements — the bag the
    faithful producer translates.  Same dispatch as `_gather` minus the role
    classification: HTML → `_html_table_grid`; wiki → nested/poem mask +
    `extract_wiki_rows` → `_walk_cell`; loose (no table) → `_walk_cell`."""
    from ._table_decompose import (extract_wiki_rows, _mask_nested_tables,
                                   _restore_nested)
    from ._tables import _HTML_TABLE_TAG_RE, _html_table_grid

    inner = _peel_table(raw)
    bag: list[Element] = []
    if _HTML_TABLE_TAG_RE.search(inner):
        for row in _html_table_grid(inner):
            for sep, attr, content in row:
                bag.extend(_walk_cell(content,
                                      {**_normalize_attrs(attr), "sep": sep}))
        return bag
    masked, nested = _mask_nested_tables(inner)
    masked, poems = _mask_poems(masked)
    _caption, rows = extract_wiki_rows(masked)
    if not rows:
        return _walk_cell(
            _restore_poems(_restore_nested(masked, nested), poems), {})
    for _rattr, cells in rows:
        for sep, attr, content in cells:
            content = _restore_poems(_restore_nested(content, nested), poems)
            bag.extend(_walk_cell(content,
                                  {**_normalize_attrs(attr), "sep": sep}))
    return bag


def _faithful_image(content: str, tt: TextTransform) -> str:
    """`[[File:..]]` → `{{IMG:..}}` via the shared image producer — width / align
    / height translated from the link params; NO bundled caption."""
    from ._layout import _process_image
    inner = re.sub(r"\]\]\s*$", "",
                   re.sub(r"^\s*\[\[(?:File|Image):", "", content,
                          flags=re.IGNORECASE))
    return _process_image(inner, tt)


def _faithful_lines(text: str, tt: TextTransform) -> str:
    """Translate a text element's inline markup (`tt`) while preserving its line
    structure — poem / `<br>` / source newlines all become `<br>`."""
    text = re.sub(r"</?poem>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return "<br>".join(tt(line).strip()
                       for line in text.split("\n") if line.strip())


def _faithful_legend_table(content: str, tt: TextTransform) -> str:
    """Nested legend table → «HTMLTABLE:» raw <table>; each <td> carries the
    source cell's width / valign as inline style, and the cell's lines are kept
    via `_faithful_lines`.  The viewer renders it natively (gridded today; the
    borderless layout-table lane is step-2 work)."""
    from ._table_decompose import extract_wiki_rows
    _cap, rows = extract_wiki_rows(_peel_table(content))
    out_rows: list[str] = []
    for _rattr, cells in rows:
        tds: list[str] = []
        for _sep, attr, cell in cells:
            na = _normalize_attrs(attr)
            style = ""
            if na.get("width"):
                style += f"width:{na['width']};"
            if na.get("valign"):
                style += f"vertical-align:{na['valign']};"
            tds.append(f'<td style="{style}">{_faithful_lines(cell, tt)}</td>')
        if tds:
            out_rows.append("<tr>" + "".join(tds) + "</tr>")
    return f"«HTMLTABLE:<table>{''.join(out_rows)}</table>«/HTMLTABLE»"


def _produce_figure_faithful(raw: str, tt: TextTransform) -> str:
    """Translate a figure's RAW bytes into faithful ordered markers (see the
    module note above).  Additive / inert — exercised by the render prototype,
    not yet wired into any producer."""
    centered = bool(_CENTER_FIGURE_RE.match(raw))
    parts: list[str] = []
    for el in _figure_bag(raw):
        if el.kind == "NESTED_TABLE":
            parts.append(_faithful_legend_table(el.content, tt))
            continue
        if el.kind == "IMAGE":
            mk = _faithful_image(el.content, tt)
        else:
            mk = _faithful_lines(el.content, tt)
        if not mk:
            continue
        parts.append(f"«CTR»{mk}«/CTR»" if centered else mk)
    return "\n\n".join(parts)
