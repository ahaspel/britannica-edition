"""Tests for the walk-classify-produce element pipeline."""
import re

from britannica.pipeline.stages.elements import (
    ElementContext,
    process_elements,
)
from britannica.pipeline.stages.elements._text import _clean_text
from britannica.pipeline.stages.elements._shapes import (
    SHAPE_BRACE_PIPE,
    SHAPE_DOUBLE_BRACKET,
    SHAPE_HTML_TAG,
    SHAPE_INLINE_IMAGE,
)
from britannica.pipeline.stages.elements._walker import walk


def _identity_transform(text: str) -> str:
    """Dummy text transform that returns text unchanged."""
    return text


def _bold_transform(text: str) -> str:
    """Simple transform that converts '''bold''' to markers."""
    return text.replace("'''", "\u00abB\u00bb", 1).replace("'''", "\u00ab/B\u00bb", 1)


class TestExtraction:
    """Elements are extracted by the walker and replaced with placeholders."""

    def test_extract_ref(self):
        text = "before <ref>footnote text</ref> after"
        extracted, extracts = walk(text)
        assert "<ref>" not in extracted
        assert len(extracts) == 1
        _ph, _shape, raw = extracts[0]
        assert "footnote text" in raw

    def test_extract_table(self):
        text = "before\n{|\n|cell\n|}\nafter"
        extracted, extracts = walk(text)
        assert "{|" not in extracted
        assert len(extracts) == 1
        _ph, shape, _raw = extracts[0]
        assert shape == SHAPE_BRACE_PIPE

    def test_extract_image(self):
        # `[[File:…]]` in inline prose is classified as SHAPE_INLINE_IMAGE
        # (more specific than the generic SHAPE_DOUBLE_BRACKET).
        text = "text [[File:Foo.jpg|thumb|A caption]] more"
        extracted, extracts = walk(text)
        assert "[[File:" not in extracted
        assert len(extracts) == 1
        _ph, shape, _raw = extracts[0]
        assert shape == SHAPE_INLINE_IMAGE

    def test_extract_score(self):
        text = "music <score>{ \\new Staff }</score> here"
        extracted, _extracts = walk(text)
        assert "<score>" not in extracted

    def test_extract_math(self):
        text = "formula <math>x^2</math> end"
        extracted, _extracts = walk(text)
        assert "<math>" not in extracted

    def test_extract_poem(self):
        text = "verse <poem>line one\nline two</poem> end"
        extracted, _extracts = walk(text)
        assert "<poem>" not in extracted

    def test_nested_ref_in_table(self):
        """Outer-first walking: the table is extracted as a single
        unit and the ref stays inside its raw bytes — found later
        by the classifier when it recurses into the table's inner."""
        text = "{|\n|cell <ref>note</ref>\n|}"
        extracted, extracts = walk(text)
        assert len(extracts) == 1
        _ph, shape, raw = extracts[0]
        assert shape == SHAPE_BRACE_PIPE
        assert "<ref>" in raw  # ref still inside the table's bytes

    def test_preserves_surrounding_text(self):
        text = "Hello <ref>note</ref> world"
        extracted, extracts = walk(text)
        ph = extracts[0][0]
        assert extracted == f"Hello {ph} world"


class TestProcessing:
    """Elements are processed to their final form."""

    def test_ref_becomes_footnote_marker(self):
        text = "text <ref>See also Wikipedia</ref> more"
        result = process_elements(text, _identity_transform, ElementContext())
        assert "\u00abFN:" in result
        assert "\u00ab/FN\u00bb" in result
        assert "See also Wikipedia" in result
        assert "<ref>" not in result

    def test_image_clean_caption(self):
        # The image is a LEAF: the bracket's trailing text is alt, not a
        # rendered caption ("no honest captions"); captionless-by-author
        # intent is fine.  Any visible caption is a separate sibling block.
        text = "[[File:Foo.jpg|thumb|A nice caption]]"
        result = process_elements(text, _identity_transform, ElementContext())
        assert "{{IMG:Foo.jpg}}" in result

    def test_image_caption_markers_stripped(self):
        """Trailing bracket text is alt (dropped), so no caption \u2014 and no
        markers \u2014 ride in the IMG leaf."""
        text = "[[File:Foo.jpg|thumb|'''Fig.''' 1 - ''Italic'' caption]]"
        result = process_elements(text, _bold_transform, ElementContext())
        assert "{{IMG:Foo.jpg}}" in result

    def test_math_preserved(self):
        text = "formula <math>x^2 + y^2</math> end"
        result = process_elements(text, _identity_transform, ElementContext())
        assert "\u00abMATH:x^2 + y^2\u00ab/MATH\u00bb" in result

    def test_ref_inside_table(self):
        """Footnote inside a table is processed cleanly."""
        text = "{|\n|cell <ref>A footnote</ref>\n|}"
        result = process_elements(text, _identity_transform, ElementContext())
        assert "\u00abFN:A footnote\u00ab/FN\u00bb" in result
        assert "<ref>" not in result

    def test_ref_text_preserves_formatting(self):
        """Footnote text KEEPS its formatting markers \u2014 the producer no
        longer flattens the body, so \u00abB\u00bb/\u00abI\u00bb/etc. survive for the viewer
        to render (the footnote producer owns its body, no _clean_text)."""
        text = "<ref>See '''bold''' here</ref>"
        result = process_elements(text, _bold_transform, ElementContext())
        fn_match = re.search(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
        assert fn_match is not None
        assert "\u00abB\u00bbbold\u00ab/B\u00bb" in fn_match.group(1)


class TestRealData:
    """Tests using actual wikitext from source pages."""

    def _load_page(self, vol, page):
        import json
        from pathlib import Path
        path = Path(f"data/raw/wikisource/vol_{vol:02d}/vol{vol:02d}-page{page:04d}.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)["raw_text"]

    def test_cithara_caption_clean(self):
        """CITHARA image caption should have no HTML or markers."""
        raw = self._load_page(6, 411)
        # Extract just the img float for Nero Citharoedus
        m = re.search(r"\{\{img float\s*\|(?:[^{}]|\{\{[^{}]*\}\})*Nero(?:[^{}]|\{\{[^{}]*\}\})*\}\}", raw, re.DOTALL | re.IGNORECASE)
        assert m, "Nero image not found in page"
        result = process_elements(m.group(0), _identity_transform, ElementContext())
        assert "{{IMG:" in result
        # Caption should be plain text
        cap = re.search(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result)
        assert cap, f"No caption in: {result}"
        assert "<br" not in cap.group(1), f"HTML in caption: {cap.group(1)}"
        assert "\u00ab" not in cap.group(1), f"Markers in caption: {cap.group(1)}"
        assert "Nero" in cap.group(1)

    def test_japan_footnote_in_table(self):
        """JAPAN earthquake table footnotes should be clean."""
        raw = self._load_page(15, 176)
        # Find the earthquake table
        m = re.search(r"\{\|.*?684.*?\|\}", raw, re.DOTALL)
        if m:
            result = process_elements(m.group(0), _identity_transform, ElementContext())
            assert "<ref>" not in result, "Raw ref tags survived"
            if "\u00abFN:" in result:
                fn = re.search(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
                assert "\u00ab" not in fn.group(1), f"Markers in footnote: {fn.group(1)}"

    def test_score_in_table_biniou(self):
        """BINIOU score tags inside tables should become image markers."""
        raw = self._load_page(3, 971)
        context = ElementContext(volume=3, page_number=971)
        result = process_elements(raw, _identity_transform, context)
        assert "<score>" not in result, "Raw score tags survived"
        assert "\\new Staff" not in result, "LilyPond code survived"


class TestTableProcessing:
    """Tables are processed with clean cells."""

    def test_simple_table(self):
        text = '{|\n|A\n|B\n|-\n|C\n|D\n|}'
        result = process_elements(text, _identity_transform, ElementContext())
        assert "«HTMLTABLE:" in result and "«/HTMLTABLE»" in result
        for cell in ("A", "B", "C", "D"):
            assert f">{cell}</td>" in result

    def test_table_carries_cell_styles(self):
        """Cell attributes are CARRIED into `<td style=…>` (the faithful
        contract), not stripped: `align="right"` → text-align:right, inline
        `style=` preserved."""
        text = '{|\n|align="right"|100\n|style="color:red"|hello\n|}'
        result = process_elements(text, _identity_transform, ElementContext())
        assert ">100</td>" in result and ">hello</td>" in result
        assert "text-align:right" in result
        assert "color:red" in result

    def test_table_with_footnote(self):
        """Footnote inside table cell should be clean in output."""
        text = '{|\n|Year\n|Deaths\n|-\n|1703\n|5000<ref>Tidal wave.</ref>\n|}'
        result = process_elements(text, _identity_transform, ElementContext())
        assert "<ref>" not in result
        assert "\u00abFN:" in result
        assert "Tidal wave" in result

    def test_table_br_preserved_in_cell(self):
        """`<br>` is preserved losslessly in the cell, not collapsed to space."""
        text = '{|\n|Houses<br />destroyed.\n|Deaths.\n|}'
        result = process_elements(text, _identity_transform, ElementContext())
        assert "Houses" in result and "destroyed." in result
        assert "<br" in result

    def test_table_with_image(self):
        """Image inside table is extracted as separate element."""
        text = '{|\n|[[File:Foo.jpg|thumb|Caption]]\n|Text\n|}'
        result = process_elements(text, _identity_transform, ElementContext())
        assert "{{IMG:Foo.jpg" in result


class TestChemistryLayout:
    """A {|\u2026|} laid out as a 2-D chemical-reaction scheme (atom-label
    cells, \u27e8/\u27e9 bracket images, rowspan brackets) is detected and
    rendered through the chemistry path \u2014 a structure-preserving \u00abCHEM:\u2026\u00bb
    block \u2014 not flattened to {{TABLE:\u2026}TABLE} by _process_table."""

    def test_fulminic_acid_competing_formulae(self):
        # FULMINIC ACID's table of the four competing structural
        # formulae (Steiner / Divers / Scholl / Nef), with a rowspan=2
        # \u3008 bracket grouping {C:N\u00b7OH ; N:CH ; CH:N\u00b7O}.
        table = (
            '{|style="line-height:100%; margin:auto"\n'
            '|C : N\u00b7OH||rowspan=2| O[[File:Langle.svg|10px]]'
            '||N : CH ||CH : N\u00b7O|| rowspan=2| C : N\u00b7OH.\n'
            '|-\n'
            '|C : N\u00b7OH, ||N : \u010a\u00b7OH, ||\u010aH : N\u00b7O, \n'
            '|- align=center\n'
            '|Steiner, || colspan=2|Divers, ||Scholl, ||Nef.\n'
            '|}'
        )
        result = process_elements(table, _identity_transform, ElementContext())
        # Its own marker \u2014 not the flattened {{TABLE:}} path.
        assert "\u00abCHEM:" in result
        assert "{{TABLE:" not in result
        # 2-D structure preserved: the rowspan bracket survives.
        assert 'rowspan="2"' in result
        # Cell content survives intact.
        assert "C : N\u00b7OH" in result
        assert "Steiner" in result and "Nef" in result
        # The angle-bracket image is rendered as the Unicode glyph
        # \u276e (U+276E) by the specialized CHEM processor.  Earlier this
        # was a `{{IMG:Langle.svg}}` marker (with a TODO to glyph-ify
        # it); the glyph rendering has since landed.
        assert "\u276e" in result

    def test_plain_table_unaffected(self):
        # A normal data table with NO angle-bracket image is untouched.
        table = '{|\n|A\n|B\n|-\n|C\n|D\n|}'
        result = process_elements(table, _identity_transform, ElementContext())
        assert "\u00abCHEM:" not in result
        assert "\u00abHTMLTABLE:" in result


class TestCleanText:
    def test_strips_bold(self):
        assert _clean_text("\u00abB\u00bbhello\u00ab/B\u00bb") == "hello"

    def test_strips_italic(self):
        assert _clean_text("\u00abI\u00bbworld\u00ab/I\u00bb") == "world"

    def test_strips_html(self):
        assert _clean_text("a<br />b") == "a b"

    def test_collapses_whitespace(self):
        assert _clean_text("a   b  c") == "a b c"
