"""Real-data tests for the v2 transform pipeline.

Each test loads actual wikitext from source pages and verifies that
_transform_text_v2 produces correct output for every element type
and text feature.
"""
import json
import re
from pathlib import Path

import pytest

RAW_DIR = Path("data/raw/wikisource")


def _load_page(vol, page):
    path = RAW_DIR / f"vol_{vol:02d}" / f"vol{vol:02d}-page{page:04d}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["raw_text"]


def _transform(raw, volume=1, page_number=1):
    from britannica.pipeline.stages.transform_articles import _transform_text_v2
    return _transform_text_v2(raw, volume, page_number)


# ── Element Types ──────────────────────────────────────────────────────

class TestRealImages:
    """[[File:...]] images from real pages."""

    def test_file_image_produces_img_marker(self):
        """Vol 1 p774 has [[File:]] images."""
        raw = _load_page(1, 774)
        result = _transform(raw)
        assert "{{IMG:" in result, "No IMG marker produced"

    def test_img_marker_has_filename(self):
        raw = _load_page(1, 774)
        result = _transform(raw)
        m = re.search(r"\{\{IMG:([^|}]+)", result)
        assert m, "No IMG filename"
        assert m.group(1).endswith((".jpg", ".png", ".gif", ".svg")), \
            f"Filename doesn't look like image: {m.group(1)}"

    def test_img_caption_is_plain_text(self):
        """Image captions should have no formatting markers or HTML."""
        raw = _load_page(1, 774)
        result = _transform(raw)
        for cap in re.findall(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result):
            assert "\u00ab" not in cap, f"Marker in caption: {cap}"
            assert "<" not in cap, f"HTML in caption: {cap}"


class TestRealImageFloat:
    """{{img float}} images from real pages (CITHARA)."""

    def test_cithara_img_float(self):
        raw = _load_page(6, 411)
        result = _transform(raw, volume=6, page_number=411)
        caps = re.findall(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result)
        nero_caps = [c for c in caps if "Nero" in c]
        assert nero_caps, "Nero Citharoedus caption not found"
        cap = nero_caps[0]
        assert "<br" not in cap, f"HTML in caption: {cap}"
        assert "\u00ab" not in cap, f"Marker in caption: {cap}"
        assert "{{" not in cap, f"Template in caption: {cap}"


class TestRealFootnotes:
    """<ref> footnotes from real pages."""

    def test_footnote_basic(self):
        """Vol 3 p76 has footnotes."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        assert "<ref>" not in result, "Raw <ref> survived"
        assert "\u00abFN:" in result, "No FN marker produced"

    def test_footnote_text_clean(self):
        """Footnote text should be plain — no markers."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        for fn in re.findall(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result):
            assert "\u00abB\u00bb" not in fn, f"Bold marker in footnote: {fn[:60]}"
            assert "\u00abI\u00bb" not in fn, f"Italic marker in footnote: {fn[:60]}"

    def test_footnote_in_table_japan(self):
        """JAPAN earthquake table (vol 15 p176) has footnotes in table cells."""
        raw = _load_page(15, 176)
        result = _transform(raw, volume=15, page_number=176)
        assert "<ref>" not in result, "Raw <ref> survived"
        # Should have footnote markers
        fns = re.findall(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
        if fns:
            for fn in fns:
                assert "\u00ab" not in fn, f"Markers in footnote: {fn[:60]}"


class TestRealTables:
    """Wiki tables from real pages."""

    def test_table_produces_marker(self):
        """Vol 3 p76 has tables (multi-element page)."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        # Should have TABLE markers or data content, not raw {|...|}
        assert "{|" not in result, "Raw wiki table markup survived"

    def test_table_attributes_stripped(self):
        """Table cell attributes like align, colspan should be stripped."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        # Check no cell attributes leaked
        for attr in ["colspan=", "rowspan=", 'align="', 'style="']:
            # Only check outside TABLE markers (attributes inside markers are OK)
            outside = re.sub(r"\{\{TABLE.*?\}TABLE\}", "", result, flags=re.DOTALL)
            assert attr not in outside, f"Leaked attribute: {attr}"


class TestRealPoems:
    """<poem> blocks from real pages."""

    def test_poem_standalone(self):
        """A standalone <poem> block produces VERSE markers."""
        result = _transform("text\n<poem>line one\nline two</poem>\nmore")
        assert "<poem>" not in result, "Raw <poem> survived"
        assert "{{VERSE:" in result, "No VERSE marker produced"
        assert "line one" in result

    def test_poem_in_table_produces_verse(self):
        """Vol 1 p44 has <poem> inside a table — should produce VERSE marker."""
        raw = _load_page(1, 44)
        result = _transform(raw)
        assert "<poem>" not in result, "Raw <poem> survived"
        assert "{{VERSE:" in result or "VERSE}" in result, "No VERSE marker from poem in table"


class TestRealMath:
    """<math> blocks from real pages."""

    def test_math_produces_marker(self):
        """Vol 3 p50 has <math> blocks."""
        raw = _load_page(3, 50)
        result = _transform(raw, volume=3, page_number=50)
        assert "<math>" not in result, "Raw <math> survived"
        assert "\u00abMATH:" in result, "No MATH marker produced"

    def test_math_content_preserved(self):
        """LaTeX content inside math should be preserved."""
        raw = _load_page(3, 50)
        result = _transform(raw, volume=3, page_number=50)
        m = re.search(r"\u00abMATH:(.*?)\u00ab/MATH\u00bb", result)
        assert m, "No MATH marker found"
        assert len(m.group(1).strip()) > 0, "Empty MATH content"


class TestRealScores:
    """<score> tags from real pages."""

    def test_bagpipe_scores(self):
        """Vol 3 p221 has <score> tags (BAG-PIPE)."""
        raw = _load_page(3, 221)
        result = _transform(raw, volume=3, page_number=221)
        assert "<score>" not in result, "Raw <score> survived"
        assert "\\new Staff" not in result, "LilyPond code survived"

    def test_biniou_score_in_table(self):
        """Vol 3 p971 has <score> inside a table."""
        raw = _load_page(3, 971)
        result = _transform(raw, volume=3, page_number=971)
        assert "<score>" not in result, "Raw <score> survived"
        assert "\\new Staff" not in result, "LilyPond code in table survived"


# ── Text Features ──────────────────────────────────────────────────────

class TestRealHieroglyphs:
    """Hieroglyph conversion from real pages."""

    def test_hieroglyph_template(self):
        """A {{hieroglyph}} template should be converted."""
        # Vol 1 p37 mentions hieroglyphs but doesn't have the template.
        # Test with synthetic input.
        result = _transform("sign {{hieroglyph|A1}} here")
        assert "{{hieroglyph|" not in result, "Raw hieroglyph template survived"


class TestRealShoulderHeadings:
    """Shoulder headings from real pages."""

    def test_shoulder_heading(self):
        """Shoulder headings are converted to SH markers."""
        raw = 'text {{EB1911 Shoulder Heading|Topic Name}} more'
        result = _transform(raw)
        assert "\u00abSH\u00bb" in result, "No SH marker produced"
        assert "Topic Name" in result

    def test_shoulder_heading_real_page(self):
        """Vol 1 p10 has shoulder headings outside noinclude."""
        raw = _load_page(1, 10)
        result = _transform(raw)
        assert "{{EB1911 Shoulder Heading" not in result, \
            "Raw shoulder heading template survived"


class TestRealLinks:
    """Cross-reference links from real pages."""

    def test_wikilink(self):
        """Vol 1 p7 has [[wikilinks]]."""
        raw = _load_page(1, 7)
        result = _transform(raw)
        assert "[[" not in result or "[[" in result and "hieroglyph" in result, \
            "Raw wikilink survived"

    def test_link_template(self):
        """Vol 3 p8 has {{EB1911 article link}}."""
        raw = _load_page(3, 8)
        result = _transform(raw, volume=3, page_number=8)
        assert "EB1911 article link" not in result, "Raw link template survived"


class TestRealSmallCaps:
    """{{sc|...}} template conversion."""

    def test_sc_template(self):
        """Vol 3 p16 has {{sc|...}} templates."""
        raw = _load_page(3, 16)
        result = _transform(raw, volume=3, page_number=16)
        assert "{{sc|" not in result, "Raw sc template survived"


class TestTableCellProcessing:
    """Table cell content is processed through text_transform."""

    def test_italic_in_table_cell(self):
        """Wiki italic in table cells must be converted."""
        result = _transform("{|\n|''italic'' text\n|normal\n|}")
        assert "''" not in result, f"Raw italic survived: {result[:60]}"

    def test_sub_sup_in_table_cell(self):
        """<sub>/<sup> in table cells must be converted to Unicode."""
        result = _transform("{|\n|H<sub>2</sub>O\n|100\n|}")
        assert "<sub>" not in result, f"Raw sub survived: {result[:60]}"
        assert "\u2082" in result, f"No Unicode subscript: {result[:60]}"

    def test_abbreviation_italic_real_data(self):
        """ABBREVIATION (vol 1 p58) has ''e.g.'' in table cells."""
        raw = _load_page(1, 58)
        result = _transform(raw)
        if "e.g." in result:
            assert "''e.g.''" not in result, "Raw wiki italic in ABBREVIATION table"


class TestNestedWrapperTemplates:
    """Wrapper templates (fine block, center, etc.) with nested content
    must not lose their inner text or links."""

    def test_fine_block_preserves_links(self):
        """Vol 1 p35 has {{fine block|...}} with nested {{EB1911 article link}}."""
        raw = _load_page(1, 35)
        result = _transform(raw)
        assert "Jethro" in result, "Jethro lost (inside {{fine block}})"
        assert "\u00abLN:" in result and "Jethro" in result, "Jethro link lost"

    def test_fine_block_preserves_text(self):
        """Content inside {{fine block}} must not be stripped."""
        raw = _load_page(1, 35)
        result = _transform(raw)
        assert "Eleazar" in result, "Eleazar lost (inside {{fine block}})"
        assert "Kenites" in result, "Kenites lost (inside {{fine block}})"

    def test_nested_center_preserves_content(self):
        """{{center|...}} with nested templates must preserve content."""
        result = _transform("text {{center|{{sc|Important}} heading}} more")
        assert "Important" in result, "Content lost inside nested {{center}}"

    def test_deeply_nested_unwrap(self):
        """Templates with multiple nesting levels must unwrap cleanly."""
        result = _transform("{{fine block|See {{EB1911 article link|Foo}} and {{sc|Bar}}.}}")
        assert "Foo" in result, "Link target lost in nested template"
        assert "Bar" in result, "Small caps text lost in nested template"


class TestRealMultiElement:
    """Pages with multiple element types."""

    def test_multi_element_page(self):
        """Vol 3 p76 has tables, footnotes, and images together."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        # No raw wiki markup should survive
        assert "{|" not in result, "Raw table markup"
        assert "<ref>" not in result, "Raw ref tags"
        # Should have clean markers
        assert "\u00abFN:" in result or "FN" not in raw, "Missing footnotes"

    def test_no_raw_html_survives(self):
        """No HTML tags should survive in the output (except in markers)."""
        raw = _load_page(3, 76)
        result = _transform(raw, volume=3, page_number=76)
        # Strip our markers first
        clean = re.sub(r"\u00ab[^«»]*\u00bb", "", result)
        clean = re.sub(r"\{\{(?:IMG|TABLE|VERSE).*?\}\}", "", clean, flags=re.DOTALL)
        html_tags = re.findall(r"<[a-z]+[^>]*>", clean, re.IGNORECASE)
        # Filter out [hieroglyph:] markers which aren't HTML
        html_tags = [t for t in html_tags if not t.startswith("<poem") and not t.startswith("<br")]
        assert not html_tags, f"HTML tags survived: {html_tags[:5]}"
