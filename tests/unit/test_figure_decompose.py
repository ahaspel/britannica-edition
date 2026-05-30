"""Direct-feed tests for the raw, recursive figure-component extractor —
the ICL analog of the table-decompose tests.  The point under test is
the RECURSION: a figure whose components are split across a nested
`{|…|}` (MARSUPIALIA) must come back with image + attribution gathered
from the inner table and caption from the outer — the nesting bug fixed
at the owning layer.
"""
from britannica.pipeline.stages.elements._figure_decompose import (
    extract_figure_components,
)


def _identity(s: str) -> str:
    return s


# MARSUPIALIA Fig. 2 — the canonical two-level nested figure: outer table
# wraps an inner [image + attribution] figure-table, with the real caption
# in the outer's second row.
MARSUPIALIA = (
    '{|style="margin:auto" width="400"\n'
    '|style="text-align:center"|\n'
    '{|cellpadding="0" cellspacing="0" style="font-size: smaller"\n'
    '|[[Image:EB1911 Marsupialia - Skull of the Tasmanian Devil.jpg|391px]]\n'
    '|-\n'
    '|From Flower, «I»Quart. Jour. Geol. Soc.«/I»\n'
    '|}\n'
    '|-\n'
    '|style="text-align:center"|\n'
    '{{sc|Fig. 2.}}—Front View of Skull of the Tasmanian Devil '
    '(«I»Sarcophilus ursinus«/I») to exhibit polyprotodont type of dentition.\n'
    '|}'
)


class TestMarsupialiaNestedFigure:
    def test_components_gathered_across_nesting(self):
        comps = extract_figure_components(MARSUPIALIA, _identity)
        # Image gathered from the INNER table — full spec (filename + params)
        # carried, not just the filename.
        assert len(comps.images) == 1
        assert "Skull of the Tasmanian Devil.jpg" in comps.images[0]
        assert "391px" in comps.images[0]          # width param carried
        # Attribution gathered from the inner table — NOT taken as caption.
        assert any("From Flower" in a for a in comps.attribution_parts), \
            comps.attribution_parts
        # Caption gathered from the OUTER row — not leaked, not lost.
        assert any("Front View of Skull" in c for c in comps.caption_parts), \
            comps.caption_parts
        # The attribution must NOT have ended up in the caption (the bug).
        assert not any("From Flower" in c for c in comps.caption_parts), \
            comps.caption_parts
        assert comps.legend_lines == []
        assert comps.footnotes == []


# BAG-PIPE Fig. 1 — single-level: musical-notation image + two footnotes,
# no caption.  Footnotes carried, not mistaken for caption/attribution.
BAGPIPE = (
    '{|{{Ts|ma}}\n'
    '|&emsp;||[[File:Bag-pipe music 1.png|450px|center]]||'
    '<ref>These harmonics may be obtained by good performers.</ref>'
    '<br><br><ref>The notes marked with asterisks are sharp.</ref>\n'
    '|}'
)


class TestBagpipeImageWithFootnotes:
    def test_image_and_footnotes_only(self):
        comps = extract_figure_components(BAGPIPE, _identity)
        assert len(comps.images) == 1
        assert "Bag-pipe music 1.png" in comps.images[0]
        # layout params carried, not tossed:
        assert "450px" in comps.images[0] and "center" in comps.images[0]
        assert len(comps.footnotes) == 2
        assert comps.caption_parts == []
        assert comps.attribution_parts == []


# ABBEY Fig. 3 — table legend: the figure's caption cell CONTAINS a nested
# `{|…|}` table laying out the (multi-column) legend.  The structural rule:
# a no-image nested table inside a figure → everything in it is legend.
# (Faithfully trimmed from the real Fig. 3 — Ground-plan of St Gall.)
ABBEY_FIG3 = (
    '{| {{ts|sm92|lh10|ma|width:450px}}\n'
    '|[[image:Abbey_3.png|450px|frameless]]\n'
    '|-\n'
    '|{{center|{{sc|Fig. 3.}}—Ground-plan of St Gall.}}\n'
    '{|{{Ts|ma}}\n'
    '|{{Ts|width:49%|vtp}}|\n'
    '{{csc|Church. }}\n\n'
    '<poem>A.&emsp;High altar.\n'
    'B.&emsp;Altar of St Paul.\n'
    'C.&emsp;Altar of St Peter.</poem>\n'
    '|width=49%|\n'
    '<poem>G.&emsp;Cloister.\n'
    'H.&emsp;Calefactory.\n'
    'I.&emsp;Necessary.</poem>\n'
    '|}\n'
    '|}'
)


# A figure whose legend is MULTICOL rows in its OWN cells (not a nested
# table) — the loose-ladder case: `|A. x || C. y` rows.  Source row-major
# order is a visual grid; reading order is alphabetical.
MULTICOL = (
    '{| {{Ts|ma}}\n'
    '|[[File:Foo.png|300px]]\n'
    '|-\n'
    '|colspan=2|{{sc|Fig. 9.}}—A multicol-legend figure.\n'
    '|-\n'
    '|A. Apple.||C. Cherry.\n'
    '|-\n'
    '|B. Banana.||D. Date.\n'
    '|}'
)


class TestMulticolLegend:
    def test_multicol_rows_become_sorted_legend(self):
        comps = extract_figure_components(MULTICOL, _identity)
        assert "Foo.png" in comps.images[0]
        assert any("multicol-legend figure" in c for c in comps.caption_parts)
        # Row-major source (A,C,B,D) → reading order (A,B,C,D) in the legend.
        # (Trailing period stripped — production's `_parse_multicol_legend_row`
        # behaviour, inherited by reuse.)
        assert comps.legend_lines == [
            "A. Apple", "B. Banana", "C. Cherry", "D. Date"], \
            comps.legend_lines
        # entries went to legend, not caption
        assert not any("Apple" in c for c in comps.caption_parts)


# A figure whose legend is a PROSE label-ladder sitting loose in one cell
# (newline-separated `LABEL, text.` entries) — NOT a nested table, NOT
# multicol rows.  The prose arm of the loose-ladder: ≥3 entries ⇒ legend.
PROSE_LEGEND = (
    '{| {{Ts|ma}}\n'
    '|[[File:Bar.png|300px]]\n'
    '|-\n'
    '|{{sc|Fig. 4.}}—A prose-legend figure.\n'
    '|-\n'
    '|a, Head.\n'
    'b, Thorax.\n'
    'c, Abdomen.\n'
    '|}'
)


class TestProseLegend:
    def test_prose_ladder_cell_becomes_legend(self):
        comps = extract_figure_components(PROSE_LEGEND, _identity)
        assert "Bar.png" in comps.images[0]
        assert any("prose-legend figure" in c for c in comps.caption_parts), \
            comps.caption_parts
        # ≥3-entry prose ladder → legend (ground-up `_parse_legend_lines`,
        # which preserves the source trailing period — a fidelity gain over
        # production's `_parse_prose_legend_rows`, which strips it).
        assert comps.legend_lines == [
            "a. Head.", "b. Thorax.", "c. Abdomen."], comps.legend_lines
        # the ladder went to legend, not caption
        assert not any("Thorax" in c for c in comps.caption_parts)


# A figure whose legend is `<br/>`-separated italic-label entries where one
# entry WRAPS across a `<br/>` — the second line has no label, so it's a
# continuation.  Production's parsers (`_emit_legend_chunk` /
# `_parse_prose_legend_rows`) silently DROP that label-less line (the
# CHAERONEIA partial-loss).  The ground-up parser appends it to its entry.
CONTINUATION = (
    '{| {{Ts|ma}}\n'
    '|[[File:Baz.png|300px]]\n'
    '|-\n'
    '|{{sc|Fig. 5.}}—A wrapped-entry legend.\n'
    '|-\n'
    '|«I»g«/I», Cerebral ganglia.<br/>'
    '«I»n«/I», Commissure uniting<br/>'
    'this with the ventral cord.<br/>'
    '«I»v«/I», Ventral nerve cord.\n'
    '|}'
)


class TestContinuationNotDropped:
    def test_wrapped_entry_continuation_is_appended(self):
        comps = extract_figure_components(CONTINUATION, _identity)
        blob = " ".join(comps.legend_lines)
        # The continuation ("this with the ventral cord") must NOT be dropped.
        assert "ventral cord" in blob, comps.legend_lines
        # It is APPENDED to the entry it continues, not lost or orphaned.
        merged = [ln for ln in comps.legend_lines if "Commissure uniting" in ln]
        assert merged and "this with the ventral cord" in merged[0], \
            comps.legend_lines
        # Three labelled entries (g, n, v) — the continuation isn't one of them.
        assert len([ln for ln in comps.legend_lines
                    if not ln.startswith("###")]) == 3, comps.legend_lines


class TestAbbeyTableLegend:
    def test_nested_table_is_legend(self):
        comps = extract_figure_components(ABBEY_FIG3, _identity)
        # Image + caption separated correctly; full spec carried.
        assert len(comps.images) == 1
        assert "Abbey_3.png" in comps.images[0]
        assert "frameless" in comps.images[0]      # param carried
        assert any("Ground-plan of St Gall" in c for c in comps.caption_parts)
        # The nested table's content went to LEGEND, not caption, not dropped.
        assert comps.legend_lines, "legend table content was dropped"
        # Recursed ALL the way down: per-entry lines + the csc sub-heading,
        # not a flattened blob.
        assert "### Church." in comps.legend_lines
        assert "A. High altar." in comps.legend_lines
        assert "G. Cloister." in comps.legend_lines
        legend_blob = " ".join(comps.legend_lines)
        # And it did NOT leak into the caption.
        assert not any("High altar" in c for c in comps.caption_parts)
        # nor the caption into the legend.
        assert "Ground-plan" not in legend_blob
