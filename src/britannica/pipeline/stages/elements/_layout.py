"""Image-layout / caption / legend / attribution table helpers.

A "layout" wiki table holds a figure (one or more images) with caption,
legend entries (KEY. description), and source attribution, rather than
tabular data.  The classifier flags these as ``LAYOUT_WRAPPER`` and
``_unwrap_layout_table`` rewrites them into ``{{IMG:…}}`` markers + a
``{{LEGEND:…}LEGEND}`` block.

Public dispatch points consumed elsewhere:
- ``_is_layout_wrapper`` — used by ``_classify_table`` to detect this kind.
- ``_unwrap_layout_table`` — used by ``_process_element`` to render it.

Everything else here is internal helper logic for the legend / caption /
attribution parsers.
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.elements._registry import (
    ElementRegistry,
    TABLE_LABELS,
    _PH,
)
from britannica.pipeline.stages.elements._image import (
    build_img_marker,
    _process_image,
)
from britannica.pipeline.stages.elements._tables import split_wiki_row
from britannica.pipeline.stages.elements._text import _clean_text
from britannica.markers import IMG_PARTS_RE, parse_img_meta

def _is_layout_wrapper(raw: str, inner: str, inner_registry: ElementRegistry | None) -> bool:
    """Detect tables that wrap other tables/images for layout purposes.

    These are outer tables used to arrange images, captions, and nested
    tables (e.g. Greek transliterations) visually.  They should be
    unwrapped to sequential content, not rendered as data tables.

    Detected when a table contains:
      - A nested TABLE child, or
      - An IMAGE child with mostly non-data content (captions, short text)

    Tables with explicit border or rules attributes in the {| header are
    never layout wrappers — they are definitively data tables.
    """
    if not inner_registry:
        return False
    # Data table signals in the header override layout wrapper detection.
    header = raw.split("\n", 1)[0]
    if re.search(r'border\s*=\s*"?[1-9]', header, re.IGNORECASE):
        return False
    if re.search(r'rules\s*=', header, re.IGNORECASE):
        return False
    if re.search(r'class\s*=\s*"[^"]*(?:wikitable|tablecolhd|border)', header, re.IGNORECASE):
        return False
    child_types = {t for t, _ in inner_registry.elements.values()}
    # Verse-only layout: <table {{Ts|ma|sm92|lh12}}><tr><td><poem>…
    # </poem></td></tr></table>.  Editors used these purely to centre
    # / resize embedded verse; the table carries no tabular meaning.
    # DONNE's "Sweetest Love, I do not go" passage is the canonical
    # case.  Unwrap to just the <poem> content (VERSE marker).
    if child_types == {"POEM"}:
        return True
    if "TABLE" in child_types:
        # A nested TABLE usually means layout (outer is a shell around
        # the sub-table).  Exception: if the outer declares a wikitext
        # table caption via ``|+`` at the top of the table body, it's
        # a genuine data table.  ``|+`` is the MediaWiki table-caption
        # sigil — only data tables carry it.  This catches AFRICA's
        # "BANTU NEGROIDS" table (40 rows of tribe names, plus one
        # incidental nested bracket-grouping table) without relying on
        # content-length heuristics.
        if re.search(r"^\|\+", inner, re.MULTILINE):
            return False
        # Another data-table signal: MULTIPLE rows with `||` cell
        # separators AND substantive content before the separator AND
        # no nested image. Such tables are genuine data tables whose
        # nested TABLE is just a caption/header sub-block (INDIA
        # Vernaculars-of-India language table). Tables that contain an
        # image plus `||` are figure-legend layouts (ABBEY Fig. 1,
        # etc.) and stay as layout wrappers; a single spacer row like
        # `| &emsp; ||` in a plate-grid (VAULT Plate I) does not count.
        if "IMAGE" not in child_types:
            # Count rows shaped like a real data row: `| LEFT || RIGHT`
            # where BOTH sides have substantive alphanumeric content.
            # Plate-layout attribution rows (`| &nbsp;''Photo, …'' ||`)
            # have trailing `||` with an empty second cell — those
            # don't count. The INDIA language table has many rows like
            # `|Malay Group (7831)|| 2` where both sides ARE
            # substantive.
            data_rows = 0

            def _substantive(s: str) -> bool:
                stripped = re.sub(r"&[a-zA-Z]+;|&#\d+;", "", s)
                return bool(re.search(r"[A-Za-z0-9]", stripped))

            for m in re.finditer(
                r"^\|(?!-|\}|\+)([^|\n]*)\|\|([^|\n]*)(?:\||$)",
                inner, re.MULTILINE,
            ):
                if _substantive(m.group(1)) and _substantive(m.group(2)):
                    data_rows += 1
            if data_rows >= 2:
                return False
        return True
    if "IMAGE" in child_types:
        # Strong signal: table contains a `Fig. N.—` / `Plate N.—`
        # caption line.  HYDROMEDUSAE Fig. 30 has ~800 chars of legend
        # text that would fail the length heuristic below, but it IS a
        # figure layout — the Fig.-caption pattern makes that
        # unambiguous and overrides the length check.
        if re.search(r"\{\{\s*sc\s*\|\s*(?:Fig|Plate)s?\.?|"
                     r"(?<![A-Za-z])(?:Fig|Plate)s?\.?\s*\d",
                     inner, re.IGNORECASE):
            return True
        # Check if non-image content is just captions (short text, no data)
        non_ph = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH), "", inner)
        non_ph = re.sub(r"[-|{}\n]", " ", non_ph)
        non_ph = re.sub(r"\b(?:align|valign|colspan|rowspan|style|width|cellpadding|cellspacing|center|right|left|top|bottom)\b", "", non_ph, flags=re.IGNORECASE)
        non_ph = re.sub(r'[="]+', "", non_ph)
        non_ph = re.sub(r"\s+", " ", non_ph).strip()
        # If remaining text is short relative to number of images, it's a layout table
        n_images = sum(1 for label in inner_registry.labels.values() if label == "IMAGE")
        if len(non_ph) < n_images * 300:
            return True
    return False


def _clean_legend_text(text: str) -> str:
    """Clean a legend entry (letter or text).  Strips layout templates,
    entity refs, and inline markers.  Runs after text_transform."""
    text = text.replace("&thinsp;", " ").replace("&ensp;", " ")
    text = text.replace("&emsp;", " ").replace("&nbsp;", " ")
    text = re.sub(r"\{\{\s*(?:em|gap|dhr|vr|hr|thinsp)\s*(?:\|[^{}]*)?\}\}",
                  " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Unwrap any layout/style templates that snuck through, keep arg
    for _ in range(3):
        text = re.sub(r"\{\{\s*(?:sc|smaller|c|center|small|csc|b|i)\s*\|"
                      r"([^{}]*)\}\}",
                      r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _format_legend_entries(entries: list[tuple[str, str]],
                            sort_alphabetic: bool = False) -> str:
    """Render (label, text) pairs as one entry per line: `L. text`.

    When `sort_alphabetic` is True, entries are sorted by their label
    in reading order (A, B, C…) — used for MULTICOL layouts where the
    source row-major order is a visual grid, not the reading order."""
    if sort_alphabetic:
        def _key(e):
            lbl = e[0]
            # Pad any embedded integer runs so `2` sorts before `10`.
            # Uppercase variants sort before lowercase ones
            # (A-T first, then a-t for "Menial Department" style).
            case_rank = 0 if lbl[:1].isupper() else 1
            padded = re.sub(r"\d+", lambda m: m.group(0).zfill(6), lbl)
            return (case_rank, padded)
        entries = sorted(entries, key=_key)
    return "\n".join(f"{label}. {text}"
                     for label, text in entries if text)


def _parse_inline_legend_cell(
    cell_text: str, text_transform
) -> tuple[str, list[tuple[str, str]]]:
    """Parse a cell like `«PH_IMG»||A. Gateway.\n\nB. Chapels.\n…` into
    (image_placeholder, legend-entries). Returns ("", []) if the cell
    isn't an image + inline-legend.

    The `||` is MediaWiki same-line cell shorthand, but here we treat
    it as a soft separator between the image and the first legend
    entry.  Subsequent entries appear on separate lines.
    """
    # Split on the FIRST `||` only (image || first-entry-starts-here)
    if "||" not in cell_text:
        return "", []
    head, _, rest = cell_text.partition("||")
    head = head.strip()
    # Head must be a bare placeholder for this to be the pattern
    if not re.fullmatch(
            re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH), head):
        return "", []
    # Parse rest into one-entry-per-line.  Any remaining `||` inside
    # `rest` (shouldn't occur for the canonical pattern but guard
    # anyway) and blank lines become line breaks.  `_LEGEND_ENTRY_RE`
    # matches each non-empty line against the `L. text` shape.
    rest = rest.replace("||", "\n")
    entries: list[tuple[str, str]] = []
    for raw in rest.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        raw = _strip_cell_attributes(raw)
        line = text_transform(raw)
        line = _clean_legend_text(line)
        m = _LEGEND_ENTRY_RE.match(line)
        if m:
            entries.append((m.group(1), m.group(2)))
        # Non-matching lines get dropped (whitespace or stray text).
    return head, entries


def _ascii_fold_label(label: str) -> str:
    """Fold a label to plain ASCII for regex-shape validation.

    * Bold/italic/small-caps markers (`«I»`, `«/I»`, etc.) → dropped
      so italic-wrapped labels (ARACHNIDA Fig. 31 `«I»d«/I»`) reach
      the validators as bare letters instead of failing on the leading
      `«` character.
    * Unicode Mathematical Italic letters (𝑎–𝑧, 𝐴–𝑍, ℎ) → ASCII
      (MUSCULAR SYSTEM Fig. 9)
    * Unicode superscript digits (⁰¹²³⁴⁵⁶⁷⁸⁹) → ASCII digits
      (HEXAPODA Fig. 14 `T⁸`, `S⁷`)
    * Unicode subscript digits (₀₁₂…) → ASCII digits
    * Prime family (′ ″ ‴ ‵ etc.) → dropped (HYDROMEDUSAE Fig. 26
      `a′, g″, k′`)
    * Greek letters (α-ω, Α-Ω) → ASCII placeholder letters so legend
      labels using Greek symbols (ANATOMY Muscular Plate Fig. 1/2)
      pass the legend-label shape validator.

    The display form stays intact — only the validator sees the fold."""
    label = re.sub(r"«/?(?:B|I|SC)»", "", label)
    # `<sup>1</sup>` / `<sub>1</sub>` HTML markup → bare text
    # (ARACHNIDA Fig. 31 `''stig''<sup>1</sup>` → "stig1").
    label = re.sub(r"</?su[bp]>", "", label, flags=re.IGNORECASE)
    out = []
    for ch in label:
        cp = ord(ch)
        if 0x1D44E <= cp <= 0x1D467:
            out.append(chr(ord('a') + cp - 0x1D44E))
        elif 0x1D434 <= cp <= 0x1D44D:
            out.append(chr(ord('A') + cp - 0x1D434))
        elif cp == 0x210E:
            out.append('h')
        elif cp in _SUPERSCRIPT_TO_ASCII:
            out.append(_SUPERSCRIPT_TO_ASCII[cp])
        elif cp in _SUBSCRIPT_TO_ASCII:
            out.append(_SUBSCRIPT_TO_ASCII[cp])
        elif cp in _PRIMES:
            continue
        elif cp in _LIGATURE_FOLD:
            out.append(_LIGATURE_FOLD[cp])
        elif 0x03B1 <= cp <= 0x03C9:
            # Lowercase Greek alphabet (α=0x03B1 … ω=0x03C9).
            # Map to ASCII a..x cyclically — we only care about
            # alpha-shape validity, not faithful transliteration.
            out.append(chr(ord('a') + (cp - 0x03B1) % 24))
        elif 0x0391 <= cp <= 0x03A9:
            out.append(chr(ord('A') + (cp - 0x0391) % 24))
        else:
            out.append(ch)
    # Strip trailing whitespace so labels like `m, r ′` (which folds
    # to `m, r ` with a trailing space from the dropped prime) still
    # match the strict legend-label regex.
    return ''.join(out).strip()


def _entries_look_like_legend(entries: list[tuple[str, str]]) -> bool:
    """Return True only if every parsed (label, text) tuple has a
    label matching one of the accepted legend-label shapes.  Defence
    against mis-classifying non-legend `||`-rich tables (e.g. FULMINIC
    ACID chemist names).  Three progressively lenient patterns:

      1. strict: purely alphanumeric (A, P₁, X₁X₁, c,c, 1, 10, 16-19)
      2. multi-word: biological abbreviations (cl. osc., osc. div.)
      3. lenient: short (≤15 chars) with spaces/&/punctuation
         allowed, for cases like HEXAPODA `T8 &c` (et cetera).
    """
    if not entries:
        return False
    for label, text in entries:
        folded = _ascii_fold_label(label)
        if (not _LEGEND_LABEL_STRICT_RE.match(folded)
                and not _LEGEND_LABEL_MULTIWORD_RE.match(folded)
                and not _LEGEND_LABEL_LENIENT_RE.match(folded)):
            return False
        if not text:
            return False
    return True


def _strip_cell_attributes(cell: str) -> str:
    """Strip leading `attr=val|` cell-attribute prefix and `{{Ts|…}}`
    styling templates from a wikitable cell's content.  Used by the
    legend parsers so `colspan=3|Malpighian corpuscles.` renders as
    `Malpighian corpuscles.`, not as literal attribute text.  Also
    drops a bare leading `|` that a `{{Ts|…}}|content` sequence
    leaves behind after template stripping (WEAVING Fig. 20)."""
    cell = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", cell)
    m = _CELL_ATTR_PREFIX_RE.match(cell)
    if m:
        cell = cell[m.end():]
    if cell.startswith("|"):
        cell = cell[1:].lstrip()
    return cell


def _split_multicol_row_cells(
    row_text: str, text_transform
) -> list[str]:
    """Split a `||`-separated wikitable row into transformed cells,
    handling `\\n|`-as-cell-separator normalisation, attribute stripping,
    and the `text_transform` pass.  Shared between the single-row
    parser (full-entry-per-cell / alternating-pair) and the cross-row
    column-major parser (for multi-row legend entries).

    Preserves *internal* empty cells (an empty col-0 with content in
    col-1 is a real shape, e.g. ARACHNIDA Fig 65's `| || D. Chelicera.
    ||` last row) but trims leading/trailing structural-artifact
    empties from the row-marker `|` and trailing `||`.
    """
    normalised = re.sub(r"\n\s*\|(?![-}|])", "||", row_text)
    pieces = normalised.replace("||", "\x01").split("\x01")
    # Strip the single leading row-start `|` from the first piece
    # only — internal `|` belongs to cell content (none, normally).
    if pieces:
        pieces[0] = pieces[0].lstrip("|")
    pieces = [p.strip() for p in pieces]
    # Drop trailing empty piece (artifact of a trailing `||` or final
    # `\n`-cell-separator).  Keep internal empties — they're real
    # empty cells whose column position matters.
    while pieces and not pieces[-1]:
        pieces.pop()
    pieces = [_strip_cell_attributes(p).strip() for p in pieces]
    return [text_transform(p) for p in pieces]


def _parse_multicol_legend_rows_column_major(
    rows: list[str], text_transform
) -> list[tuple[str, str]] | None:
    """Parse N rows of `||`-separated cells as column-major legend
    entries with multi-row continuation support.

    Each row produces N cells, one per column.  Within a column,
    cells in successive rows compose entries: a cell that matches
    a full-entry label-shape starts a NEW entry; a cell that doesn't
    is treated as a CONTINUATION of the previous entry in the same
    column (joined with a space).  Entries are returned column-major
    so the reading order matches the print layout (top-to-bottom of
    column 1, then column 2, …).

    Canonical case: ARACHNIDA Fig 7 (Limulus dorsal-surface diagram)
    where each column has 3–4 entries spread across 9 rows of cells.

    Returns None when:
      - rows don't form a uniform column grid,
      - the first cell in a column is a continuation (no prior entry
        to attach to), or
      - the resulting entries fail the legend-label shape check.
    """
    row_cells: list[list[str]] = []
    n_cols: int | None = None
    for row in rows:
        cells = _split_multicol_row_cells(row, text_transform)
        if not cells:
            continue
        if n_cols is None:
            n_cols = len(cells)
        if len(cells) < n_cols:
            # Short row — likely a `colspan=N` annotation or note
            # appended inside the legend wikitable (ARACHNIDA Fig 47
            # has `|colspan=2|[Observe the powerful gnathobases…]`
            # as the final row).  Stop legend processing here so
            # the note doesn't get absorbed as a continuation of
            # the previous column's entry.  Anything after this row
            # is left to fall through into the surrounding layout
            # unwrap as separate paragraphs.
            break
        elif len(cells) > n_cols:
            return None
        row_cells.append(cells)

    if not row_cells or n_cols is None or n_cols < 2:
        return None

    def _label_shape_real(label_text: str, cell_orig: str) -> bool:
        """Reject plain-lowercase pseudo-labels from `_MULTICOL_FULL_
        ENTRY_RE` matches — `mesosoma, each with a movable` parses as
        label=`mesosoma`, text=`each with a movable`, but `mesosoma`
        is a continuation word, not a real legend label.  Real labels
        are italic in source, contain uppercase or digits, or are
        short Roman / abbreviation forms.
        """
        if cell_orig.lstrip().startswith("«I»"):
            return True
        return bool(re.search(r"[A-Z0-9]", label_text))

    columns: list[list[tuple[str, str]]] = [[] for _ in range(n_cols)]
    for cells in row_cells:
        for c_idx, cell in enumerate(cells):
            cell_stripped = cell.strip()
            if not cell_stripped:
                continue
            first_is_italic = cell_stripped.startswith("«I»")
            if first_is_italic:
                m = _MULTICOL_FULL_ENTRY_ITALIC_RE.match(cell_stripped)
                if m:
                    label = m.group(1).strip()
                    txt = _clean_legend_text(m.group(2)).rstrip(". ")
                    columns[c_idx].append((label, txt))
                    continue
            cleaned = _clean_legend_text(cell_stripped)
            m = _MULTICOL_FULL_ENTRY_RE.match(cleaned)
            if m and _label_shape_real(m.group(1), cell_stripped):
                label = m.group(1)
                txt = m.group(2).rstrip(". ")
                columns[c_idx].append((label, txt))
                continue
            # Continuation: append to the previous entry in this
            # column.  No prior entry → the column starts with a
            # non-label cell, which isn't a legend shape.
            if not columns[c_idx]:
                return None
            prev_label, prev_text = columns[c_idx][-1]
            cont = cleaned.rstrip(". ").strip()
            if cont:
                columns[c_idx][-1] = (
                    prev_label, f"{prev_text} {cont}".strip())

    entries = [e for col in columns for e in col]
    return entries if entries else None


def _row_is_single_full_entry(row: str) -> bool:
    """True iff the row has exactly one non-empty cell and it is a
    complete `LABEL,. text` legend entry.  These are the
    rowspan-continuation rows of a 2-column legend (ARACHNIDA Fig 31):
    the right column's cell spans two rows, so the second row carries
    only the left column's next entry."""
    cells = [c for _s, _a, c in split_wiki_row(row) if c.strip()]
    if len(cells) != 1:
        return False
    c = cells[0].strip()
    if c.startswith("«I»"):
        return bool(_MULTICOL_FULL_ENTRY_ITALIC_RE.match(c))
    return bool(_MULTICOL_FULL_ENTRY_RE.match(_clean_legend_text(c)))


def _collect_rowspan_legend(
    rows: list[str], text_transform,
) -> list[tuple[str, str]]:
    """Column-major legend collection for `rowspan`-uneven rows
    (ARACHNIDA Fig 31).  Each cell is a complete entry; the right
    column uses `rowspan=2`, so alternate rows have only the left
    cell.  Reads every cell by column index — col 0 from all rows,
    then col 1 from the rows that have it — which yields the print's
    column-major reading order without needing uniform rows."""
    row_cells = [_split_multicol_row_cells(r, text_transform) for r in rows]
    max_cols = max((len(c) for c in row_cells), default=0)
    entries: list[tuple[str, str]] = []
    for col in range(max_cols):
        for cells in row_cells:
            if col >= len(cells):
                continue
            cell = cells[col].strip()
            if not cell:
                continue
            if cell.startswith("«I»"):
                m = _MULTICOL_FULL_ENTRY_ITALIC_RE.match(cell)
            else:
                m = _MULTICOL_FULL_ENTRY_RE.match(_clean_legend_text(cell))
            if m:
                entries.append(
                    (m.group(1).strip(), m.group(2).rstrip(". ").strip()))
    return entries


def _parse_multicol_legend_row(
    row_text: str, text_transform
) -> list[tuple[str, str]]:
    """Parse a row of `||`-separated legend entries.

    Two shapes are supported:

    1. Alternating-pair (Cluny vol 1 p. 46):
         `A.||Gateway.||F.||Tomb of St Hugh.||M.||Bakehouse.`
       Every OTHER cell is a label, the next is its text.

    2. Full-entry-per-cell (Mosque of Amr vol 2 p. 450):
         `1. Kibla. || 5. Fountain for Ablution`
       Every cell is a complete `label. text` entry.

    Detection: if the first cell itself matches the `label. text`
    shape, we treat every cell as a full entry; otherwise we fall back
    to alternating-pair parsing.
    """
    # Wikitable cells can be separated by `||` on a single line OR by
    # `\n|` (cell on each line). Normalise the latter to `||` so the
    # split handles both shapes — otherwise multi-line cells merge
    # into single entries with embedded newlines/pipes, breaking
    # label detection (TUNICATA Fig. 2 Mantle-and-Test legend,
    # POLYZOA Paludicella legend). Leave `\n|-` (row sep) and `\n|}`
    # (close) alone. Known minor regression: MOSQUE Fig. 1 Plan of
    # Amr was already emitting a garbage mixed-separator legend pre-
    # fix; with normalisation it falls through to prose instead. The
    # content survives either way.
    normalised = re.sub(r"\n\s*\|(?![-}|])", "||", row_text)
    pieces = normalised.replace("||", "\x01").split("\x01")
    pieces = [p.lstrip("|").strip() for p in pieces if p.strip()]
    if not pieces:
        return []
    # Strip per-cell attribute prefixes (colspan=, rowspan=, width=,
    # etc.) — these are cell-layout hints, not legend content.
    pieces = [_strip_cell_attributes(p).strip() for p in pieces]
    pieces = [p for p in pieces if p]
    if not pieces:
        return []
    out: list[tuple[str, str]] = []
    # Apply text_transform up front so {{em|…}} spacers, italics, and
    # entity refs are normalized before label detection.
    transformed = [text_transform(p) for p in pieces]

    # Shape detection on the first cell.
    #
    # If the first cell is italicized (biological-abbreviation
    # convention, SPONGES Fig. 2 "''cl. osc.''"), it's a label-only
    # cell — the format is label || text alternating, NOT full-entry.
    # Without this guard `cl. osc.,` would match the full-entry regex
    # as (label=`cl`, text=`osc.,`) and produce garbage.
    first_is_italic = transformed[0].strip().startswith(
        "\u00abI\u00bb")
    first = _clean_legend_text(transformed[0])
    if not first_is_italic and _MULTICOL_FULL_ENTRY_RE.match(first):
        # Full-entry-per-cell
        for t in transformed:
            cell = _clean_legend_text(t)
            m = _MULTICOL_FULL_ENTRY_RE.match(cell)
            if m:
                out.append((m.group(1), m.group(2).rstrip(". ")))
        return out
    # Italic-label full-entry-per-cell (ARACHNIDA Figs 31/32, ECHINODERMA
    # plate 1).  Each cell carries `''label'', text.` rather than the
    # alternating `''label''||text` shape \u2014 without this branch the
    # cells get merged into garbage pairs and the legend rows leak as
    # plain prose with `||` separators showing through.
    if first_is_italic and _MULTICOL_FULL_ENTRY_ITALIC_RE.match(transformed[0]):
        for t in transformed:
            m = _MULTICOL_FULL_ENTRY_ITALIC_RE.match(t)
            if m:
                # group(1) already includes the \u00abI\u00bb\u2026\u00ab/I\u00bb wrapper plus
                # optional `<sup>\u2026</sup>` / `<sub>\u2026</sub>` suffix.
                label = m.group(1).strip()
                text_part = _clean_legend_text(m.group(2)).rstrip(". ")
                out.append((label, text_part))
        return out
    # Alternating-pair.  Labels may terminate with `.` OR `,`
    # (HYDROMEDUSAE Fig. 30 uses `''ex'',||Ex-umbral ectoderm.`);
    # strip both trailing punctuations.
    i = 0
    while i + 1 < len(transformed):
        label = _clean_legend_text(transformed[i]).rstrip(".,")
        text = _clean_legend_text(transformed[i + 1])
        if label and text:
            out.append((label, text))
        i += 2
    return out


def _extract_poem_legend(
    table_raw: str, text_transform
) -> list[str]:
    """Extract legend content from a nested layout table as a list of
    LEGEND-format lines (`### Subhead.` or `L. text`).  Tries three
    shapes in preference order:

      A. `<poem>` blocks with `{{csc|…}}` subheadings (Abbey_3)
      B. `||`-separated (label, text) rows (HYDROMEDUSAE Fig. 73)
      C. Plain-paragraph `''label'', text` entries in a single cell
         (HYDROMEDUSAE Fig. 55)
    """
    body = re.sub(r"^\{\|[^\n]*\n?", "", table_raw)
    body = re.sub(r"\n?\|\}\s*$", "", body)
    # Strip a leading `|-…\n` row-separator so the first cell doesn't
    # swallow it (POLYZOA Fig. 7 Cristatella legend has `|-valign="top"`
    # as the very first line after `{|...`, and the split regex only
    # matches `\n\s*\|-+` which misses a `|-` at position 0). Without
    # this, entry 1 parses as label `-valign="top"`, fails legend
    # validation, and the whole Shape B path falls through.
    body = re.sub(r"^(?:\s*\|-+[^\n]*\n)+", "", body)
    cells = re.split(r"\n(?:\s*\|-+[^\n]*\n)+", body)

    # --- Shape A: poems + csc subheadings ---
    poem_lines: list[str] = []
    for cell_block in cells:
        current_cell: list[str] = []

        def flush_cell():
            if not current_cell:
                return
            text = "\n".join(current_cell)
            _emit_legend_chunk(text, text_transform, poem_lines)

        for line in cell_block.split("\n"):
            stripped = line.strip()
            if stripped.startswith("|") and current_cell:
                flush_cell()
                current_cell = [stripped.lstrip("|").strip()]
            elif stripped.startswith("|"):
                current_cell = [stripped.lstrip("|").strip()]
            else:
                current_cell.append(line)
        flush_cell()
    if poem_lines:
        return poem_lines

    # --- Shape B: ||-separated (label, text) rows ---
    pair_entries: list[tuple[str, str]] = []
    for cell_block in cells:
        if "||" in cell_block:
            pair_entries.extend(
                _parse_multicol_legend_row(cell_block, text_transform))
    if pair_entries and _entries_look_like_legend(pair_entries):
        return [f"{lbl}. {text}" for lbl, text in pair_entries]

    # --- Shape C: plain-paragraph `''label'', text` entries ---
    plain_entries: list[tuple[str, str]] = []
    entry_re = re.compile(
        r"^\s*(?:''\s*)?([A-Za-z0-9](?:[A-Za-z0-9.\-]{0,15})?)"
        r"(?:\s*''\s*)?[.,]\s+(.+\S)\s*$",
        re.DOTALL,
    )
    for cell_block in cells:
        for para in re.split(r"\n\s*\n", cell_block):
            para = para.strip()
            if not para:
                continue
            if para.startswith("|"):
                para = para[1:].strip()
                if not para:
                    continue
            transformed = text_transform(para)
            cleaned = _clean_legend_text(transformed)
            m = entry_re.match(cleaned)
            if m:
                plain_entries.append((m.group(1), m.group(2)))
    if plain_entries and _entries_look_like_legend(plain_entries):
        return [f"{lbl}. {text}" for lbl, text in plain_entries]

    return []


def _emit_legend_chunk(text: str, text_transform,
                        out: list[str]) -> None:
    """Parse one cell's worth of legend source text, appending entries
    and `### Subhead.` lines to `out` in SOURCE ORDER.

    Subheadings (`{{csc|Church.}}`) and `<poem>` blocks are
    interleaved in the source; this single-pass scanner walks forward
    and emits them in the order they appear, so the reader sees e.g.:

        ### Church.
        A. High altar.
        B. Altar of St Paul.
        ### Monastic Buildings.
        G. Cloister.
    """
    sub_re = re.compile(r"\{\{\s*csc\s*\|([^{}]*)\}\}", re.IGNORECASE)
    poem_re = re.compile(r"<poem>([\s\S]*?)</poem>", re.IGNORECASE)
    pos = 0
    while pos < len(text):
        m_sub = sub_re.search(text, pos)
        m_poem = poem_re.search(text, pos)
        # Pick whichever matches first
        if m_sub and (not m_poem or m_sub.start() < m_poem.start()):
            content = _clean_legend_text(m_sub.group(1)).rstrip(".")
            if content:
                out.append(f"### {content}.")
            pos = m_sub.end()
        elif m_poem:
            for ln in m_poem.group(1).splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                ln = text_transform(ln)
                ln = _clean_legend_text(ln)
                em = _LEGEND_ENTRY_RE.match(ln)
                if em:
                    out.append(f"{em.group(1)}. {em.group(2)}")
            pos = m_poem.end()
        else:
            break


def _image_ph_filename(
    ph_id: str, inner_registry: ElementRegistry
) -> str | None:
    """Look up the filename for an IMAGE element placeholder."""
    if inner_registry.labels.get(ph_id) != "IMAGE":
        return None
    raw = inner_registry.elements[ph_id][1]
    m = re.match(r"\[\[(?:File|Image):([^\]|]+)",
                 raw, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _image_ph_extcap(
    ph_id: str, inner_registry: ElementRegistry
) -> str:
    """The trailing caption the (context-blind) walker folded into an
    IMAGE element via `|EXTCAP:` — the first line(s) of a figure's
    caption when the image and caption sit in the same wikitable cell
    (HYDROMEDUSAE Fig 36: the walker grabs the `{{sc|Fig. 36.}}—…`
    line into the image, leaving the continuation in the cell).  A
    captioned/legended producer must recover it and re-join, otherwise
    rebuilding the IMG marker from cell text alone drops it."""
    inner = inner_registry.inners.get(ph_id, "")
    if "|EXTCAP:" in inner:
        return inner.rsplit("|EXTCAP:", 1)[1]
    return ""


def _looks_like_caption(text: str) -> bool:
    """True if `text` starts with `Fig. N.` / `Plate N.` / `{{sc|Fig` /
    `''Fig.''`."""
    return bool(_FIG_CAPTION_START_RE.match(text))


def _find_caption_row_idx(
    rows: list[str], start_idx: int, text_transform
) -> int | None:
    """Locate the caption row (one starting with `Fig. N.—` or similar)
    among `rows[start_idx+1:]`.  This lets us skip attribution lines
    like `From Allman's Gymnoblastic Hydroids…` that sit between the
    image and the real caption.  Returns the row index, or None.

    Falls back to accepting a row where the `Fig. N.` pattern appears
    MID-CELL after an in-cell attribution (HYDROMEDUSAE Fig. 71 Velella:
    `From G. H. Fowler, after Cuvier, …  {{sc|Fig. 71.}}—…`)."""
    # Preferred: a row whose prefix-stripped content STARTS with Fig.
    for i in range(start_idx + 1, len(rows)):
        body = rows[i].strip()
        body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
        for _ in range(5):
            before = body
            if body.startswith("|"):
                body = body[1:].lstrip()
            m = _CELL_ATTR_PREFIX_RE.match(body)
            if m:
                body = body[m.end():]
            body = body.lstrip()
            if body == before:
                break
        if _looks_like_caption(body):
            return i
    # Fallback: a row where `{{sc|Fig.}}` / `''Fig.''` / `Fig. N.`
    # appears mid-cell (attribution precedes the caption in the same
    # cell).  `_extract_caption_from_colspan_row` handles extraction.
    for i in range(start_idx + 1, len(rows)):
        if _FIG_CAPTION_INLINE_RE.search(rows[i]):
            return i
    return None


def _extract_caption_from_colspan_row(
    row_text: str, text_transform
) -> str | None:
    """Pull caption text from a `|colspan=N …|caption` row.  In-cell
    attribution (HYDROMEDUSAE Fig. 71 Velella: `From G. H. Fowler,
    after Cuvier… {{sc|Fig. 71.}}—…`) is appended to the caption in
    parens so the credit survives."""
    body = row_text.strip()
    if body.startswith("|"):
        body = body[1:]
    body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
    # After Ts-template strip a bare `|` separator can remain
    # (`{{Ts|ac}}|content` → `|content`). Drop it before the
    # attribute-prefix match — otherwise the lone pipe leaks
    # through as in-cell attribution and gets appended to the
    # caption as `(|.)` (MOSQUE Figs 1 & 3).
    body = re.sub(r"^\s*\|\s*", "", body)
    # Strip the attribute prefix using the shared regex so we cover
    # the full set (cellpadding, nowrap, etc.) and tolerate leading
    # whitespace — otherwise unrecognised attrs leak into "attribution"
    # and get appended to the caption in parens (DINOFLAGELLATA Fig. 2,
    # ECHINODERMA Fig. 4, DYNAMO Figs 9-10, …).
    m = _CELL_ATTR_PREFIX_RE.match(body)
    if m:
        body = body[m.end():]
    body = body.strip()
    # Multi-cell caption rows: a single image can have its caption
    # split across multiple `||`-separated cells (ANATOMY Muscular
    # Plate row carries `Fig. 1.|| colspan=2 |Fig. 2.` for one image
    # showing both figures).  Strip cell-attribute prefix from each
    # piece and join with a space so the inter-cell `||` and trailing
    # `colspan=N|` don't leak into the rendered caption.
    if "||" in body:
        pieces: list[str] = []
        for part in body.split("||"):
            part = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", part).strip()
            part = re.sub(r"^\s*\|\s*", "", part)
            am = _CELL_ATTR_PREFIX_RE.match(part)
            if am:
                part = part[am.end():]
            part = part.strip()
            if part:
                pieces.append(part)
        body = " ".join(pieces)
    # Split out in-cell attribution preceding the Fig. caption.
    attribution = None
    if not _looks_like_caption(body):
        fig_m = _FIG_CAPTION_INLINE_RE.search(body)
        if fig_m:
            prefix = body[:fig_m.start()].strip()
            body = body[fig_m.start():]
            if prefix:
                attr_clean = _clean_text(text_transform(prefix))
                attr_clean = attr_clean.rstrip(" .,;:")
                if attr_clean:
                    attribution = attr_clean
    caption = _clean_text(text_transform(body.strip()))
    if not caption:
        return None
    if attribution:
        caption = _append_attribution(caption, attribution)
    return caption


def _append_attribution(caption: str, attribution: str) -> str:
    """Combine a caption with its attribution in a stable parenthetical
    form.  Avoids doubling parens when attribution itself already
    wraps in parens, and idempotent if called twice."""
    attribution = attribution.strip(" .")
    if not attribution:
        return caption
    if attribution in caption:
        return caption
    # If attribution is already parenthesized, keep its form.
    if attribution.startswith("(") and attribution.endswith(")"):
        return f"{caption.rstrip()} {attribution}"
    return f"{caption.rstrip()} ({attribution}.)"


def _collect_attribution_rows(
    rows: list[str], img_row_idx: int, cap_row_idx: int,
    text_transform,
) -> str:
    """Collect clean attribution text from rows strictly between the
    image row and the caption row.  Typical sources: `{{sm|From A. M.
    Paterson, …}}` or `|style="font-size:smaller"|From O. Maas, …`.
    Returns a single joined string (may be empty)."""
    parts: list[str] = []
    for i in range(img_row_idx + 1, cap_row_idx):
        body = rows[i].strip()
        body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
        body = re.sub(r"\{\{sm\|([^{}]*)\}\}", r"\1", body,
                      flags=re.IGNORECASE)
        # Strip leading `|` and attribute prefixes iteratively — a
        # `{{Ts|…}}` template that precedes the cell content leaves
        # `||` behind after stripping, and the first `|`-strip only
        # peels one (POLYZOA Fig. 2 Crisia: `|{{Ts|sm}}|(After
        # Hincks.)` reduces to `|(After Hincks.)`, then needs another
        # peel before the plain attribution is exposed).
        for _ in range(5):
            before = body
            if body.startswith("|"):
                body = body[1:].lstrip()
            m = _CELL_ATTR_PREFIX_RE.match(body)
            if m:
                body = body[m.end():]
            body = body.lstrip()
            if body == before:
                break
        body = body.strip()
        if not body:
            continue
        t = _clean_text(text_transform(body))
        t = t.strip(" .,;")
        if t:
            parts.append(t)
    return " ".join(parts).strip()


def _parse_prose_legend_rows(
    legend_rows: list[str], text_transform
) -> list[str]:
    """Parse rows that contain prose-format legend entries (no ||
    separator, multiple `LABEL, text.` or `LABEL. text.` chunks per
    line, optional `''Subheading'':` lines).

    Returns LEGEND-format lines (`### Sub.` or `L. text`), or []
    if no plausible entries were found.
    """
    out: list[str] = []
    subhead_re = re.compile(
        r"^\s*(?:&emsp;|&ensp;|&nbsp;|\s)*"
        r"''([^']{2,30})''\s*:\s*(?:<br\s*/?>)?\s*(.*)$",
        re.IGNORECASE)
    entry_label = _LEGEND_LABEL
    entry_re = re.compile(
        r"^\s*(" + entry_label +
        r"(?:\s*,\s*" + entry_label + r")*)[.,]\s+(.+)$",
        re.DOTALL)

    for row in legend_rows:
        # Strip cell attrs, Ts styling, and leading `|`
        row = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", row)
        # `{{hi|…}}` has two forms: `{{hi|text}}` and
        # `{{hi|amount|text}}`.  Unwrap both, keeping only the text
        # argument.
        row = re.sub(r"\{\{hi\|[^|{}]*\|([^{}]*)\}\}", r"\1", row,
                     flags=re.IGNORECASE)
        row = re.sub(r"\{\{hi\|([^{}]*)\}\}", r"\1", row,
                     flags=re.IGNORECASE)
        # Work line by line within the row
        cell_content = row
        if cell_content.lstrip().startswith("|"):
            cell_content = cell_content.lstrip()[1:]
        for line in cell_content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Subheading line: `''Name'':<br>rest`  or  `''Name'':`
            m = subhead_re.match(line)
            if m:
                sub = m.group(1).strip().rstrip(":")
                out.append(f"### {sub}.")
                line = m.group(2).strip()
                if not line:
                    continue
            # Transform + clean the line
            tl = text_transform(line)
            tl = _clean_legend_text(tl)
            if not tl:
                continue
            # Split on sentence boundaries that precede a label.
            chunks = re.split(
                r"(?<=\.)\s+(?=(?:[IVX]+|[A-Za-z][A-Za-z0-9.]{0,4})"
                r"[,.] )", tl)
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                em = entry_re.match(chunk)
                if em:
                    label = em.group(1).strip()
                    text = em.group(2).strip().rstrip(". ")
                    if text:
                        out.append(f"{label}. {text}")
                # Chunks that don't parse are silently dropped —
                # we only want real legend entries.
    # Only return if we got multiple real entries (not just
    # subheadings) — a single-subheading-only legend is suspicious.
    entry_count = sum(1 for line in out if not line.startswith("###"))
    if entry_count >= 3 and _entries_look_like_legend(
            [tuple(line.split(". ", 1)) for line in out
             if not line.startswith("###")]):
        return out
    return []


def _try_image_layout_subclass(
    inner: str, text_transform,
    inner_registry: ElementRegistry
) -> str | None:
    """Attempt to recognize one of the three known image-layout
    subclasses (INLINE, MULTICOL, POEM).  Returns the processed output
    on match, or None to fall through to the generic unwrapper."""
    if not inner_registry:
        return None
    image_phs = [k for k, label in inner_registry.labels.items()
                 if label == "IMAGE"]
    if not image_phs:
        return None

    # Multi-image layout: outer table wraps 2+ images.  Disentangle
    # into per-image figures rather than treating "multi-image" as a
    # distinct shape — each image is its own figure (caption,
    # attribution, optional poem-legend) that just happens to share
    # the same outer wikitable.  The shared table encodes parallel
    # content either column-major (side-by-side: all images in the
    # same row, caption/attribution/poem cells stacked beneath in the
    # matching column — BEE Figs 18/19, LARVAL FORMS Figs 5/6, FUNGI
    # Figs 12/13, WEAVING Figs 19/20, METAMORPHOSIS Figs 4/5) or row-
    # major (vertical stack: each image in its own row, caption /
    # attribution / poem rows immediately follow — MUSCULAR SYSTEM
    # Figs 7/8, GYMNOSPERMS Macrozamia/Ginkgo).
    if len(image_phs) >= 2:
        table_phs = [k for k, (t, _) in inner_registry.elements.items()
                     if t == "TABLE"]
        poem_phs = [k for k, label in inner_registry.labels.items()
                     if label == "POEM"]
        if table_phs:
            return None  # nested layout table — let generic unwrap handle
        # Consume runs of consecutive `|-` row separators in one match.
        # Source occasionally has stray `|-\n|-\n` doubles (ARACHNIDA
        # Fig 1) which a one-shot `\n\s*\|-+[^\n]*\n` only consumes
        # once, leaking the second `|-` as a spurious "-" cell.  Also
        # strip any leading `|-` row marker — LEAF Figs 5/6's source
        # opens the table with ``|-valign="bottom"`` before any cells,
        # which otherwise leaks into row-0's first cell and shifts the
        # column-index mapping by one (so the caption-row columns no
        # longer line up with the image-row columns).
        inner_stripped = re.sub(r"^\s*\|-+[^\n]*\n", "", inner)
        rows_local = re.split(
            r"\n(?:\s*\|-+[^\n]*\n)+", inner_stripped)
        # Per-image row positions
        img_row_of: dict[str, int] = {}
        for ph in image_phs:
            for i, r in enumerate(rows_local):
                if ph in r:
                    img_row_of[ph] = i
                    break

        # A `Fig. N.` marker inside a cell, possibly wrapped in
        # ``{{sc|…}}`` / ``{{csc|…}}``.  Used to split cells that hold
        # an attribution above the caption (FUNGI Fig 12's cell:
        # ``{{smaller block/s}}From Strasburger's…{{smaller block/e}}
        # {{sc|Fig. 12.}}—…``).
        _CELL_FIG_MARKER_RE = re.compile(
            r"\{\{(?:sc|csc|SC)\|\s*(?:Fig|Plate)s?\.?"
            r"|\b(?:Fig|Plate)s?\.?\s*\d"
        )

        def _classify_cells(
            cells_text: list[str], image_ph: str
        ) -> tuple[list[str], list[str], list[str]]:
            """Process a list of cell content strings belonging to one
            image; return (caption_parts, attribution_parts,
            legend_lines).  ``split_wiki_row`` collapses newlines inside
            a cell to spaces, so a cell that originally held both an
            attribution and a caption (FUNGI Fig 12) arrives as one
            string.  Use the ``Fig. N.`` marker as the split boundary:
            text before the marker is attribution, text from the marker
            onward is the caption."""
            caption_parts: list[str] = []
            attribution_parts: list[str] = []
            legend_lines: list[str] = []
            for content in cells_text:
                if not content.strip():
                    continue
                if image_ph in content:
                    continue  # skip the image cell itself
                # Pull poem placeholders out of the cell → legend.
                cell_text = content
                for poem_ph in poem_phs:
                    if poem_ph in cell_text:
                        poem_raw = inner_registry.elements[poem_ph][1]
                        _emit_legend_chunk(
                            poem_raw, text_transform, legend_lines)
                        cell_text = cell_text.replace(poem_ph, "")
                # Split at the first Fig./Plate marker.  Before =
                # attribution (or other non-caption text); from the
                # marker on = caption.
                marker = _CELL_FIG_MARKER_RE.search(cell_text)
                if marker:
                    before = cell_text[:marker.start()].strip()
                    after = cell_text[marker.start():].strip()
                    if before:
                        c = _clean_text(text_transform(before))
                        if c:
                            attribution_parts.append(c)
                    if after:
                        c = _clean_text(text_transform(after))
                        if c:
                            caption_parts.append(c)
                else:
                    c = _clean_text(text_transform(cell_text))
                    if c:
                        if _looks_like_caption(c):
                            caption_parts.append(c)
                        else:
                            attribution_parts.append(c)
            return caption_parts, attribution_parts, legend_lines

        def _emit_image(image_ph: str, cells_text: list[str]) -> list[str]:
            fn = _image_ph_filename(image_ph, inner_registry)
            if not fn:
                return []
            cap_parts, attr_parts, legend_lines = _classify_cells(
                cells_text, image_ph)
            cap = " ".join(cap_parts).strip()
            for attr in attr_parts:
                cap = _append_attribution(cap, attr) if cap else attr
            out = [build_img_marker(fn, cap)]
            if legend_lines:
                out.append(
                    "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
            return out

        # Unified disentangle: group images by the row they live in.
        # Each group is processed as a self-contained mini-figure-set
        # whose "content rows" run from the group's image-row + 1 up
        # to the next group's image-row (or the end of the table).
        # The slicing strategy is determined per-group:
        #
        # * one image in the group → vertical: concatenate all cells
        #   in the content rows as that image's content.
        # * multiple images in the group → side-by-side: column-slice
        #   the content rows by each image's column index in the
        #   image-row.
        #
        # This handles:
        # * pure side-by-side (BEE, FUNGI, LARVAL FORMS Fig 5/6,
        #   WEAVING, METAMORPHOSIS) — one group, multi-image
        # * pure vertical (MUSCULAR SYSTEM, GYMNOSPERMS Macrozamia/
        #   Ginkgo) — N groups, each single-image
        # * N×M image grids with per-row caption rows (LEAF Figs 36-41,
        #   Figs 42-45) — N groups, each multi-image
        # in a single pass.
        groups: dict[int, list[str]] = {}
        for ph in image_phs:
            groups.setdefault(img_row_of[ph], []).append(ph)
        sorted_group_rows = sorted(groups.keys())

        parts_out: list[str] = []
        ok = True
        for i, img_row_idx in enumerate(sorted_group_rows):
            phs_in_group = groups[img_row_idx]
            next_row = (sorted_group_rows[i + 1]
                        if i + 1 < len(sorted_group_rows)
                        else len(rows_local))
            content_rows = list(range(img_row_idx + 1, next_row))

            if len(phs_in_group) == 1:
                # Vertical slice: all content cells in content_rows
                # belong to this image.
                ph = phs_in_group[0]
                cells_text: list[str] = []
                for r_idx in content_rows:
                    for _sep, _attr, content in split_wiki_row(
                            rows_local[r_idx]):
                        if content.strip():
                            cells_text.append(content)
                parts_out.extend(_emit_image(ph, cells_text))
            else:
                # Side-by-side slice: each image owns the cells at
                # its column index in every content row.
                img_row_cells = list(split_wiki_row(
                    rows_local[img_row_idx]))
                image_col_of: dict[str, int] = {}
                for col_idx, (_sep, _attr, content) in enumerate(
                        img_row_cells):
                    for ph in phs_in_group:
                        if ph in content:
                            image_col_of[ph] = col_idx
                if len(image_col_of) != len(phs_in_group):
                    ok = False
                    break
                for ph in sorted(phs_in_group,
                                 key=lambda p: image_col_of[p]):
                    col_idx = image_col_of[ph]
                    col_cells = []
                    for r_idx in content_rows:
                        cells = list(split_wiki_row(rows_local[r_idx]))
                        if col_idx < len(cells):
                            _sep, _attr, cell_content = cells[col_idx]
                            col_cells.append(cell_content)
                    parts_out.extend(_emit_image(ph, col_cells))

        if ok and parts_out:
            return "\n\n" + "\n\n".join(parts_out) + "\n\n"
        return None

    img_ph = image_phs[0]
    filename = _image_ph_filename(img_ph, inner_registry)
    if not filename:
        return None

    table_phs = [k for k, (t, _) in inner_registry.elements.items()
                 if t == "TABLE"]

    # Split into rows on `|-`.  Consume consecutive `|-` separators
    # in one match (see ARACHNIDA Fig 1 source: stray `|-\n|-\n`
    # before the legend).
    rows = re.split(r"\n(?:\s*\|-+[^\n]*\n)+", inner)

    # Locate the row containing the image placeholder and the row
    # containing the caption (typically colspan=N … Fig. …).
    img_row_idx = None
    for i, r in enumerate(rows):
        if img_ph in r:
            img_row_idx = i
            break
    if img_row_idx is None:
        return None

    poem_phs = [k for k, label in inner_registry.labels.items()
                 if label == "POEM"]

    # Locate the caption row.  `fig_cap_idx` is set only when we find
    # a row that actually begins with `Fig. N.—` / `Plate N.—` —
    # strong signal that this table IS a figure layout.  When absent,
    # most subclasses fall back to `img_row_idx + 1`, but the MULTICOL
    # and IMG_ATTRIBUTION_CAPTION paths REQUIRE `fig_cap_idx` so that
    # non-figure tables (FULMINIC ACID formula comparison) can't
    # masquerade as legends.
    fig_cap_idx = _find_caption_row_idx(rows, img_row_idx, text_transform)
    cap_idx = fig_cap_idx
    if cap_idx is None and img_row_idx + 1 < len(rows):
        cap_idx = img_row_idx + 1

    # -- POEM_COLUMNS_LEGEND: outer has 1 image + N poems as DIRECT
    #    children (not wrapped in a nested table).  Fig. 6 / Fig. 7
    #    in ABBEY use this.  Row 0 = colspan image, row 1 = colspan
    #    caption, rows 2+ = cells containing `<poem>` placeholders.
    if poem_phs and not table_phs:
        # Image row + caption row expected
        if cap_idx is not None:
            caption = _extract_caption_from_colspan_row(
                rows[cap_idx], text_transform)
            if caption:
                # Walk each poem in registry-insertion order (which
                # matches source order because extract() is linear).
                # For each POEM, extract its content and parse into
                # LEGEND entries. CSC subheadings that sit OUTSIDE
                # poems (between cells) aren't common in this shape
                # but we support them by also scanning the raw inner
                # text between poem placeholders.
                legend_lines: list[str] = []
                for ph, label in inner_registry.labels.items():
                    if label != "POEM":
                        continue
                    eraw = inner_registry.elements[ph][1]
                    # Extract poem body, apply _emit_legend_chunk so
                    # it goes through the same entry-pattern matcher
                    # as the other legend handlers.
                    _emit_legend_chunk(eraw, text_transform, legend_lines)
                if legend_lines:
                    img_marker = build_img_marker(filename, caption)
                    legend_block = (
                        "{{LEGEND:" + "\n".join(legend_lines) +
                        "}LEGEND}")
                    # Wrap in \n\n on both sides so the figure+legend
                    # always ends up as its own paragraph, regardless
                    # of surrounding whitespace. Excess newlines get
                    # collapsed by the transform normalizer.
                    return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- NESTED_LEGEND: outer has a single TABLE child (a nested
    #    layout table containing the legend).  `_extract_poem_legend`
    #    tries three shapes (poems / ||-pairs / plain paragraphs) and
    #    returns an empty list if none matches — in that case we fall
    #    through so that data tables aren't mis-claimed as legends.
    if len(table_phs) == 1:
        inner_table_ph = table_phs[0]
        inner_table_raw = inner_registry.elements[inner_table_ph][1]
        legend_lines = _extract_poem_legend(
            inner_table_raw, text_transform)
        if legend_lines:
            # Caption: prefer a Fig.-matched row.  In the Abbey_3
            # shape, the caption row ALSO contains the inner-table
            # placeholder, which we must strip before caption
            # extraction (otherwise its processed legend content
            # would get substituted back into the caption field).
            caption = None
            if fig_cap_idx is not None:
                row_without_ph = rows[fig_cap_idx].replace(
                    inner_table_ph, "")
                caption = _extract_caption_from_colspan_row(
                    row_without_ph, text_transform)
            if not caption:
                caption_row = next(
                    (r for r in rows if inner_table_ph in r), None)
                if caption_row is not None:
                    caption_cell = caption_row.replace(
                        inner_table_ph, "").strip()
                    caption_cell = re.sub(r"^\|\s*", "", caption_cell)
                    caption_cell = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*",
                                           "", caption_cell)
                    caption = _clean_text(text_transform(caption_cell))
            img_marker = build_img_marker(filename, caption)
            legend_block = (
                "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
            return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- INLINE_LEGEND: image row contains `||` on the image's own line.
    if "||" in rows[img_row_idx]:
        # Image row: `|[[Image:…]]||A. x\n\nB. y\n…`
        img_row = rows[img_row_idx]
        # Skip any leading `{{ts|…}}` styling line before the image cell.
        row_lines = [l for l in img_row.split("\n") if l.strip()]
        # The image-cell line is whichever one contains img_ph.
        image_line = next(l for l in row_lines if img_ph in l)
        # Image cell starts at `|` and runs across multiple lines until
        # the next line starting with `|` (next cell) or end of row.
        idx = row_lines.index(image_line)
        cell_lines = [image_line]
        for nxt in row_lines[idx + 1:]:
            if nxt.lstrip().startswith("|"):
                break
            cell_lines.append(nxt)
        cell_text = "\n".join(cell_lines).lstrip("|")
        _, entries = _parse_inline_legend_cell(cell_text, text_transform)
        if entries and _entries_look_like_legend(entries):
            # Caption: first row AFTER the image row that looks like a
            # colspan caption.
            caption = None
            for r in rows[img_row_idx + 1:]:
                c = _extract_caption_from_colspan_row(r, text_transform)
                if c:
                    caption = c
                    break
            img_marker = build_img_marker(filename, caption)
            legend_block = ("{{LEGEND:" +
                             _format_legend_entries(entries) + "}LEGEND}")
            return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- MULTICOL_LEGEND: image row + caption row + N rows of
    #    ||-separated (label, text) pairs.  Guards:
    #    1. Caption row must start with `Fig. N.—` / `Plate N.—`.
    #    2. At least one legend row must contain `||`.
    #    3. At least 2 (label,text) entries must parse.
    #    4. Every label must match the strict legend-label shape.
    #
    #    Two parser passes: the column-major pass handles multi-row
    #    entries (cells in successive rows that continue a previous
    #    entry, e.g. ARACHNIDA Fig 7 where each legend entry spans
    #    2-5 cells down one column).  If that fails (or yields a
    #    non-legend label shape), fall back to the per-row parser
    #    which handles full-entry-per-cell and alternating-pair
    #    layouts (single-row entries only).
    if fig_cap_idx is not None:
        legend_rows = rows[fig_cap_idx + 1:]
        has_multicol_marker = any("||" in r for r in legend_rows)
        if has_multicol_marker:
            caption = _extract_caption_from_colspan_row(
                rows[fig_cap_idx], text_transform)
            if caption:
                col_major_entries = (
                    _parse_multicol_legend_rows_column_major(
                        legend_rows, text_transform))
                used_column_major = bool(
                    col_major_entries
                    and len(col_major_entries) >= 2
                    and _entries_look_like_legend(col_major_entries))
                if used_column_major:
                    entries = col_major_entries
                else:
                    entries = []
                    for r in legend_rows:
                        entries.extend(
                            _parse_multicol_legend_row(r, text_transform))
                if (entries
                        and len(entries) >= 2
                        and _entries_look_like_legend(entries)):
                    img_marker = build_img_marker(filename, caption)
                    # Column-major output already reflects the print
                    # reading order — top-to-bottom of column 1, then
                    # column 2.  Preserve that.  Per-row entries
                    # (full-entry-per-cell, alternating-pair) come out
                    # row-major in source order — keep the legacy
                    # alphabetic sort there, which is what the rest of
                    # the corpus has been validated against.
                    legend_block = (
                        "{{LEGEND:" +
                        _format_legend_entries(
                            entries,
                            sort_alphabetic=not used_column_major) +
                        "}LEGEND}")
                    return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- IMG_PROSE_LEGEND: image + caption + rows of prose-format
    #    entries (multiple `LABEL, text.` chunks per line, optional
    #    `''Subheading'':` lines).  HEXAPODA Fig. 3 Thorax of Saw-Fly.
    #    Runs before IMG_SIMPLE_CAPTION so the sub-legend survives as
    #    a LEGEND block.
    if (fig_cap_idx is not None
            and not poem_phs and not table_phs
            and not any("||" in r for r in rows[fig_cap_idx + 1:])):
        legend_lines = _parse_prose_legend_rows(
            rows[fig_cap_idx + 1:], text_transform)
        if legend_lines:
            caption = _extract_caption_from_colspan_row(
                rows[fig_cap_idx], text_transform)
            if caption:
                img_marker = build_img_marker(filename, caption)
                legend_block = (
                    "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
                return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- IMG_SIMPLE_CAPTION / IMG_ATTRIBUTION_CAPTION: 1 image + a
    #    Fig.-matched caption row, no legend (no meaningful `||`, no
    #    POEM/TABLE children).  Covers simple 2-row image+caption
    #    (Corymorpha Fig. 3) and 3-row image+attribution+caption
    #    (HYDROMEDUSAE Fig. 5/29).  Rows between image and caption
    #    are attribution and get dropped.
    #
    #    A SPURIOUS `||` at the start of the image row (the MediaWiki
    #    `||[[Image:…]]` shorthand for "no attrs, content follows") is
    #    tolerated — detect it by asking whether the image row has
    #    any substantive text content besides the image placeholder.
    def _image_row_has_legend_text() -> bool:
        text = rows[img_row_idx].replace(img_ph, "")
        text = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}", "", text)
        text = re.sub(r"(?:colspan|rowspan|align|valign|style|width|"
                      r"class|cellpadding|cellspacing|bgcolor)"
                      r"\s*=\s*\"?[^\"|]*\"?", "", text,
                      flags=re.IGNORECASE)
        text = text.replace("||", "").replace("|", "")
        return bool(text.strip())

    if (fig_cap_idx is not None
            and not poem_phs and not table_phs
            and not any("||" in r for r in rows[fig_cap_idx + 1:])
            and not _image_row_has_legend_text()):
        caption = _extract_caption_from_colspan_row(
            rows[fig_cap_idx], text_transform)
        if caption:
            attr = _collect_attribution_rows(
                rows, img_row_idx, fig_cap_idx, text_transform)
            if attr:
                caption = _append_attribution(caption, attr)
            return f"\n\n{build_img_marker(filename, caption)}\n\n"

    return None


def _simple_table_text(raw: str) -> str | None:
    """If `raw` is a tiny wikitable containing only plain text cells
    (no images, no nested placeholders, no complex markup, no
    multi-cell `||` rows) return the cells joined with spaces. Used by
    layout-wrapper caption bundling to fold a nested "copyright notice"
    or attribution table into the figure's caption instead of leaving
    it as a stray PRE block below. Multi-cell rows (`||`) indicate a
    legend or data table — never fold those, they need their own
    structure and folding them would leak raw `||`/`''` markers into
    the caption (seen on ICHTHYOLOGY Fig. 4, SPONGES, TUNICATA).
    """
    if _PH in raw:
        return None
    if len(raw) > 500:
        return None
    if "[[File:" in raw or "[[Image:" in raw or "{{IMG:" in raw:
        return None
    # Reject multi-cell rows — this is a legend/data table.
    if re.search(r"\|\|", raw):
        return None
    body = re.sub(r"^\s*\{\||\|\}\s*$", "", raw.strip())
    body = re.sub(r"\|-[^\n]*", "\n", body)
    pieces: list[str] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cell = line[1:]
        if "|" in cell:
            head, _, tail = cell.partition("|")
            if re.match(
                r"^\s*(?:align|valign|style|width|class|colspan|"
                r"rowspan|cellpadding|bgcolor|nowrap|height)\b",
                head, re.IGNORECASE,
            ):
                cell = tail
        pieces.append(cell.strip())
    text = " ".join(p for p in pieces if p).strip()
    return text or None


# Attribution-before-caption pattern: cell contains `From X` /
# `After X` / `Photo X` / `Copyright X` / `Modified X` and then a
# `Fig.` or `Plate.` caption marker LATER in the cell.  When a
# wikitable packs attribution and caption into one cell with
# attribution first (HYDROMEDUSAE Fig 71 plain prose, ARACHNIDA
# Fig 33 wrapped in `{{Fs|92%|…}}` styling), this lets us spot the
# shape and defer to the legacy producer's attribution-reordering
# logic.  When attribution is AFTER the Fig marker (the normal
# in-source order), this pattern doesn't match because `From` only
# appears after `Fig`.
_ATTRIBUTION_BEFORE_CAPTION_RE = re.compile(
    r"\b(?:From|After|Photo|Copyright|Modified)\b"
    r".{0,400}?(?:\{\{\s*sc\s*\|\s*)?(?:Fig|Plate)s?\.?\s*\d",
    re.IGNORECASE | re.DOTALL,
)


# Shared figure pipeline — every figure producer (CAPTIONED_FIGURE,
# CAPTIONED_FIGURE_GRID, FIGURE_GROUP, and the multi-image path inside
# the catch-all) routes its per-image text cells through these.  The
# canonical output is identical regardless of source shape: extract
# routes each cell into (caption, attribution, legend); assemble emits
# `{{IMG:fn|caption (attribution)}}` plus an optional separate
# `{{LEGEND:…}LEGEND}` block.

_CELL_FIG_MARKER_RE = re.compile(
    r"\{\{(?:sc|csc|SC)\|\s*(?:Fig|Plate)s?\.?"
    r"|\b(?:Fig|Plate)s?\.?\s*\d"
)


# ── ICL presentation-markup normalizer ───────────────────────────────
#
# Family-scoped (ICL only): pure-DECORATION templates that NO figure
# path needs and EVERY figure path benefits from removing.  Unwrapping
# them once, up front, lets the legend / caption / multicol detectors
# and producers operate on clean content instead of each
# re-implementing a partial unwrap.
#
# Three exclusions, each by the "does any path need it?" test:
#   * Semantic typography (`sc`, `b`, `i`) — the OUTPUT path needs them;
#     they survive as `«SC»/«B»/«I»` markers via the text transform.
#   * Cell-attribute templates (`Ts`) — sit in the attribute position;
#     stripped per-cell by `_strip_cell_attributes`.
#   * `{{Hi|…}}` hanging-indent — NOT decoration: it wraps each legend
#     entry individually, so the Hi boundary IS the entry boundary that
#     the legend-extraction path needs (`_extract_hi_legend`).  Removing
#     it would destroy that structure.
_ICL_WRAPPER_TEMPLATES = frozenset({
    "center", "c", "fs", "nowrap",
    "fine block", "fine print", "small", "smaller", "fqm",
})
_ICL_SPACER_TEMPLATES = frozenset({
    "em", "gap", "thinsp", "ensp", "emsp", "nbsp", "dhr", "vr", "hr",
})


def _match_braced_template(text: str, i: int) -> tuple[int, str] | tuple[None, None]:
    """``text[i:i+2] == '{{'``.  Return ``(end, inner)`` where ``end``
    is the index just past the matching ``}}`` and ``inner`` is the
    content between the braces, handling nested ``{{…}}``.  Returns
    ``(None, None)`` if unbalanced."""
    depth = 0
    k, n = i, len(text)
    while k < n - 1:
        if text[k] == "{" and text[k + 1] == "{":
            depth += 1
            k += 2
            continue
        if text[k] == "}" and text[k + 1] == "}":
            depth -= 1
            k += 2
            if depth == 0:
                return k, text[i + 2:k - 2]
            continue
        k += 1
    return None, None


def _split_template_args(inner: str) -> list[str]:
    """Split a template's inner on top-level ``|`` (ignoring ``|``
    inside nested ``{{…}}`` / ``[[…]]``)."""
    args: list[str] = []
    depth = 0
    cur: list[str] = []
    i, n = 0, len(inner)
    while i < n:
        two = inner[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            i += 2
            continue
        if two in ("}}", "]]"):
            depth = max(0, depth - 1)
            cur.append(two)
            i += 2
            continue
        if inner[i] == "|" and depth == 0:
            args.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(inner[i])
        i += 1
    args.append("".join(cur))
    return args


def _normalize_icl_markup(text: str) -> str:
    """Unwrap pure-layout templates from ICL content to a fixpoint.

    Wrapper templates (`{{Hi|…}}`, `{{center|…}}`, `{{Fs|N%|…}}`,
    `{{nowrap|…}}`, …) collapse to their LAST argument — which is the
    content regardless of whether the template carries a leading size
    / option argument (`{{hi|X}}` and `{{hi|1em|X}}` both → ``X``).
    Spacer templates (`{{em|.7}}`, `{{gap}}`, …) collapse to a single
    space.  Nested wrappers (`{{center|{{Fs|92%|X}}}}`) resolve over
    successive passes.  Non-layout templates (`{{sc|…}}`, `{{IMG:…}}`,
    placeholders) are left untouched.
    """
    prev = None
    while text != prev:
        prev = text
        out: list[str] = []
        i, n = 0, len(text)
        while i < n:
            if text[i] == "{" and i + 1 < n and text[i + 1] == "{":
                end, inner = _match_braced_template(text, i)
                if end is not None:
                    args = _split_template_args(inner)
                    name = args[0].strip().lower()
                    if name in _ICL_WRAPPER_TEMPLATES:
                        out.append(args[-1] if len(args) > 1 else "")
                        i = end
                        continue
                    if name in _ICL_SPACER_TEMPLATES:
                        out.append(" ")
                        i = end
                        continue
            out.append(text[i])
            i += 1
        text = "".join(out)
    return text


def _unwrap_cell_wrappers(text: str) -> str:
    """Unwrap purely positional/styling wrappers around figure-cell
    text so a downstream Fig-marker split doesn't slice through a
    balanced template:

      * ``{{center|X}}`` / ``{{c|X}}`` → ``X``
      * ``{{Fs|N%|X}}`` → ``X``
      * ``<span style="…">X</span>`` / ``<div …>X</div>`` → ``X``

    Handles nested templates by balanced-brace matching for the
    outer wrapper (``{{center|{{sc|Fig}}. 10.—…}}`` — the simple
    `[^{}]*` regex can't cross the inner ``{{sc|…}}``).  Iterates to
    a fixpoint.  Italic / small-caps / `{{hi|…}}` wrappers are
    intentionally preserved — they carry caption-semantic content.
    """
    def _strip_outer_braced_wrapper(s: str) -> str:
        stripped = s.strip()
        for prefix_re, _ in (
            (r"^\{\{\s*(?:center|c|Center)\s*\|", "center-like"),
            (r"^\{\{\s*Fs\s*\|[^{}|]*\|", "Fs-with-size"),
        ):
            m = re.match(prefix_re, stripped, flags=re.IGNORECASE)
            if not m:
                continue
            start = m.end()
            depth = 1
            i = start
            while i < len(stripped) - 1:
                if stripped[i] == "{" and stripped[i + 1] == "{":
                    depth += 1
                    i += 2
                    continue
                if stripped[i] == "}" and stripped[i + 1] == "}":
                    depth -= 1
                    if depth == 0:
                        inner = stripped[start:i]
                        tail = stripped[i + 2:]
                        return (inner + tail).strip()
                    i += 2
                    continue
                i += 1
        return s

    prev = None
    while text != prev:
        prev = text
        text = re.sub(
            r"<(span|div)\b[^>]*>(.*?)</\1>", r"\2",
            text, flags=re.IGNORECASE | re.DOTALL)
        text = _strip_outer_braced_wrapper(text)
    return text


def _extract_figure_components(
    cells_text: list[str],
    inner_registry: ElementRegistry,
    text_transform,
    skip_ph: str | None = None,
) -> tuple[list[str], list[str], list[str]]:
    """For one image's worth of text cells, return
    ``(caption_parts, attribution_parts, legend_lines)``.

    * If ``skip_ph`` is the image's own placeholder and a cell contains
      it (in-cell caption shape — ORDNANCE Fig 54, STEAM_ENGINE Fig 10),
      the placeholder is stripped and the remainder is processed as
      that image's caption material.  Empty remainders are skipped.
    * Embedded POEM placeholders contribute legend entries.
    * A Fig./Plate marker inside a cell splits it: text before becomes
      attribution, text from the marker onward becomes caption.
    * Cells without a marker are classified by `_looks_like_caption`.
    """
    poem_phs = [k for k, label in inner_registry.labels.items()
                if label == "POEM"]
    caption_parts: list[str] = []
    attribution_parts: list[str] = []
    legend_lines: list[str] = []
    for content in cells_text:
        if not content.strip():
            continue
        if skip_ph and skip_ph in content:
            content = content.replace(skip_ph, "").strip()
            if not content:
                continue
        content = _unwrap_cell_wrappers(content).strip()
        if not content:
            continue
        cell_text = content
        for poem_ph in poem_phs:
            if poem_ph in cell_text:
                poem_raw = inner_registry.elements[poem_ph][1]
                _emit_legend_chunk(
                    poem_raw, text_transform, legend_lines)
                cell_text = cell_text.replace(poem_ph, "")
        marker = _CELL_FIG_MARKER_RE.search(cell_text)
        if marker:
            before = cell_text[:marker.start()].strip()
            after = cell_text[marker.start():].strip()
            if before:
                c = _clean_text(text_transform(before))
                if c:
                    attribution_parts.append(c)
            if after:
                c = _clean_text(text_transform(after))
                if c:
                    caption_parts.append(c)
        else:
            c = _clean_text(text_transform(cell_text))
            if c:
                if _looks_like_caption(c):
                    caption_parts.append(c)
                else:
                    attribution_parts.append(c)
    return caption_parts, attribution_parts, legend_lines


def _assemble_figure_parts(
    filename: str,
    caption_parts: list[str],
    attribution_parts: list[str],
    legend_lines: list[str],
    *,
    width: int | None = None,
    height: int | None = None,
    align: str | None = None,
) -> list[str]:
    """Return the canonical figure marker(s) for one image.

    Returns a list of one or two marker strings: the ``{{IMG:…}}``
    marker (with caption + parenthesized attribution baked in), and —
    only if legend content exists — a separate ``{{LEGEND:…}LEGEND}``
    marker.  Callers are responsible for `\\n\\n` flanking when joining
    multiple figures together.

    ``width``/``height``/``align`` carry the image's layout metadata into
    the marker (the metadata-carrying pattern).  Optional — callers that
    work from a bare filename omit them and get the identical
    metadata-free marker.
    """
    cap = " ".join(caption_parts).strip()
    for attr in attribution_parts:
        cap = _append_attribution(cap, attr) if cap else attr
    out = [build_img_marker(
        filename, cap or None, width=width, height=height, align=align)]
    if legend_lines:
        out.append(
            "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
    return out


def _process_captioned_figure(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Focused producer for `CAPTIONED_FIGURE` — single-image figure
    layout.

    Classifier predicate guarantees:
      * Exactly 1 IMAGE child in `inner_registry`.
      * That image sits in row 0, alone in its cell among the images
        (no parallel images — that's `CAPTIONED_FIGURE_GRID`).
      * No POEM or nested-wikitable children.
      * No data-table header signal.

    Iteration strategy: treat every non-empty cell across all rows as
    a text unit for this single image, then route through the shared
    `_extract_figure_components` + `_assemble_figure_parts`.  Source
    shape variations — in-cell `<br>`-separated caption (ORDNANCE
    Fig 54, STEAM_ENGINE Fig 10), attribution-before-Fig
    (HYDROMEDUSAE Fig 71), `{{Fs|N%|…}}` styling wrappers (ARACHNIDA
    Fig 33, BAG-PIPE Fig 1) — all collapse to the same canonical
    figure marker because partition + assemble are shared with every
    other figure producer.

    No fall-back to the catch-all: cases outside the predicate's
    guarantees get their own labels and producers.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if not image_phs:
        return ""
    image_ph = image_phs[0]
    filename = _image_ph_filename(image_ph, inner_registry)
    if not filename:
        return ""

    # The walker may have folded the caption's first line(s) into the
    # image via `|EXTCAP:` (image + caption share a cell — Fig 36).
    # Re-attach it at the image's position so the full caption is
    # processed as one unit instead of being dropped on rebuild.
    extcap = _image_ph_extcap(image_ph, inner_registry)
    extcap = re.sub(r"<br\s*/?>", " ", extcap, flags=re.IGNORECASE).strip()

    # Collect text units: every non-empty cell across all rows.  `<br>`
    # → space first so an in-cell multi-segment caption arrives as a
    # single string per cell.  `{{Ts|…}}` is styling-only — strip it.
    inner = _normalize_icl_markup(inner)
    cleaned = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    rows = re.split(r"\|-[^\n]*", cleaned)
    cells_text: list[str] = []
    for row in rows:
        for _sep, _attr, content in split_wiki_row(row):
            if not content.strip():
                continue
            content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "",
                              content).strip()
            if not content:
                continue
            if extcap and image_ph in content:
                content = content.replace(
                    image_ph, image_ph + " " + extcap, 1)
            cells_text.append(content)

    cap_parts, attr_parts, legend = _extract_figure_components(
        cells_text, inner_registry, text_transform, skip_ph=image_ph)

    parts = _assemble_figure_parts(
        filename, cap_parts, attr_parts, legend)
    return "\n\n" + "\n\n".join(parts) + "\n\n"


def _process_captioned_figure_inline(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Focused producer for `CAPTIONED_FIGURE_INLINE` — single-image
    figure where the caption rides in the image's own cell.

    The classifier predicate guarantees a single IMAGE child, no
    POEM / nested-table siblings, and substantive text in the image
    row beyond the placeholder.  The cell looks like:

        ``[[File:Foo.png|…]]<br>{{sc|Fig. N.}}—caption text``

    optionally wrapped in ``{{center|…}}`` or
    ``<span style="…">…</span>``.

    Iteration: walk all cells, treat the image-bearing cell with the
    placeholder stripped as caption material; route through the
    shared component extractor + assembler.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if not image_phs:
        return ""
    image_ph = image_phs[0]
    filename = _image_ph_filename(image_ph, inner_registry)
    if not filename:
        return ""

    inner = _normalize_icl_markup(inner)
    cleaned = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    rows = re.split(r"\|-[^\n]*", cleaned)
    cells_text: list[str] = []
    for row in rows:
        for _sep, _attr, content in split_wiki_row(row):
            if not content.strip():
                continue
            content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "",
                              content).strip()
            if not content:
                continue
            cells_text.append(content)

    cap_parts, attr_parts, legend = _extract_figure_components(
        cells_text, inner_registry, text_transform, skip_ph=image_ph)

    parts = _assemble_figure_parts(
        filename, cap_parts, attr_parts, legend)
    return "\n\n" + "\n\n".join(parts) + "\n\n"


# A `[[File:…]]` / `[[Image:…]]` opener inside a prose FIGURE span.
_PROSE_FIG_IMG_RE = re.compile(
    r"\[\[(?:File|Image):[^\]]*\]\]", re.IGNORECASE)
_FIG_SC_WRAP_RE = re.compile(
    r"\{\{\s*(?:c?sc|small-caps)\s*\|", re.IGNORECASE)


def _strip_figure_outer_wrapper(span: str) -> str:
    """Peel layout / small-caps wrappers enclosing a WHOLE figure down to
    image + caption.  `_unwrap_cell_wrappers` handles `{{center|…}}`/`{{Fs|…}}`;
    this loop adds the small-caps figure wrappers (`{{csc|[[File:…]]<br>Fig. N.}}`
    — ACCUMULATOR Fig 20) it deliberately preserves for caption *cells* but which,
    around an entire figure, are only caption styling."""
    prev = None
    while span != prev:
        prev = span
        span = _unwrap_cell_wrappers(span).strip()
        if _FIG_SC_WRAP_RE.match(span) and "[[" in span:
            end, inner = _match_braced_template(span, 0)
            if end is not None:
                args = _split_template_args(inner)
                content = args[-1] if len(args) > 1 else inner
                span = (content + span[end:]).strip()
    return span


def _process_prose_figure(raw: str, text_transform) -> str | None:
    """Structural producer for the prose ``SHAPE_FIGURE`` — an image plus
    its structurally-delimited caption run, carved as one span by the
    walker's figure break (float-div, ``{{center|…}}``-wrapped, or bare).

    Extracts the image (filename + width/align), folds the caption and
    attribution INTO the ``{{IMG:…}}`` marker and emits any legend as a
    separate ``{{LEGEND:…}}`` — routed through the same
    ``_extract_figure_components`` + ``_assemble_figure_parts`` the table
    captioned-figure producers use, so prose and table figures fold
    identically.  Folding *and consuming* the caption is what kills the
    leak/duplicate: the caption never survives as loose body text, and a
    marker that already carries its caption leaves the export-time
    caption-fill (`_patch_img`) nothing to do.

    Returns ``None`` for spans this producer doesn't yet own (no image, or
    ≥2 images — the multi-image caption row, e.g. Figs 22-23); the caller
    falls back to the legacy assembly so those keep rendering as before.
    """
    span = _strip_figure_outer_wrapper(raw.strip())
    images = _PROSE_FIG_IMG_RE.findall(span)
    if len(images) != 1:
        return None
    m = _PROSE_FIG_IMG_RE.search(span)

    image_inner = re.sub(
        r"^\[\[(?:File|Image):", "", m.group(0), flags=re.IGNORECASE)
    image_inner = re.sub(r"\]\]$", "", image_inner)
    img_marker = _process_image(image_inner, text_transform)
    pm = IMG_PARTS_RE.match(img_marker)
    if pm is None:
        return None
    filename = pm.group(1)
    meta = parse_img_meta(pm.group(2))
    filelink_caption = pm.group(3)

    material = span[m.end():]
    material = re.sub(r"<br\s*/?>", " ", material, flags=re.IGNORECASE)
    material = _normalize_icl_markup(material)
    paras = [p for p in re.split(r"\n\n+", material) if p.strip()]

    cap_parts, attr_parts, legend = _extract_figure_components(
        paras, ElementRegistry(), text_transform)
    # EB1911 figures frequently repeat the caption in BOTH the File link's
    # caption param AND a separate `{{sc|Fig.}} N.—…` block beneath the
    # image (WEIGHING / SEWING MACHINES, ORDNANCE Figs 22, 23-30).  The
    # block caption is the fuller one (carries the `Fig. N.—` prefix), so
    # it wins; the File-link caption is only used when no block caption
    # exists — folding both would duplicate the text.
    if filelink_caption and not cap_parts:
        cap_parts = [filelink_caption]

    parts = _assemble_figure_parts(
        filename, cap_parts, attr_parts, legend,
        width=meta.get("width"), height=meta.get("height"),
        align=meta.get("align"))
    return "\n\n" + "\n\n".join(parts) + "\n\n"


# Legend-cell shape detection.  Used at both classification and
# production time to decide whether a row carries multicol legend
# entries.  Operating on CELL CONTENT (post-`split_wiki_row`) — not
# raw row text — lets us see past cell-attribute prefixes
# (``|align="right"|…``) and simple wrapper templates (``{{nowrap|…}}``).

# A "label" token is short and distinct from prose text:
#   * Italic-wrapped: ``«I»...«/I»`` with up to ~30 chars (covers
#     single letters, multi-word abbreviations like `«I»cl. osc.«/I»`,
#     hyphenated like `«I»prae-gen«/I»`).
#   * Plain: 1-6 alphanumerics (digit-starting OK — `1`, `10`),
#     OR a compound form with internal `.`/`-`/`,` like `c.c`,
#     `c,c`, `st.c`, `prae-gen` (max 10 chars).
#   * Optional prime suffix (`′″‴`) — ARACHNIDA Fig 47 `7′`,
#     HYDROMEDUSAE Fig 49 `«I»g«/I»′`.
#
# Plain labels are deliberately kept short so plain words like
# `Osculum.` or `Gateway.` (the text-cell of an alternating-pair
# row) don't false-match as labels.
_LEGEND_CELL_LABEL = (
    r"(?:"
    r"«I»[^«]{1,30}«/I»"                                       # italic
    r"|[A-Za-z0-9]+\s+to\s+[A-Za-z0-9]+"                        # range (`III to VI`, `1 to 5`)
    r"|[A-Za-z0-9]{1,6}"                                        # 1-6 pure alphanumerics
    r"|[A-Za-z0-9]+[.,\-][A-Za-z0-9.,\-]{0,7}[A-Za-z0-9]"      # 3-10 with required internal punct
    r")"
    r"[′″‴]?"
)

_CELL_LABEL_ONLY_RE = re.compile(
    r"^\s*" + _LEGEND_CELL_LABEL + r"\s*[.,]\s*$"
)

_CELL_FULL_ENTRY_RE = re.compile(
    r"^\s*" + _LEGEND_CELL_LABEL + r"\s*[.,]\s+\S"
)


def _legend_cell_prep(content: str) -> str:
    """Normalise a cell's content before label-shape matching.

    Unwraps simple text templates (``{{nowrap|…}}``) and normalises
    HTML whitespace entities (``&emsp;``, ``&nbsp;``, etc.) to plain
    spaces so labels wrapped/padded with them match cleanly.  Mirrors
    what the producer's `_chop_legend_entries` does to cell pieces
    before parsing.
    """
    c = re.sub(r"\{\{[Nn]owrap\|([^{}]*)\}\}", r"\1", content)
    c = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", c)
    return c.strip()


def _cell_is_legend_label(content: str) -> bool:
    """The cell is just a label (with `.` or `,` terminator).
    Examples: `1.`, `«I»osc.«/I»,`, `{{nowrap|&emsp;«I»a«/I»,&nbsp;}}`."""
    return bool(_CELL_LABEL_ONLY_RE.match(_legend_cell_prep(content)))


def _cell_is_legend_full_entry(content: str) -> bool:
    """The cell is `LABEL[.,]\\s+TEXT` — a complete legend entry.
    Examples: `1. Kibla.`, `«I»cl. osc.«/I», Closed osculum.`."""
    return bool(_CELL_FULL_ENTRY_RE.match(_legend_cell_prep(content)))


def _row_has_legend_multicol_cells(row: str) -> bool:
    """True iff the row's FIRST non-empty cell is a legend label and
    the row has ≥2 cells.  Covers both legend shapes:

      * **Alternating pairs** — `|«I»b«/I»,||Cephalic tentacles.` —
        cell 0 is a label-only cell, cell 1 is the description.
        Canonical: ABBEY Fig 5, GASTROPODA Fig 32, HYDROMEDUSAE Fig 30.

      * **Full-entry-per-cell** — `| 1. Kibla. || 5. Fountain…` —
        cell 0 is a full `LABEL.,TEXT` entry.  Canonical: MOSQUE OF AMR.

    The decision keys on the FIRST cell only.  A legend row always
    *starts* with a label; the trailing description cells must not be
    label-classified because short single-word descriptions
    (`Foot.`) or hyphenated phrases (`Mantle-skirt, …`) would
    spuriously match the label/full-entry shapes and skew a
    per-cell count.

    Cell-aware via ``split_wiki_row``, so cell-attribute prefixes
    (``align="right"|`` etc.) are stripped before matching.
    """
    cells = split_wiki_row(row)
    contents = [c for _sep, _attr, c in cells if c.strip()]
    if len(contents) < 2:
        return False
    first = contents[0]
    return _cell_is_legend_label(first) or _cell_is_legend_full_entry(first)


_LEGEND_ROW_PROSE_RE = re.compile(
    r"(?:^|\n)\s*"
    r"(?:«I»[A-Za-z][A-Za-z0-9.]{0,3}«/I»|[A-Za-z][A-Za-z0-9.]{0,3})"
    r"[′″‴]?"
    r"\s*[.,]\s+[A-Z‘“a-z]"
)


def _row_is_legend(row: str) -> bool:
    """True if ``row`` looks like a legend row (multicol or prose)."""
    if _row_has_legend_multicol_cells(row):
        return True
    if len(_LEGEND_ROW_PROSE_RE.findall(row)) >= 2:
        return True
    return False


def _chop_legend_entries(
    text: str, delimiter: str, text_transform,
) -> list[tuple[str, str]]:
    """Split ``text`` by ``delimiter`` and parse into legend (label,
    text) entries.

    Auto-detects the chunk shape from the first non-empty chunk:

    * Label-only (e.g. ``"A."`` or ``"«I»a«/I»"``) → alternating-pair
      mode: take chunks in pairs as (label, text).  Used for multicol
      rows like ``|A.||Gateway.||F.||Tomb of St Hugh.``.
    * Full-entry (e.g. ``"A. Gateway."`` / ``"«I»oc«/I», Lateral
      eyes."``) → each chunk is one complete entry.  Used for full-
      entry multicol rows (ARACHNIDA Fig 7) and prose cells with
      newline/semicolon-separated entries (HYDROMEDUSAE Fig 1).

    ``delimiter`` is either ``"||"`` (multicol row) or a single-char
    newline-like splitter (``"\\n"``).  The rest of the producer
    treats the returned entries identically regardless of how they
    were chopped.
    """
    # Normalise `\n|` cell separators to the `||` delimiter so a
    # multi-line multicol row chops into individual cells.  Some
    # legends pack 2-3 (label, text) pairs per row with `&emsp;`
    # spacer cells and newline-pipe separators between pairs
    # (GASTROPODA Fig 28); without this the `||` split glues the
    # `\n|&emsp;\n|`-joined neighbours onto the prior entry's text.
    if delimiter == "||":
        text = re.sub(r"\n\s*\|(?![-}|])", "||", text)
    pieces = [p.strip() for p in text.split(delimiter)]
    pieces = [p.lstrip("|").strip() for p in pieces if p]
    if not pieces:
        return []
    pieces = [_strip_cell_attributes(p).strip() for p in pieces]
    # Drop spacer-only cells (entity-only `&emsp;`/`&nbsp;` or empty) —
    # they separate (label, text) pairs in multi-pair rows and would
    # otherwise shift the alternating-pair index pairing.
    pieces = [p for p in pieces
              if re.sub(r"&[a-zA-Z]+;|&#\d+;|\s+", "", p)]
    if not pieces:
        return []
    transformed = [text_transform(p) for p in pieces]

    first = _clean_legend_text(transformed[0])
    first_is_italic = transformed[0].strip().startswith("«I»")

    # Full-entry shape: first chunk parses as a complete `label, text`.
    # Italic-wrapped first chunks must be tested against the italic
    # shape ONLY.  Falling through to the plain regex on the
    # italic-stripped text spuriously full-matches multi-word
    # abbreviations: ``«I»cl. osc.«/I»,`` cleaned to ``cl. osc.,``
    # parses as plain LABEL=`cl` + TEXT=`osc.,` even though the
    # italic shape rejects it (no text after the trailing comma).
    # That would route the row to full-entry mode where the actual
    # italic chunk fails → empty pair list (SPONGES Fig 2).
    if first_is_italic:
        full_match = bool(
            _MULTICOL_FULL_ENTRY_ITALIC_RE.match(transformed[0]))
    else:
        full_match = bool(_MULTICOL_FULL_ENTRY_RE.match(first))
    if full_match:
        out: list[tuple[str, str]] = []
        for t in transformed:
            cell = t if t.strip().startswith("«I»") else _clean_legend_text(t)
            m = (_MULTICOL_FULL_ENTRY_ITALIC_RE.match(cell)
                 if cell.strip().startswith("«I»")
                 else _MULTICOL_FULL_ENTRY_RE.match(_clean_legend_text(t)))
            if m:
                out.append(
                    (m.group(1).strip(), m.group(2).rstrip(". ").strip()))
        return out

    # Alternating-pair shape: even-indexed chunks are labels,
    # odd-indexed are texts.  Strip the abbreviation punctuation
    # from the label but keep text punctuation intact.
    out = []
    for i in range(0, len(transformed) - 1, 2):
        lbl = _clean_legend_text(transformed[i]).rstrip(".,")
        text = _clean_legend_text(transformed[i + 1])
        if lbl and text:
            out.append((lbl, text))
    return out


# `{{Hi|LABEL, text}}` / `{{Hi|SIZE|LABEL, text}}` / `{{hi|…}}` — a
# "hanging indent" template the source uses to typeset each legend
# entry.  Multiple per cell, scattered across columns (ARACHNIDA Fig
# 26, 78).  Both arities occur: a leading size argument is optional
# (ARACHNIDA Fig 3 uses bare `{{hi|content}}`).  The capture is the
# LAST argument either way.  Content is brace-free by producer time
# (italics already `«I»` markers).
_HI_LEGEND_RE = re.compile(r"\{\{[Hh]i\|(?:[^|{}]*\|)?([^{}]*)\}\}")


def _extract_hi_legend(
    inner: str, text_transform,
) -> tuple[list[str], str]:
    """Extract legend entries wrapped in ``{{Hi|SIZE|LABEL, text}}`` /
    ``{{hi|…}}`` hanging-indent templates.

    Each ``{{Hi}}`` chunk is one complete legend entry; chunks appear
    in source (column-major) order.  Returns ``(legend_lines,
    inner_without_hi)`` — the inner with the ``{{Hi}}`` chunks
    excised so the rest of the producer only sees the image, caption
    and attribution.  Returns ``([], inner)`` when fewer than two
    ``{{Hi}}`` chunks are present (not the hanging-indent shape).

    Canonical: ARACHNIDA Fig 26 (A–D in two columns), Fig 78
    (A/B/C with `;`-separated sub-references kept inside each entry).
    """
    chunks = _HI_LEGEND_RE.findall(inner)
    if len(chunks) < 2:
        return [], inner
    lines: list[str] = []
    for raw_chunk in chunks:
        t = text_transform(re.sub(r"<br\s*/?>", " ", raw_chunk)).strip()
        if t.startswith("«I»"):
            m = _MULTICOL_FULL_ENTRY_ITALIC_RE.match(t)
        else:
            m = _MULTICOL_FULL_ENTRY_RE.match(_clean_legend_text(t))
        if m:
            label = m.group(1).strip()
            text = m.group(2).rstrip(". ").strip()
            lines.append(f"{label}. {text}")
        else:
            cleaned = _clean_legend_text(t)
            if cleaned:
                lines.append(cleaned)
    return lines, _HI_LEGEND_RE.sub("", inner)


# A short italic legend label, possibly with a `<sup>/<sub>` suffix and
# an `X and Y` compound (ARACHNIDA Fig 3 `«I»m¹«/I» and «I»m²«/I»`).
_FLOWING_LABEL = (
    r"«I»[A-Za-z][A-Za-z0-9.]{0,6}(?:<su[bp]>[^<]+</su[bp]>)?«/I»"
    r"(?:\s+and\s+«I»[A-Za-z][A-Za-z0-9.]{0,6}(?:<su[bp]>[^<]+</su[bp]>)?«/I»)?"
)
_FLOWING_ENTRY_START_RE = re.compile(r"(" + _FLOWING_LABEL + r")\s*,\s")
_FLOWING_ATTRIBUTION_RE = re.compile(
    r"\(\s*(?:After|From|Modified|Photo|Copyright)\b", re.IGNORECASE)


def _extract_flowing_italic_legend(
    inner: str, text_transform,
) -> tuple[list[str], str]:
    """Extract a *flowing* italic-labelled legend — a run of
    ``«I»label«/I», text.`` entries packed into one cell, mixing
    `{{hi|…}}`-wrapped and bare entries separated by ``. `` / ``<br>``
    (ARACHNIDA Fig 3, Fig 31).  Distinct from `_extract_hi_legend`
    (discrete `{{Hi}}` chunks, plain labels — Fig 26, 78): here the
    entry boundary is the italic short-label, not the template.

    Operates per-row so a stray short italic in the caption row can't
    be mistaken for a legend entry.  In the legend row, ``{{hi|…}}`` is
    unwrapped transparently and the run is split on each italic-label
    start; a trailing ``(After …)`` attribution is left in place.

    Returns ``(legend_lines, inner_without_run)`` — the legend row's
    entry text removed, caption / attribution preserved.  Returns
    ``([], inner)`` when no row carries ≥3 such entries.
    """
    parts = re.split(r"(\|-[^\n]*)", inner)
    legend_lines: list[str] = []
    found = False
    for idx, part in enumerate(parts):
        if part.startswith("|-") or found:
            continue
        # A flowing legend is packed into ONE cell — each entry's text
        # follows its label directly (`«I»sf«/I», The sub-frontal…`),
        # entries `. `/`<br>`-separated.  Skip rows that are really
        # multicol: `||`-separated, OR an alternating `\n|` grid where
        # the label and its text sit in SEPARATE cells (HYDROMEDUSAE
        # Fig 74 `|«I»n«/I»,\n|Nectocalyx.`).  The latter is detected
        # by a bare label-only cell — flowing entries never put the
        # label alone in a cell.
        if "||" in part:
            continue
        if any(_cell_is_legend_label(c)
               for _s, _a, c in split_wiki_row(part)):
            continue
        unwrapped = _HI_LEGEND_RE.sub(lambda m: m.group(1), part)
        starts = list(_FLOWING_ENTRY_START_RE.finditer(unwrapped))
        if len(starts) < 3:
            continue
        # Slice each entry from its label to the next label start.
        run_start = starts[0].start()
        prefix = unwrapped[:run_start]
        for i, m in enumerate(starts):
            seg_end = (starts[i + 1].start() if i + 1 < len(starts)
                       else len(unwrapped))
            body = unwrapped[m.end():seg_end]
            # Trailing attribution belongs to the figure, not the
            # legend — cut it from the last entry and keep as suffix.
            suffix = ""
            attr = _FLOWING_ATTRIBUTION_RE.search(body)
            if attr:
                suffix = body[attr.start():]
                body = body[:attr.start()]
            label = _clean_legend_text(text_transform(m.group(1)))
            text = _clean_legend_text(text_transform(body)).rstrip(". ")
            if label and text:
                legend_lines.append(f"{label}. {text}")
            if suffix:
                # Keep `prefix`'s leading newline + cell marker so the
                # leftover stays a parseable row (otherwise the `|-`
                # splitter swallows the attribution).
                prefix = prefix + " " + suffix.strip()
        parts[idx] = prefix
        found = True
    if not found:
        return [], inner
    return legend_lines, "".join(parts)


def _process_legended_figure(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Focused producer for `LEGENDED_FIGURE` — single-image figure
    whose legend is encoded in regular cells (NOT in a POEM or
    nested-wikitable child; those go to `LEGENDED_FIGURE_CHILD`).

    Four legend-cell sub-shapes share one assembly path:

      * Hanging-indent (ARACHNIDA Fig 26, 78): each entry wrapped in
        a `{{Hi|SIZE|LABEL, text}}` template, packed several per cell
        across columns.  Extracted first (Phase 0) and excised from
        the inner so the remaining phases only see image/caption.
      * Multicol-alternating (ABBEY Fig 5): `|A.||Gateway.||F.||…`
        — `||` delimiter, label-only first chunk → alternating pairs.
      * Multicol-full-entry (ARACHNIDA Fig 7):
        `|«I»oc«/I», Lateral eyes.||VIII, The six…` — `||` delimiter,
        full-entry first chunk → each chunk is one entry.
      * Prose-cell (HYDROMEDUSAE Fig 1): one cell with line-separated
        `«I»a«/I», Hydranth;` entries — `\\n` delimiter, full-entry.

    The producer routes each detected legend region through the same
    chop helper with the appropriate delimiter; the rest of the
    producer treats the resulting entries identically.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if not image_phs:
        return ""
    image_ph = image_phs[0]
    filename = _image_ph_filename(image_ph, inner_registry)
    if not filename:
        return ""

    legend_lines: list[str] = []
    text_cells: list[str] = []

    # Family-scoped normalization: strip pure-decoration layout
    # templates ({{center}}, {{Fs}}, {{em}} spacers, …) so the legend
    # detectors see clean content.  `{{Hi}}` survives — it carries
    # legend-entry boundaries that Phase 0 needs.
    inner = _normalize_icl_markup(inner)

    # Phase 0: single-cell packed legends.
    #   (a) Flowing italic legend — a run of `«I»label«/I», text.`
    #       entries (hi-wrapped and/or bare) in one cell (Fig 3, 31).
    #   (b) Discrete hanging-indent — each `{{Hi}}` is one complete
    #       entry, plain-labelled, across columns (Fig 26, 78).
    # Try the flowing parse first; fall back to discrete `{{Hi}}`.
    flowing_lines, inner = _extract_flowing_italic_legend(
        inner, text_transform)
    if flowing_lines:
        legend_lines.extend(flowing_lines)
    else:
        hi_lines, inner = _extract_hi_legend(inner, text_transform)
        legend_lines.extend(hi_lines)

    cleaned = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    rows = re.split(r"\|-[^\n]*", cleaned)

    # Phase 1: multicol legend rows.  A multicol BLOCK starts when a
    # row matches the strict label-shape regex; subsequent rows that
    # contain `||` (continuation rows whose leading cell is mid-
    # entry text, no label-shape) belong to the same block.  The
    # block ends at the first non-`||` row.  This catches ARACHNIDA
    # Fig 7's column-major shape where 9 rows hold 4 column entries
    # via cross-row continuation.
    multicol_rows: list[str] = []
    other_rows: list[str] = []
    in_block = False
    for row in rows:
        if not row.strip():
            continue
        if _row_has_legend_multicol_cells(row):
            multicol_rows.append(row)
            in_block = True
        elif in_block and ("||" in row or _row_is_single_full_entry(row)):
            # A `||` row continues a multicol block (ARACHNIDA Fig 7);
            # a single full-entry row continues a `rowspan` block where
            # the right column spans two rows (ARACHNIDA Fig 31).
            multicol_rows.append(row)
        else:
            in_block = False
            other_rows.append(row)
    if multicol_rows:
        # Three multicol sub-shapes share the iteration ("walk rows,
        # collect entries column-major"), but differ in cell parsing:
        #
        # * Rowspan-uneven (ARACHNIDA Fig 31): a `rowspan=2` right
        #   column leaves alternate rows with one cell.  Each cell is
        #   a complete entry — collect column-major by cell index.
        # * Full-entry-per-cell with cross-row continuation
        #   (ARACHNIDA Fig 7): an entry can span 3-4 rows of the
        #   same column.  Handled by `_parse_multicol_legend_rows_
        #   column_major` which tracks per-column continuation.
        # * Alternating-pair (ABBEY Fig 5): each row has N/2 (label,
        #   text) pairs, transpose for column-major reading order.
        #   Chop each row, transpose ourselves.
        #
        # Column-major parser returns None on the alternating-pair
        # shape (first cell is label-only, no text), giving us a
        # clean fallback signal.
        if any(re.search(r"rowspan", r, re.IGNORECASE)
               for r in multicol_rows):
            col_pairs = _collect_rowspan_legend(
                multicol_rows, text_transform)
        else:
            col_pairs = _parse_multicol_legend_rows_column_major(
                multicol_rows, text_transform)
        if col_pairs:
            legend_lines.extend(
                f"{lbl}. {text}" for lbl, text in col_pairs)
        else:
            pairs_per_row = [
                _chop_legend_entries(r, "||", text_transform)
                for r in multicol_rows
            ]
            max_cols = max((len(p) for p in pairs_per_row), default=0)
            for col in range(max_cols):
                for row_pairs in pairs_per_row:
                    if col < len(row_pairs):
                        lbl, text = row_pairs[col]
                        legend_lines.append(f"{lbl}. {text}")

    # Phase 2: prose-cell legends and caption/attribution cells.
    for row in other_rows:
        for _sep, _attr, content in split_wiki_row(row):
            if not content.strip():
                continue
            content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "",
                              content).strip()
            if not content:
                continue
            # A cell with ≥3 line-shaped `LABEL.text` entries is the
            # prose-cell legend shape — chop by newline.
            if len(_LEGEND_ROW_PROSE_RE.findall(content)) >= 3:
                pairs = _chop_legend_entries(
                    content, "\n", text_transform)
                legend_lines.extend(f"{lbl}. {text}" for lbl, text in pairs)
                continue
            text_cells.append(content)

    cap_parts, attr_parts, _extra_legend = _extract_figure_components(
        text_cells, inner_registry, text_transform, skip_ph=image_ph)
    if _extra_legend:
        legend_lines.extend(_extra_legend)

    parts = _assemble_figure_parts(
        filename, cap_parts, attr_parts, legend_lines)
    return "\n\n" + "\n\n".join(parts) + "\n\n"


def _process_legended_figure_child(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Focused producer for `LEGENDED_FIGURE_CHILD` — single-image
    figure whose legend lives in a POEM placeholder or a nested
    wikitable child.

    Iteration strategy:

      1. Find image filename from the IMAGE child.
      2. For every non-image child placeholder: harvest legend lines
         from its raw via the appropriate parser
         (`_emit_legend_chunk` for POEM, `_extract_poem_legend` for
         a nested TABLE).  Excise the placeholder from any cell that
         contained it.
      3. Run `_extract_figure_components` on the remaining cells →
         caption + attribution.
      4. Hand to the shared `_assemble_figure_parts`.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if not image_phs:
        return ""
    image_ph = image_phs[0]
    filename = _image_ph_filename(image_ph, inner_registry)
    if not filename:
        return ""

    cleaned = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    rows = re.split(r"\|-[^\n]*", cleaned)

    legend_lines: list[str] = []
    text_cells: list[str] = []
    for row in rows:
        if not row.strip():
            continue
        for _sep, _attr, content in split_wiki_row(row):
            if not content.strip():
                continue
            content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "",
                              content).strip()
            if not content:
                continue
            for ph, lbl in list(inner_registry.labels.items()):
                if ph not in content or ph == image_ph:
                    continue
                if lbl == "POEM":
                    poem_raw = inner_registry.elements[ph][1]
                    _emit_legend_chunk(
                        poem_raw, text_transform, legend_lines)
                    content = content.replace(ph, "")
                elif lbl in TABLE_LABELS:
                    sub_raw = inner_registry.elements[ph][1]
                    legend_lines.extend(_extract_poem_legend(
                        sub_raw, text_transform))
                    content = content.replace(ph, "")
            content = content.strip()
            if content:
                text_cells.append(content)

    cap_parts, attr_parts, _extra_legend = _extract_figure_components(
        text_cells, inner_registry, text_transform, skip_ph=image_ph)
    if _extra_legend:
        legend_lines.extend(_extra_legend)

    parts = _assemble_figure_parts(
        filename, cap_parts, attr_parts, legend_lines)
    return "\n\n" + "\n\n".join(parts) + "\n\n"


def _process_legended_figure_beside(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Focused producer for `LEGENDED_FIGURE_BESIDE` — single-image
    figure whose legend sits in a sibling cell to the image's right,
    separated from the image by ``||`` on the same row.  Canonical
    case: ABBEY Fig 1 (Santa Laura) — image cell + paragraph-
    separated ``A. Gateway.\\n\\nB. Chapels.\\n\\n…`` legend cell.

    The caption typically lives in a subsequent ``colspan``-row.

    Distinct from `LEGENDED_FIGURE` because the legend cell shares
    a row with the image, which requires preserving paragraph-`\\n\\n`
    breaks (`split_wiki_row` collapses them) when parsing legend
    entries.  Parsing the raw row text directly keeps the producer
    simple — one helper does the legend extraction, one helper does
    the caption.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if len(image_phs) != 1:
        return ""
    image_ph = image_phs[0]
    filename = _image_ph_filename(image_ph, inner_registry)
    if not filename:
        return ""

    rows = re.split(r"\|-[^\n]*", inner)

    # Locate the image's row and extract the raw cell text (image
    # cell + sibling-legend cell, newlines intact).
    image_row_idx = next((i for i, r in enumerate(rows)
                           if image_ph in r), None)
    if image_row_idx is None:
        return ""
    image_row = rows[image_row_idx]
    row_lines = [l for l in image_row.split("\n") if l.strip()]
    image_line = next((l for l in row_lines if image_ph in l), None)
    if image_line is None or "||" not in image_line:
        return ""
    li = row_lines.index(image_line)
    cell_lines = [image_line]
    for nxt in row_lines[li + 1:]:
        if nxt.lstrip().startswith("|"):
            break
        cell_lines.append(nxt)
    cell_text = "\n".join(cell_lines).lstrip("|")

    _, entries = _parse_inline_legend_cell(cell_text, text_transform)
    if not entries or not _entries_look_like_legend(entries):
        return ""
    legend_lines = [f"{lbl}. {text}" for lbl, text in entries]

    # Caption: scan subsequent rows for a `colspan`-row containing a
    # Fig./Plate. marker.
    caption = None
    for r in rows[image_row_idx + 1:]:
        c = _extract_caption_from_colspan_row(r, text_transform)
        if c:
            caption = c
            break

    parts = _assemble_figure_parts(
        filename, [caption] if caption else [], [], legend_lines)
    return "\n\n" + "\n\n".join(parts) + "\n\n"


def _process_simple_plate(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Producer for `UNPAIRED_FIGURE_GROUP` — any multi-image figure
    layout (formerly `SIMPLE_PLATE`; the grid/non-grid split was dropped
    because this producer is total over both — it bundles equal-or-more
    than the generic passthrough in every case).

    The classifier predicate guarantees ≥2 IMAGE children and no
    data-table header signal.  Images may be arranged:

      * Vertical-stack: each image alone in its own row, caption
        rows immediately following until the next image-row
        (BIRD, AMPHITHEATRE PLATE I, MUSCULAR SYSTEM Figs 7/8).
      * Parallel-row multi-row: 2+ images in a header row, caption
        rows below split by column index (SHIP PLATE X, LEAF
        Figs 36-41).
      * Mixed: a sequence of image-rows where each row is itself a
        side-by-side or single-image group; content rows between
        image-rows belong to the group above.

    Iteration:
      1. Locate each image's row.  Group images by row.
      2. Each group "owns" the content rows up to the next group.
      3. Single-image group → vertical slice (all content cells).
         Multi-image group → column-slice each image owns the cells
         at its column index in subsequent rows.
      4. Per image: hand the owned cells to shared
         `_extract_figure_components` + `_assemble_figure_parts`.
    """
    if inner_registry is None:
        return ""
    image_phs = [ph for ph, lbl in inner_registry.labels.items()
                 if lbl == "IMAGE"]
    if len(image_phs) < 2:
        return ""

    cleaned = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    # Strip leading row-separator if any, then split on `\n|-` runs.
    inner_stripped = re.sub(r"^\s*\|-+[^\n]*\n", "", cleaned)
    rows = re.split(r"\n(?:\s*\|-+[^\n]*\n)+", inner_stripped)

    # Per-image row index.
    img_row_of: dict[str, int] = {}
    for ph in image_phs:
        for i, r in enumerate(rows):
            if ph in r:
                img_row_of[ph] = i
                break
    if len(img_row_of) != len(image_phs):
        return ""  # malformed — let LAYOUT_WRAPPER fall-through handle

    # Group images by their row index.
    groups: dict[int, list[str]] = {}
    for ph in image_phs:
        groups.setdefault(img_row_of[ph], []).append(ph)
    sorted_group_rows = sorted(groups.keys())

    output_parts: list[str] = []
    for i, img_row_idx in enumerate(sorted_group_rows):
        phs_in_group = groups[img_row_idx]
        next_row = (sorted_group_rows[i + 1]
                    if i + 1 < len(sorted_group_rows)
                    else len(rows))
        content_rows = list(range(img_row_idx + 1, next_row))

        if len(phs_in_group) == 1:
            # Vertical slice: all content cells belong to this image.
            ph = phs_in_group[0]
            filename = _image_ph_filename(ph, inner_registry)
            if not filename:
                continue
            cells_text: list[str] = []
            for r_idx in content_rows:
                for _sep, _attr, content in split_wiki_row(rows[r_idx]):
                    if content.strip():
                        cells_text.append(content)
            cap, attr, legend = _extract_figure_components(
                cells_text, inner_registry, text_transform, skip_ph=ph)
            output_parts.extend(_assemble_figure_parts(
                filename, cap, attr, legend))
        else:
            # Column slice: each image owns the cells at its column
            # index in subsequent rows.
            img_row_cells = list(split_wiki_row(rows[img_row_idx]))
            image_col_of: dict[str, int] = {}
            for col_idx, (_sep, _attr, content) in enumerate(
                    img_row_cells):
                for ph in phs_in_group:
                    if ph in content:
                        image_col_of[ph] = col_idx
            if len(image_col_of) != len(phs_in_group):
                continue  # malformed group — skip
            for ph in sorted(phs_in_group,
                              key=lambda p: image_col_of[p]):
                filename = _image_ph_filename(ph, inner_registry)
                if not filename:
                    continue
                col_idx = image_col_of[ph]
                col_cells: list[str] = []
                for r_idx in content_rows:
                    cells = list(split_wiki_row(rows[r_idx]))
                    if col_idx < len(cells):
                        _sep, _attr, cell_content = cells[col_idx]
                        col_cells.append(cell_content)
                cap, attr, legend = _extract_figure_components(
                    col_cells, inner_registry, text_transform,
                    skip_ph=ph)
                output_parts.extend(_assemble_figure_parts(
                    filename, cap, attr, legend))

    if not output_parts:
        return ""
    return "\n\n" + "\n\n".join(output_parts) + "\n\n"


def _unwrap_layout_table(inner: str, text_transform,
                         inner_registry: ElementRegistry | None = None) -> str:
    """Unwrap a layout table to sequential content.

    Extracts cell content row by row, joining each cell's content
    as a separate block.  Child placeholders (images, nested tables)
    pass through and get substituted by the caller.

    Special case: if the table contains exactly one image placeholder
    + one or more caption rows, bundle them into a single
    {{IMG:filename|caption}} so the figure renders with its caption
    inside (avoids the duplicate-caption-paragraph regression seen in
    SEWING MACHINES Fig. 2 / ACACIA Senegal).
    """
    # First try the explicit image-layout subclasses (INLINE_LEGEND /
    # MULTICOL_LEGEND / POEM_LEGEND). These have dedicated handlers
    # that emit a structured `{{LEGEND:…}LEGEND}` block alongside the
    # image marker, which the generic unwrap cannot do. On no-match,
    # fall through to the legacy generic logic below.
    subclassed = _try_image_layout_subclass(
        inner, text_transform, inner_registry)
    if subclassed is not None:
        return subclassed

    inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)

    raw_rows = re.split(r"\|-[^\n]*", inner)
    parts = []
    for raw_row in raw_rows:
        # Collect all content: standalone placeholders (child elements
        # appearing in the row without a leading `|`) AND attribute-
        # stripped cell content via the shared row splitter.
        row_content: list[str] = []

        # Pre-pass: pick up standalone placeholder lines.  A layout-
        # wrapper sometimes holds a child element (image, nested table)
        # on its own line without the surrounding `|` cell syntax —
        # those would never match `split_wiki_row`'s `^|` extraction,
        # so we grab them here first.
        pre_pass_phs: set[str] = set()
        for ln in raw_row.split("\n"):
            stripped = ln.strip()
            if _PH in stripped and stripped.startswith(_PH):
                row_content.append(stripped)
                pre_pass_phs.add(stripped)

        for sep, attr_part, content in split_wiki_row(raw_row):
            if not content:
                continue
            # Drop leftover {{Ts|…}} cell-styling templates (same logic
            # as `_process_table`'s `_extract_cells`).
            content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", content).strip()
            if not content:
                continue
            # ``split_wiki_row`` walks `\n|` as cell separators, which
            # picks up the same standalone-placeholder lines the
            # pre-pass already captured (LEAF Figs 3-4: the outer
            # wrapper's cells each contain a single nested-table
            # placeholder on its own line).  Skip the duplicate so
            # downstream substitution doesn't emit the child element's
            # processed output twice.
            if content in pre_pass_phs:
                continue
            row_content.append(content)

        for c in row_content:
            # Placeholders (child elements) must pass through untouched.
            # Push each placeholder AND each non-empty surrounding text
            # chunk as a SEPARATE `parts` entry — this is what lets the
            # image+caption bundling below fire when source put the
            # image and its caption in the *same* cell separated by
            # `<br>` (ABERRATION ``|[[File:…|Fig. 2]]<br>{{csc|Fig.
            # 2.}}|``: continuation merge produces one cell containing
            # placeholder+caption-text, and emitting them joined would
            # bypass the bundling and leak ``«SC»Fig. 2.«/SC»`` as
            # duplicate text after the figure).
            if _PH in c:
                ph_re = re.compile(
                    re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+"
                    + re.escape(_PH))
                last = 0
                for m in ph_re.finditer(c):
                    if m.start() > last:
                        chunk = c[last:m.start()]
                        if chunk.strip():
                            parts.append(text_transform(chunk).strip())
                    parts.append(m.group(0))
                    last = m.end()
                if last < len(c):
                    tail = c[last:]
                    if tail.strip():
                        parts.append(text_transform(tail).strip())
            else:
                content = text_transform(c)
                if content.strip():
                    parts.append(content.strip())

    # Image + caption bundling: when the unwrap produced a single
    # IMAGE placeholder plus one or more text parts, fold the first
    # text part into the IMG marker as its caption. Reuses the same
    # caption-cleaning step _process_image applies, so the caption
    # comes out as plain text (no «I»/«SC» leak) like any other IMG.
    if inner_registry is not None and len(parts) >= 2:
        ph_re = re.compile(re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH))
        image_indices = [
            i for i, p in enumerate(parts)
            if ph_re.fullmatch(p.strip())
            and inner_registry.labels.get(p.strip()) == "IMAGE"
        ]
        text_indices = [
            i for i, p in enumerate(parts)
            if not ph_re.fullmatch(p.strip())
            and p.strip()
        ]
        if len(image_indices) == 1 and text_indices:
            img_idx = image_indices[0]
            ph_id = parts[img_idx].strip()
            etype, eraw = inner_registry.elements[ph_id]
            # Case-insensitive: wikitext uses `[[File:…]]`, `[[Image:…]]`,
            # and (rarely) lowercase `[[image:…]]` (ABBEY vol 1 p. 44).
            fname_m = re.match(
                r"\[\[(?:File|Image):([^\]|]+)", eraw, re.IGNORECASE)
            # If the IMAGE element's raw extends *beyond* the file
            # link (it captured a following `{{sc|Fig}}. N.—…` caption
            # block at element-extraction time — ROOFS Fig. 4 with
            # three caption segments a/b/c separated by `<br>`), the
            # image already has a rich multi-segment caption.  Don't
            # let bundling overwrite that with the in-cell text that
            # happens to come after; let the placeholder substitute
            # normally and the bundled text become a trailing sibling
            # paragraph.
            link_only = bool(re.match(
                r"\[\[(?:File|Image):[^\]]+\]\]\s*$",
                eraw.strip(), re.IGNORECASE | re.DOTALL,
            ))
            if fname_m and link_only:
                filename = fname_m.group(1).strip()
                caption_idx = next(
                    (i for i in text_indices if i > img_idx), None)
                if caption_idx is not None:
                    # Caption is already through text_transform (cells
                    # were processed in _extract_cells). Apply the
                    # same _clean_text used by _process_image to
                    # strip any «I»/«SC»/etc. markers and produce
                    # plain figcaption text.
                    caption = _clean_text(parts[caption_idx].strip())
                    # Fold trailing simple-text table placeholders into
                    # the caption. Country-map layouts (UNITED STATES,
                    # IRELAND, SCOTLAND …) put the Perthes attribution
                    # in one cell and a small nested table with the
                    # copyright notice in the next cell — both are part
                    # of the caption, not a separate block underneath
                    # the figure.
                    trailing_parts: list[str] = []
                    for i in range(len(parts)):
                        if i == img_idx or i == caption_idx:
                            continue
                        p = parts[i].strip()
                        if not p:
                            continue
                        extra_text = None
                        if ph_re.fullmatch(p) and inner_registry is not None:
                            t_etype, t_raw = inner_registry.elements.get(
                                p, ("", ""))
                            if t_etype == "TABLE":
                                extra_text = _simple_table_text(t_raw)
                        if extra_text:
                            # _simple_table_text returns raw wikitext —
                            # run text_transform to convert ''italic'' →
                            # «I»…«/I», then _clean_text for the plain
                            # figcaption form (matches how caption_idx
                            # is processed above).
                            extra_text = _clean_text(
                                text_transform(extra_text).strip())
                            caption = (
                                f"{caption} {extra_text}".strip()
                                if caption else extra_text
                            )
                        else:
                            trailing_parts.append(parts[i])

                    if caption:
                        img_marker = build_img_marker(filename, caption)
                    else:
                        img_marker = f"{{{{IMG:{filename}}}}}"
                    # Preserve remaining trailing parts (legend tables,
                    # etc.) as siblings after the figure. Without this
                    # the St Gall ground-plan legend on Abbey_3 would be
                    # dropped entirely when bundling fired.
                    if trailing_parts:
                        return "\n\n".join([img_marker, *trailing_parts])
                    return img_marker

    # Single-POEM-placeholder unwrap: a wikitable whose only content
    # is a <poem> block (the {|…|} analogue of DONNE's centred-verse
    # <table>).  Flank with blank lines so the downstream paragraph
    # splitter treats the resulting {{VERSE:…}VERSE} as a standalone
    # paragraph and the viewer renders <blockquote class="verse">
    # (set off from prose like BLANK VERSE), not an inline span.
    if (
        len(parts) == 1 and inner_registry is not None
        and parts[0].strip() in {
            k for k, label in inner_registry.labels.items()
            if label == "POEM"
        }
    ):
        return "\n\n" + parts[0] + "\n\n"

    return "\n\n".join(parts)


_LEGEND_LABEL = (
    r"[A-Za-z0-9](?:[A-Za-z0-9₁₂₃.\-]*[A-Za-z0-9₁₂₃])?")
_LEGEND_ENTRY_RE = re.compile(
    # Label terminator may be `.` OR `,` — HEXAPODA Fig. 18 Springtail
    # uses `1, Ocular segment.` form inside `<poem>` blocks.
    r"^\s*(" + _LEGEND_LABEL +
    r"(?:\s*,\s*" + _LEGEND_LABEL + r")*)[.,]\s+(.*\S)\s*$")

_MULTICOL_FULL_ENTRY_RE = re.compile(
    # Label: one or more alphanumeric tokens, optionally with `to`-range
    # form (`VIII to XIII`) for ARACHNIDA Fig. 7 / Fig. 32 cells, then
    # comma-or-period separator + text.  Originally period-only; the
    # comma form covers ARACHNIDA Fig. 1 (`LAP, Left anterior process.`)
    # and similar plates throughout the corpus.
    r"^\s*"
    r"([A-Za-z0-9]+(?:\s+to\s+[A-Za-z0-9]+)?"
    r"(?:\s*,\s*[A-Za-z0-9]+(?:\s+to\s+[A-Za-z0-9]+)?)*)"
    r"[.,]\s+(.+\S)\s*$")
_MULTICOL_FULL_ENTRY_ITALIC_RE = re.compile(
    # Italic label optionally with a superscript/subscript suffix
    # (HTML `<sup>1</sup>` form or Unicode `¹`/`₁` after
    # `_convert_inline_sub_sup` runs).  Also accepts an `X to Y`
    # range form (ARACHNIDA Fig. 32 `''br''¹ to ''br''⁵, Branchial
    # appendages…`).
    r"^\s*("
    r"«I»[^«]+«/I»"
    r"(?:<su[bp]>[^<]+</su[bp]>|[¹²³⁰-₉]+)?"
    r"(?:\s+to\s+«I»[^«]+«/I»"
    r"(?:<su[bp]>[^<]+</su[bp]>|[¹²³⁰-₉]+)?)?"
    r")"
    r"\s*[.,]\s+(.+\S)\s*$"
)

_LEGEND_LABEL_STRICT_RE = re.compile(
    r"^" + _LEGEND_LABEL +
    r"(?:\s*,\s*" + _LEGEND_LABEL + r")*$")
_LEGEND_LABEL_MULTIWORD_RE = re.compile(
    r"^[A-Za-z][A-Za-z]{0,5}(?:[.,]?\s+[A-Za-z][A-Za-z]{0,5}){1,3}\.?$")

_SUPERSCRIPT_TO_ASCII = {
    0x2070: "0", 0x00B9: "1", 0x00B2: "2", 0x00B3: "3",
    0x2074: "4", 0x2075: "5", 0x2076: "6", 0x2077: "7",
    0x2078: "8", 0x2079: "9",
}
_SUBSCRIPT_TO_ASCII = {
    0x2080: "0", 0x2081: "1", 0x2082: "2", 0x2083: "3",
    0x2084: "4", 0x2085: "5", 0x2086: "6", 0x2087: "7",
    0x2088: "8", 0x2089: "9",
}
_PRIMES = (0x2032, 0x2033, 0x2034, 0x2035, 0x2036, 0x2037,
           0x02B9, 0x02BA, 0x02BC)
_LIGATURE_FOLD = {
    0x00C6: "AE", 0x00E6: "ae",  # Æ æ
    0x0152: "OE", 0x0153: "oe",  # Œ œ
}

_LEGEND_LABEL_LENIENT_RE = re.compile(
    # Short, starts+ends with alphanumeric, allows spaces, periods,
    # commas, hyphens, ampersand (HEXAPODA Fig. 14 `T8 &c`).  Capped at
    # 15 chars so it can't swallow sentence fragments.
    r"^[A-Za-z0-9](?=.{0,14}$)[A-Za-z0-9 &,.\-]*[A-Za-z0-9.]$")

_CELL_ATTR_PREFIX_RE = re.compile(
    # Attribute-value may NOT contain `{` / `}` — otherwise the greedy
    # `[^"|\n]*` slurps across a following `{{Ts|…}}` styling template
    # and mis-consumes it as an attr value, which then breaks cap-row
    # detection (`colspan=2 {{Ts|ac}}|{{sc|Fig. 54}}…` is a real
    # Mosque of Amr example).
    r"^(?:\s*(?:colspan|rowspan|align|valign|style|width|class|"
    r"cellpadding|cellspacing|bgcolor|height|nowrap|border|scope|id)"
    r"\s*=\s*\"?[^\"|\n{}]*\"?\s*)+\|",
    re.IGNORECASE,
)

_FIG_CAPTION_START_RE = re.compile(
    # Accepts leading italic `''`, smallcaps `{{sc|` / `{{csc|`, or
    # bare `Fig.` / `Plate.` text.  HYDROMEDUSAE sources use ``{{sc|``
    # variants; DIFFERENCES Fig 1's source uses ``{{csc|`` (centred
    # smallcaps) for the caption row — without `csc` in the prefix the
    # row failed _looks_like_caption, fell to the inline-search path,
    # and the ``{{csc|`` opener got captured as "attribution" and
    # folded into the IMG caption as a stray ``(.)``.
    r"^\s*(?:''|\{\{\s*(?:sc|csc)\s*\|\s*)*(?:Fig|Plate)s?\.?",
    re.IGNORECASE,
)

_FIG_CAPTION_INLINE_RE = re.compile(
    r"(?:''|\{\{\s*(?:sc|csc)\s*\|\s*)*"
    r"(?:Fig|Plate)s?[\s.}]{1,10}\d",
    re.IGNORECASE,
)

_PROSE_ENTRY_SPLIT_RE = re.compile(
    r"(?=(?:^|\. |; |\s)(?:[IVX]+|[A-Za-z][A-Za-z0-9.]{0,4})[,.] )")

