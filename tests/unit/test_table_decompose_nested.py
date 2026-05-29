"""Step A of the flat-walker move: producer-owned recursion for nested
wikitables.

These tests feed RAW nested-table bytes directly into the cell extractor,
bypassing the walker.  That direct feed is the whole point: in production
the walker placeholderizes a nested table before the producer ever runs,
so this recursion path is dormant and can only be exercised in isolation.
The tests pin three things:

  * the balanced-span scanner finds nested ``{|…|}`` correctly,
  * ``extract_wiki_rows`` keeps a nested table intact inside its owning
    cell (the outer ``|-`` / ``|+`` keys don't fragment it),
  * ``produce_cell`` recurses on a raw nested table via the supplied
    callback — and is byte-identical to today when no callback is given.
"""
from britannica.pipeline.stages.elements._table_decompose import (
    _mask_nested_tables,
    _restore_nested,
    extract_wiki_rows,
    find_nested_table_spans,
    produce_cell,
)


def _identity(text: str) -> str:
    return text


# An outer table whose second data row's right-hand cell holds a nested
# table (the GERMANY-shape: a real grid with a decorative sub-grid inside
# one cell).  `inner` is the bytes the walker would hand the table
# producer after peeling the outer `{|` / `|}`.
NESTED_INNER = (
    "|-\n"
    "| Region || Population\n"
    "|-\n"
    "| North ||\n"
    "{|\n"
    "|-\n"
    "| sub-a || sub-b\n"
    "|}\n"
    "|-\n"
    "| South || 1000\n"
)
NESTED_RAW = "{|\n|-\n| sub-a || sub-b\n|}"


class TestFindNestedTableSpans:
    def test_none(self):
        assert find_nested_table_spans("| a || b\n| c") == []

    def test_single(self):
        text = "before {|\n|x\n|} after"
        spans = find_nested_table_spans(text)
        assert len(spans) == 1
        s, e = spans[0]
        assert text[s:e] == "{|\n|x\n|}"

    def test_two_siblings(self):
        text = "{|\n|x\n|} mid {|\n|y\n|}"
        spans = find_nested_table_spans(text)
        assert len(spans) == 2
        assert text[spans[0][0]:spans[0][1]] == "{|\n|x\n|}"
        assert text[spans[1][0]:spans[1][1]] == "{|\n|y\n|}"

    def test_nested_in_nested_returns_outer_only(self):
        # A table nested inside a nested table is contained in the OUTER
        # span — the producer that recurses on the outer finds the inner
        # on its own next descent (recursion at the right layer).
        text = "{|\n|a\n{|\n|deep\n|}\n|}"
        spans = find_nested_table_spans(text)
        assert len(spans) == 1
        assert text[spans[0][0]:spans[0][1]] == text


class TestMaskRoundTrip:
    def test_mask_then_restore_is_identity(self):
        masked, raw_spans = _mask_nested_tables(NESTED_INNER)
        assert "{|" not in masked          # nested opener is gone from masked
        assert raw_spans == [NESTED_RAW]
        assert _restore_nested(masked, raw_spans) == NESTED_INNER

    def test_no_nested_is_noop(self):
        text = "| a || b\n|-\n| c || d"
        masked, raw_spans = _mask_nested_tables(text)
        assert masked == text
        assert raw_spans == []


class TestExtractWikiRowsKeepsNestedIntact:
    def test_nested_table_stays_in_one_cell(self):
        _caption, rows = extract_wiki_rows(NESTED_INNER)
        # Three data rows; the nested table did NOT spawn phantom rows.
        assert len(rows) == 3
        # Row 1 header-ish: Region / Population.
        assert [c[2] for c in rows[0][1]] == ["Region", "Population"]
        # Row 2: "North" + the raw nested table, intact, in the 2nd cell.
        north_cells = rows[1][1]
        assert north_cells[0][2] == "North"
        assert north_cells[1][2] == NESTED_RAW
        # Row 3: untouched.
        assert [c[2] for c in rows[2][1]] == ["South", "1000"]

    def test_non_nested_table_unaffected(self):
        text = "|-\n| a || b\n|-\n| c || d"
        _caption, rows = extract_wiki_rows(text)
        assert [[c[2] for c in cells] for _attrs, cells in rows] == [
            ["a", "b"], ["c", "d"],
        ]


class TestProduceCellRecursion:
    def test_recurse_fires_on_raw_nested_table(self):
        seen = []

        def recurse(raw: str) -> str:
            seen.append(raw)
            return "«NESTED-MARKER»"

        content = f"North {NESTED_RAW} tail"
        styles, body = produce_cell("", content, _identity, recurse=recurse)
        assert seen == [NESTED_RAW]            # recursed on the nested raw
        assert body == "North «NESTED-MARKER» tail"   # marker substituted

    def test_recurse_none_leaves_content_untouched(self):
        # The production default: no callback -> body-text only, nested
        # bytes (if any) pass straight through as today.
        content = f"North {NESTED_RAW} tail"
        _styles, body = produce_cell("", content, _identity)
        assert body == content

    def test_no_nested_table_never_calls_recurse(self):
        seen = []

        def recurse(raw: str) -> str:           # pragma: no cover
            seen.append(raw)
            return "x"

        _styles, body = produce_cell("", "plain cell", _identity,
                                     recurse=recurse)
        assert seen == []
        assert body == "plain cell"


class TestEndToEnd:
    def test_extract_then_produce_recurses_exactly_once(self):
        seen = []

        def recurse(raw: str) -> str:
            seen.append(raw)
            return "«SUBTABLE»"

        _caption, rows = extract_wiki_rows(NESTED_INNER)
        produced = [
            [produce_cell(attr, content, _identity, recurse=recurse)[1]
             for _sep, attr, content in cells]
            for _attrs, cells in rows
        ]
        # The nested table was produced exactly once, on its raw bytes.
        assert seen == [NESTED_RAW]
        # Its marker landed in the North row's second cell; siblings clean.
        assert produced[0] == ["Region", "Population"]
        assert produced[1] == ["North", "«SUBTABLE»"]
        assert produced[2] == ["South", "1000"]
