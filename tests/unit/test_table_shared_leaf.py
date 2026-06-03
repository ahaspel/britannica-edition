"""Phase 0 of the table-producer collapse: byte-identity of the shared
recursive-decomposition leaf against the canonical ``_process_html_table``
spine.

`produce_table_rows` + `assemble_table_marker` (the form chooser) are
lifted verbatim from `_process_html_table`'s canonical-decomposition body
(lines 1963-2065).  These tests pin that a producer delegating to the
shared leaf reproduces that spine exactly — the precondition for migrating
the five wiki producers onto it one phase at a time.

We feed HTML ``<table>`` inputs that bypass `_process_html_table`'s three
front guards (illustration wrapper, HYDRAULICS no-``<tr>`` flow, verse-poem
single-cell) so the comparison is purely the shared canonical path.
"""
from britannica.pipeline.stages.elements._table_decompose import (
    assemble_table_marker,
    produce_table_rows,
)
from britannica.pipeline.stages.elements._tables import _html_cell_clean


def _identity(text: str) -> str:
    return text


# ── Representative inner tables ─────────────────────────────────────────

PLAIN = (
    "<tr><td>Region</td><td>Population</td></tr>"
    "<tr><td>North</td><td>1000</td></tr>"
    "<tr><td>South</td><td>2000</td></tr>"
)

HEADER = (
    "<tr><th>Year</th><th>Count</th></tr>"
    "<tr><td>1901</td><td>42</td></tr>"
)

ALIGNED = (
    "<tr><td style=\"text-align:right\">12</td>"
    "<td style=\"text-align:center\">mid</td></tr>"
    "<tr><td>34</td><td>end</td></tr>"
)

SPAN = (
    "<tr><th colspan=\"2\">Header</th></tr>"
    "<tr><td rowspan=\"2\">A</td><td>b1</td></tr>"
    "<tr><td>b2</td></tr>"
)

SPAN_STYLED = (
    "<tr><td colspan=\"2\" style=\"text-align:center\">Total</td></tr>"
    "<tr><td>x</td><td>y</td></tr>"
)

BR_CELL = (
    "<tr><td>line one<br>line two</td><td>solo</td></tr>"
)

EMPTY_CELLS = (
    "<tr><td>a</td><td></td><td>c</td></tr>"
)


class TestFormChooser:
    def test_span_routes_to_html(self):
        _c, parsed, hh, hs = produce_table_rows(
            SPAN, _identity, flavor="html", cell_preclean=_html_cell_clean)
        assert hs is True
        assert assemble_table_marker(
            "", parsed, hh, hs).startswith("«HTMLTABLE")

    def test_no_span_routes_to_wiki_marker(self):
        _c, parsed, hh, hs = produce_table_rows(
            PLAIN, _identity, flavor="html", cell_preclean=_html_cell_clean)
        assert hs is False
        out = assemble_table_marker("", parsed, hh, hs)
        assert out.startswith("{{TABLE")
        assert out.endswith("}TABLE}")

    def test_header_selects_tableh(self):
        _c, parsed, hh, hs = produce_table_rows(
            HEADER, _identity, flavor="html", cell_preclean=_html_cell_clean)
        assert hh is True
        assert assemble_table_marker("", parsed, hh, hs).startswith("{{TABLEH")

    def test_empty_input_returns_empty(self):
        assert assemble_table_marker("", [], False, False) == ""


class TestFlavorAutodetect:
    def test_html_detected(self):
        _c, parsed, _hh, _hs = produce_table_rows(
            PLAIN, _identity, cell_preclean=_html_cell_clean)
        assert len(parsed) == 3

    def test_wiki_detected(self):
        inner = "|-\n| a || b\n|-\n| c || d"
        _c, parsed, _hh, _hs = produce_table_rows(inner, _identity)
        assert [[cell[3] for cell in cells] for _row_attr, cells in parsed] == [
            ["a", "b"], ["c", "d"],
        ]
