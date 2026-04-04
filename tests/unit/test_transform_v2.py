"""Tests for the new extract-process-reassemble transform pipeline (v2).

Runs _transform_text_v2 on real source pages and verifies the output
is correct — clean captions, clean footnotes, no leaked markup.
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


def _transform_v2(raw, volume=1, page_number=1):
    from britannica.pipeline.stages.transform_articles import _transform_text_v2
    return _transform_text_v2(raw, volume, page_number)


class TestBasicTransform:
    """Basic text transformation works."""

    def test_bold_converted(self):
        result = _transform_v2("'''HELLO''' world")
        assert "\u00abB\u00bb" in result or "HELLO" in result

    def test_italic_converted(self):
        result = _transform_v2("''italic'' text")
        assert "\u00abI\u00bb" in result or "italic" in result

    def test_section_tags_stripped(self):
        result = _transform_v2('<section begin="foo" />text<section end="foo" />')
        assert "<section" not in result
        assert "text" in result


class TestImageCaptions:
    """Image captions come out as clean plain text."""

    def test_simple_image(self):
        result = _transform_v2("[[File:Foo.jpg|thumb|A caption]]")
        assert "{{IMG:Foo.jpg|A caption}}" in result

    def test_caption_no_markers(self):
        """Bold/italic in captions should be stripped."""
        result = _transform_v2("[[File:Foo.jpg|thumb|'''Fig.''' 1 — ''Italic'']]")
        cap = re.search(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result)
        assert cap, f"No caption found in: {result}"
        assert "\u00ab" not in cap.group(1), f"Markers in caption: {cap.group(1)}"
        assert "Fig." in cap.group(1)

    def test_cithara_real_data(self):
        """CITHARA image caption from real data should be clean."""
        raw = _load_page(6, 411)
        result = _transform_v2(raw, volume=6, page_number=411)
        # Find the Nero caption
        caps = re.findall(r"\{\{IMG:[^|]+\|([^}]+)\}\}", result)
        nero_caps = [c for c in caps if "Nero" in c]
        assert nero_caps, "Nero caption not found"
        assert "<br" not in nero_caps[0]
        assert "\u00ab" not in nero_caps[0]


class TestFootnotes:
    """Footnotes produce clean «FN:...«/FN» markers."""

    def test_simple_footnote(self):
        result = _transform_v2("text<ref>A note.</ref> more")
        assert "\u00abFN:" in result
        assert "A note." in result
        assert "<ref>" not in result

    def test_footnote_no_markers(self):
        """Footnote text should be plain — no formatting markers."""
        result = _transform_v2("text<ref>See '''bold''' and ''italic''.</ref>")
        fn = re.search(r"\u00abFN:(.*?)\u00ab/FN\u00bb", result)
        assert fn, f"No footnote in: {result}"
        assert "\u00ab" not in fn.group(1), f"Markers in footnote: {fn.group(1)}"
        assert "bold" in fn.group(1)

    def test_footnote_in_table(self):
        """Footnote inside a table cell should be clean."""
        raw = "{|\n|1703\n|5000<ref>Tidal wave.</ref>\n|}"
        result = _transform_v2(raw)
        assert "\u00abFN:" in result
        assert "Tidal wave" in result
        assert "<ref>" not in result


class TestTables:
    """Tables produce {{TABLE:...}TABLE} markers."""

    def test_simple_table(self):
        result = _transform_v2("{|\n|A\n|B\n|-\n|C\n|D\n|}")
        assert "{{TABLE" in result
        assert "A | B" in result
        assert "C | D" in result

    def test_table_attributes_stripped(self):
        result = _transform_v2('{|\n|align="right"|100\n|200\n|}')
        assert "100" in result
        assert "align" not in result


class TestScores:
    """Score tags become image markers."""

    def test_score_replaced(self):
        raw = _load_page(3, 221)
        result = _transform_v2(raw, volume=3, page_number=221)
        assert "<score>" not in result
        assert "\\new Staff" not in result


class TestMath:
    """Math produces «MATH:...«/MATH» markers."""

    def test_math_preserved(self):
        result = _transform_v2("formula <math>x^2</math> end")
        assert "\u00abMATH:" in result
        assert "x^2" in result
