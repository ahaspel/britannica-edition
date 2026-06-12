"""Flavor autodetection + decomposition shape for the table leaf.

`produce_table` recurses the grid to the ground and emits in one descent — both
`{|` and `<table>` syntaxes recognized by `recognize_table`, no flavor branch.
These tests pin that autodetection and the cell decomposition via the emitted
`«HTMLTABLE»` marker.  `recurse` is identity here: a cell's content is its own
producer's problem, and the real leaf recursion is exercised by the snapshot
suite — here we only check the structural chop.
"""
from britannica.pipeline.stages.elements._table_decompose import produce_table


def _ident(s: str) -> str:
    return s


PLAIN = (
    "<tr><td>Region</td><td>Population</td></tr>"
    "<tr><td>North</td><td>1000</td></tr>"
    "<tr><td>South</td><td>2000</td></tr>"
)


class TestFlavorAutodetect:
    def test_html_detected(self):
        # `<tr>`/`<td>` with no `{|` → recognized as HTML; three rows.
        _caption, marker = produce_table(PLAIN, _ident)
        assert marker.count("<tr>") == 3
        assert "<td>Region</td>" in marker

    def test_wiki_detected(self):
        inner = "|-\n| a || b\n|-\n| c || d"
        _caption, marker = produce_table(inner, _ident)
        assert "<td>a</td><td>b</td>" in marker
        assert "<td>c</td><td>d</td>" in marker
