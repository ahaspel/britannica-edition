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
        # Image gathered from the INNER table.
        assert comps.images == [
            "EB1911 Marsupialia - Skull of the Tasmanian Devil.jpg"]
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
        assert comps.images == ["Bag-pipe music 1.png"]
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


class TestAbbeyTableLegend:
    def test_nested_table_is_legend(self):
        comps = extract_figure_components(ABBEY_FIG3, _identity)
        # Image + caption separated correctly.
        assert comps.images == ["Abbey_3.png"]
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
