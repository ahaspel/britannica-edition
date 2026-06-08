"""Flavor autodetection + decomposition shape for the shared table leaf.

`produce_table_rows` is the single row/cell split every table producer shares.
These tests pin its `{|` vs `<table>` flavor autodetection (`flavor=None`) and
the `(tag, colspan, rowspan, content, styles)` cell tuple it returns.

(The old form-chooser `assemble_table_marker` + its `{{TABLE}}`-marker emitter
`assemble_wiki_marker` were deleted as dead code: the live producer always
assembles `«HTMLTABLE»` via `assemble_html_rows`, so the align-only `{{TABLE}}`
form had no producer left.)
"""
from britannica.pipeline.stages.elements._table_decompose import (
    produce_table_rows,
)


PLAIN = (
    "<tr><td>Region</td><td>Population</td></tr>"
    "<tr><td>North</td><td>1000</td></tr>"
    "<tr><td>South</td><td>2000</td></tr>"
)


class TestFlavorAutodetect:
    def test_html_detected(self):
        # `<tr>`/`<td>` with no `{|` → `flavor=None` auto-detects HTML.
        _c, parsed, _hh, _hs = produce_table_rows(PLAIN)
        assert len(parsed) == 3

    def test_wiki_detected(self):
        inner = "|-\n| a || b\n|-\n| c || d"
        _c, parsed, _hh, _hs = produce_table_rows(inner)
        # Cell tuple is (tag, colspan, rowspan, content, styles) — content at [3].
        assert [[cell[3] for cell in cells] for _row_attr, cells in parsed] == [
            ["a", "b"], ["c", "d"],
        ]
