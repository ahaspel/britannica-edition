"""CHEM family producers and predicates.

Today: the inline-CHEM family covers ``CHEM_DUAL`` (a ``{{dual line|…}}``
whose content carries element-formula clusters — `C{{sub|6}}H{{sub|5}}`
/ `Fe{{sub|2}}O{{sub|3}}` / etc.).  Block-level CHEM (``CHEMISTRY_LAYOUT``
for tables) lives in ``_tables.py`` for historical reasons; this module
is the home for inline chem work going forward.

Predicate:
  * ``is_chem_dual_line(inner_text)`` — looks at the dual_line's args
    after stripping the template-name prefix; returns True iff any arg
    is a molecular formula by the same `_is_chem_formula` test the
    block-level classifier uses for `CHEMISTRY_LAYOUT`.

Producer:
  * ``_process_chem_dual_line(inner, text_transform)`` — initially
    byte-identical with `_process_dual_line` (renders `A<br>B`).
    Lives here so future chem-specific work (formula validation,
    structural-formula layout, element linking) has a single home.
"""
from __future__ import annotations

import re

from britannica.pipeline.stages.elements._dual_line import (
    _process_dual_line, _split_top_level_pipe)
from britannica.pipeline.stages.elements._tables import (
    _chem_normalize, _is_chem_formula)


_DUAL_LINE_NAME_PREFIX_RE = re.compile(
    r"^\s*dual\s+line\s*\|", re.IGNORECASE)


def is_chem_dual_line(inner_text: str) -> bool:
    """True iff any pipe-arg of the dual_line is a molecular formula.

    Uses the same element-aware test (`_is_chem_formula`) the table
    classifier uses for `CHEMISTRY_LAYOUT` — keeping the chem domain
    knowledge (periodic table + formula grammar) in one place.

    For each top-level pipe-separated arg, normalize away subscript
    markup / templates / non-breaking spaces / `·` combiners, then
    split on chem-reaction-style operators (`= + → ⟶`) — if any
    operand parses as a molecular formula with H/O/N, the dual_line
    is chem-shaped.
    """
    m = _DUAL_LINE_NAME_PREFIX_RE.match(inner_text)
    body = inner_text[m.end():] if m else inner_text
    parts = _split_top_level_pipe(body)
    if parts and parts[0].lstrip().lower().startswith("style="):
        parts = parts[1:]
    for p in parts:
        normalized = _chem_normalize(p.strip())
        # Match the operand split used by `_chem_row_is_reaction`.
        operands = [o.strip(" .,;:")
                    for o in re.split(r"[=＝→⟶+]", normalized)
                    if o.strip(" .,;:")]
        for op in operands:
            if _is_chem_formula(op.replace(" ", "")):
                return True
    return False


def _process_chem_dual_line(inner: str, text_transform) -> str:
    """Render a CHEM_DUAL element.

    Initially byte-identical with `_process_dual_line` (the shared
    layout producer).  Lives here so future chem-specific rendering
    (formula spacing, element linking, balance validation) has its
    natural home — the chem family owns its chem-shaped dual_lines
    even when the rendering hasn't specialized yet.
    """
    return _process_dual_line(inner, text_transform)
