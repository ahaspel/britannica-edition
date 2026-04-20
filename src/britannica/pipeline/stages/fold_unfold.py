"""Unfold 'folded' wikitable rows.

A folded row is one physical ``|-`` row whose cells each hold N logical
values stacked with ``<br>`` — a pattern used in EB1911 for dense data
tables (ATMOSPHERIC ELECTRICITY, BEER analyses, ATMOSPHERE hourly
readings). Downstream table processors collapse ``<br>`` to space,
turning what should be an N-row table into one giant row with all
values concatenated. This module rewrites folded rows as N real rows
so the ordinary table pipeline sees a well-formed table.

Boundary tests applied per wikitable (``{| … |}``):

  1. Per-row: a row is ``foldable`` iff every cell splits into exactly
     1 or N ``<br>``-parts (for some N ≥ 2), and ≥ 2 cells split into N.
     Any cell with a split count other than 1 or N means the fold
     interpretation is inconsistent — reject.

  2. Per-table: the table must have exactly ONE foldable row, and that
     row must be ≥ half of the table's non-empty ``|-``-delimited
     segments. Multiple candidates indicate intra-cell line-wrap
     formatting repeating across siblings (e.g. ``"1500°F<br>(815.5°C)"``
     unit conversions); a lone candidate in a big table is a quirky
     multi-line cell.

The two tests are purely structural — no frequency tuning thresholds —
and together they keep false positives out of the unfolder's path.
"""
from __future__ import annotations

import re

_TRAILING_BR_RE = re.compile(r"(?:\s*<br\s*/?>\s*)+$", re.IGNORECASE)
_BR_SPLIT_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TABLE_RE = re.compile(r"\{\|[\s\S]*?\n\|\}", re.MULTILINE)
_ROW_SEP_RE = re.compile(r"^\|-[^\n]*$", re.MULTILINE)


def _split_count(cell_content: str) -> int:
    """Number of ``<br>``-separated values in the cell, ignoring any
    purely-trailing ``<br>`` (authors often add one for visual padding —
    it must not add a phantom empty value)."""
    trimmed = _TRAILING_BR_RE.sub("", cell_content)
    return len(_BR_SPLIT_RE.findall(trimmed)) + 1


def _parse_row_cells(row_text: str) -> list[tuple[str, str, str]]:
    """Return list of (sigil, attrs, content) for each cell in the row.

    Wikitable cell syntax:
      ``| content``               → ("|", "", "content")
      ``| attrs | content``       → ("|", "attrs", "content")
      ``| a | a || b | b``        → two cells, ``||`` on one line
      ``! header``                → ("!", "", "header")
    Caption lines (``|+``) are ignored; all other leading characters
    are rejected.
    """
    cells: list[tuple[str, str, str]] = []
    for line in row_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("|+"):
            continue
        if stripped == "|}":
            continue  # table closer, not a cell
        if not (stripped.startswith("|") or stripped.startswith("!")):
            continue
        sigil = stripped[0]
        body = stripped[1:]
        # Protect pipes inside {{…}} templates and [[…]] links so
        # they don't get treated as attr/content separators.
        body = re.sub(r"\{\{[^}]*\}\}",
                      lambda m: m.group(0).replace("|", "\x04"), body)
        body = re.sub(r"\[\[[^\]]*\]\]",
                      lambda m: m.group(0).replace("|", "\x04"), body)
        sep = "!!" if sigil == "!" else "||"
        for chunk in body.split(sep):
            if "|" in chunk:
                attrs, _, content = chunk.rpartition("|")
            else:
                attrs, content = "", chunk
            attrs = attrs.replace("\x04", "|")
            content = content.replace("\x04", "|")
            cells.append((sigil, attrs, content))
    return cells


def _row_fold_n(cells: list[tuple[str, str, str]]) -> int | None:
    """Return N (the fold arity) if the row is structurally foldable,
    else None. See module docstring for the structural criteria."""
    if not cells:
        return None
    splits = [_split_count(c[2]) for c in cells]
    n = max(splits)
    if n < 2:
        return None
    if any(s != 1 and s != n for s in splits):
        return None
    if sum(1 for s in splits if s == n) < 2:
        return None
    return n


def _unfold_cells(cells: list[tuple[str, str, str]], n: int) -> list[str]:
    """Return a list of N wikitext row bodies (each a multi-line string
    starting with ``|``/``!`` cell lines, no ``|-`` prefix).

    A cell with split_count == 1 is constant and replicates across all
    N rows. A cell with split_count == N distributes its ``<br>``-parts
    one per row.
    """
    cell_parts: list[tuple[str, str, list[str]]] = []
    for sigil, attrs, content in cells:
        trimmed = _TRAILING_BR_RE.sub("", content)
        parts = _BR_SPLIT_RE.split(trimmed)
        if len(parts) == 1:
            # Constant cell — replicate content in every unfolded row.
            parts = [content] * n
        cell_parts.append((sigil, attrs, parts))

    rows: list[str] = []
    for i in range(n):
        lines: list[str] = []
        for sigil, attrs, parts in cell_parts:
            part = parts[i].strip() if i < len(parts) else ""
            if attrs:
                lines.append(f"{sigil}{attrs}|{part}")
            else:
                lines.append(f"{sigil}{part}")
        rows.append("\n".join(lines))
    return rows


_IMAGE_REF_RE = re.compile(
    r"\[\[(?:File|Image):", re.IGNORECASE)


def _unfold_table(table_wt: str) -> str:
    """Rewrite one ``{| … |}`` if it has exactly one folded row that
    dominates the table; otherwise return the table unchanged."""
    # Skip image-layout tables. If any row contains an image reference,
    # the table is a figure layout (images + captions) and any
    # multi-<br> caption row is NOT a fold — it's a single caption with
    # line breaks. Unfolding would shred the caption into bogus rows.
    if _IMAGE_REF_RE.search(table_wt):
        return table_wt
    sep_spans = [m.span() for m in _ROW_SEP_RE.finditer(table_wt)]
    if not sep_spans:
        return table_wt

    # Segments: [pre-first-sep, post-sep-1, post-sep-2, ...]. The pre
    # segment holds the ``{|`` opener line and any pre-row content; we
    # skip it when scanning for data rows.
    pre = table_wt[: sep_spans[0][0]]
    segments: list[tuple[str, str]] = []  # (sep_text, body_text)
    for i, span in enumerate(sep_spans):
        sep_text = table_wt[span[0]: span[1]]
        body_end = sep_spans[i + 1][0] if i + 1 < len(sep_spans) else len(table_wt)
        body = table_wt[span[1]: body_end]
        segments.append((sep_text, body))

    # Scan segments for fold candidates.
    nonempty_segs = 0
    candidate_idx = -1
    candidate_n = 0
    candidate_cells: list[tuple[str, str, str]] = []
    for i, (_, body) in enumerate(segments):
        cells = _parse_row_cells(body)
        if not cells:
            continue
        nonempty_segs += 1
        n = _row_fold_n(cells)
        if n is not None:
            if candidate_idx != -1:
                # > 1 candidate → formatting, not fold
                return table_wt
            candidate_idx = i
            candidate_n = n
            candidate_cells = cells

    if candidate_idx == -1:
        return table_wt
    if candidate_n < 2:
        return table_wt
    if 1 * 2 < nonempty_segs:  # candidate must be ≥ half of data rows
        return table_wt

    # Separate the fold body from any tail content (the ``|}`` closer
    # lives inside the final segment).
    orig_sep, orig_body = segments[candidate_idx]
    # Find the portion of body that we've been treating as row content.
    # _parse_row_cells reads lines; the "body" text actually includes
    # everything up to the next |- (or EOF). To reassemble we keep
    # trailing whitespace and any non-cell lines (e.g. ``|}`` on the
    # last segment).
    body_lines = orig_body.split("\n")
    cell_line_indices = set()
    for idx, line in enumerate(body_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("|+"):
            continue
        if stripped.startswith("|") or stripped.startswith("!"):
            # Exclude ``|}`` closer
            if stripped == "|}":
                continue
            cell_line_indices.add(idx)
    if not cell_line_indices:
        return table_wt
    first_cell = min(cell_line_indices)
    last_cell = max(cell_line_indices)
    before = "\n".join(body_lines[:first_cell])
    after = "\n".join(body_lines[last_cell + 1:])

    unfolded_bodies = _unfold_cells(candidate_cells, candidate_n)

    # Reassemble: pre segments unchanged, splice in N rows at candidate,
    # post segments unchanged.
    out_parts: list[str] = [pre]
    for i, (sep, body) in enumerate(segments):
        if i == candidate_idx:
            for k, uf_body in enumerate(unfolded_bodies):
                s = sep if k == 0 else "|-"
                out_parts.append(s)
                if k == 0 and before.strip():
                    out_parts.append("\n" + before + "\n")
                else:
                    out_parts.append("\n")
                out_parts.append(uf_body)
                if k == len(unfolded_bodies) - 1 and after.strip():
                    out_parts.append("\n" + after)
                else:
                    out_parts.append("\n")
        else:
            out_parts.append(sep)
            out_parts.append(body)
    return "".join(out_parts)


def unfold_folded_rows(wikitext: str) -> str:
    """Top-level entry point: rewrite every folded wikitable in the text.

    No-op for text containing no ``{| … |}`` tables or no folded rows.
    Safe to call on arbitrary wikitext.
    """
    if "{|" not in wikitext or "<br" not in wikitext:
        return wikitext
    return _TABLE_RE.sub(lambda m: _unfold_table(m.group(0)), wikitext)
