"""Tests for the extract-process-reassemble element pipeline."""
import re

from britannica.pipeline.stages.elements import (
    extract,
    process_elements,
    _clean_text,
)


def _identity_transform(text: str) -> str:
    """Dummy text transform that returns text unchanged."""
    return text


def _bold_transform(text: str) -> str:
    """Simple transform that converts '''bold''' to markers."""
    return text.replace("'''", "\u00abB\u00bb", 1).replace("'''", "\u00ab/B\u00bb", 1)


class TestExtraction:
    """Elements are extracted and replaced with placeholders."""

    def test_extract_ref(self):
        text = "before <ref>footnote text</ref> after"
        extracted, reg = extract(text)
        assert "<ref>" not in extracted
        assert len(reg.elements) == 1
        assert "footnote text" in list(reg.elements.values())[0][1]

    def test_extract_table(self):
        text = "before\n{|\n|cell\n|}\nafter"
        extracted, reg = extract(text)
        assert "{|" not in extracted
        assert len(reg.elements) == 1
        etype, raw = list(reg.elements.values())[0]
        assert etype == "TABLE"

    def test_extract_image(self):
        text = "text [[File:Foo.jpg|thumb|A caption]] more"
        extracted, reg = extract(text)
        assert "[[File:" not in extracted
        assert len(reg.elements) == 1

    def test_extract_score(self):
        text = "music <score>{ \\new Staff }</score> here"
        extracted, reg = extract(text)
        assert "<score>" not in extracted

    def test_extract_math(self):
        text = "formula <math>x^2</math> end"
        extracted, reg = extract(text)
        assert "<math>" not in extracted

    def test_extract_poem(self):
        text = "verse <poem>line one\nline two</poem> end"
        extracted, reg = extract(text)
        assert "<poem>" not in extracted

    def test_nested_ref_in_table(self):
        """Extracting table first captures the ref inside it."""
        text = "{|\n|cell <ref>note</ref>\n|}"
        extracted, reg = extract(text)
        # Table is extracted (outermost)
        assert len(reg.elements) == 1
        etype, raw = list(reg.elements.values())[0]
        assert etype == "TABLE"
        # The ref is still inside the table's raw content
        assert "<ref>" in raw

    def test_preserves_surrounding_text(self):
        text = "Hello <ref>note</ref> world"
        extracted, reg = extract(text)
        key = list(reg.elements.keys())[0]
        assert extracted == f"Hello {key} world"


class TestProcessing:
    """Elements are processed to their final form."""

    def test_ref_becomes_footnote_marker(self):
        text = "text <ref>See also Wikipedia</ref> more"
        result = process_elements(text, _identity_transform, {})
        assert "\u00abFN:" in result
        assert "\u00ab/FN\u00bb" in result
        assert "See also Wikipedia" in result
        assert "<ref>" not in result

    def test_image_clean_caption(self):
        text = "[[File:Foo.jpg|thumb|A nice caption]]"
        result = process_elements(text, _identity_transform, {})
        assert "{{IMG:Foo.jpg|A nice caption}}" in result

    def test_image_caption_markers_stripped(self):
        """Bold/italic markers in captions are stripped to plain text."""
        text = "[[File:Foo.jpg|thumb|'''Fig.''' 1 - ''Italic'' caption]]"
        result = process_elements(text, _bold_transform, {})
        assert "{{IMG:Foo.jpg|" in result
        # Caption should be plain text, no markers
        caption = re.search(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result)
        assert caption is not None
        cap_text = caption.group(1)
        assert "\u00ab" not in cap_text
        assert "'''" not in cap_text

    def test_math_preserved(self):
        text = "formula <math>x^2 + y^2</math> end"
        result = process_elements(text, _identity_transform, {})
        assert "\u00abMATH:x^2 + y^2\u00ab/MATH\u00bb" in result

    def test_ref_inside_table(self):
        """Footnote inside a table is processed cleanly."""
        text = "{|\n|cell <ref>A footnote</ref>\n|}"
        result = process_elements(text, _identity_transform, {})
        assert "\u00abFN:A footnote\u00ab/FN\u00bb" in result
        assert "<ref>" not in result

    def test_ref_text_is_clean(self):
        """Footnote text has no formatting markers."""
        text = "<ref>See '''bold''' and ''italic''</ref>"
        result = process_elements(text, _bold_transform, {})
        fn_match = re.search(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
        assert fn_match is not None
        fn_text = fn_match.group(1)
        assert "\u00ab" not in fn_text


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
        result = process_elements(m.group(0), _identity_transform, {})
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
            result = process_elements(m.group(0), _identity_transform, {})
            assert "<ref>" not in result, "Raw ref tags survived"
            if "\u00abFN:" in result:
                fn = re.search(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
                assert "\u00ab" not in fn.group(1), f"Markers in footnote: {fn.group(1)}"

    def test_score_in_table_biniou(self):
        """BINIOU score tags inside tables should become image markers."""
        raw = self._load_page(3, 971)
        context = {"volume": 3, "page_number": 971}
        result = process_elements(raw, _identity_transform, context)
        assert "<score>" not in result, "Raw score tags survived"
        assert "\\new Staff" not in result, "LilyPond code survived"


class TestTableProcessing:
    """Tables are processed with clean cells."""

    def test_simple_table(self):
        text = '{|\n|A\n|B\n|-\n|C\n|D\n|}'
        result = process_elements(text, _identity_transform, {})
        assert "{{TABLE" in result
        assert "}TABLE}" in result
        assert "A | B" in result
        assert "C | D" in result

    def test_table_strips_attributes(self):
        text = '{|\n|align="right"|100\n|style="color:red"|hello\n|}'
        result = process_elements(text, _identity_transform, {})
        assert "100" in result
        assert "hello" in result
        assert "align" not in result
        assert "style" not in result

    def test_table_with_footnote(self):
        """Footnote inside table cell should be clean in output."""
        text = '{|\n|Year\n|Deaths\n|-\n|1703\n|5000<ref>Tidal wave.</ref>\n|}'
        result = process_elements(text, _identity_transform, {})
        assert "<ref>" not in result
        assert "\u00abFN:" in result
        assert "Tidal wave" in result

    def test_table_br_single_cell_collapses(self):
        """Single cell with <br> collapses to space."""
        text = '{|\n|Houses<br />destroyed.\n|Deaths.\n|}'
        result = process_elements(text, _identity_transform, {})
        assert "Houses destroyed." in result or "Houses  destroyed." in result

    def test_table_with_image(self):
        """Image inside table is extracted as separate element."""
        text = '{|\n|[[File:Foo.jpg|thumb|Caption]]\n|Text\n|}'
        result = process_elements(text, _identity_transform, {})
        assert "{{IMG:Foo.jpg" in result


class TestCleanText:
    def test_strips_bold(self):
        assert _clean_text("\u00abB\u00bbhello\u00ab/B\u00bb") == "hello"

    def test_strips_italic(self):
        assert _clean_text("\u00abI\u00bbworld\u00ab/I\u00bb") == "world"

    def test_strips_html(self):
        assert _clean_text("a<br />b") == "a b"

    def test_collapses_whitespace(self):
        assert _clean_text("a   b  c") == "a b c"
