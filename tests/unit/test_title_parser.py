"""Tests for heading extraction (used by section parser for anonymous sections)."""
from britannica.pipeline.stages.detect_boundaries import _extract_heading


def test_extract_heading_all_caps_word():
    title, remainder = _extract_heading("ABACUS, a calculating device.")
    assert title == "ABACUS"
    assert "calculating" in remainder


def test_extract_heading_multi_word():
    title, remainder = _extract_heading("ACCA LARENTIA, in Roman legend.")
    assert title == "ACCA LARENTIA"


def test_extract_heading_with_comma_name():
    title, remainder = _extract_heading(
        "ACCURSIUS, FRANCISCUS, Italian jurist."
    )
    assert "ACCURSIUS" in title
    assert "FRANCISCUS" in title


def test_extract_heading_no_heading():
    title, remainder = _extract_heading("a continuation of text in lowercase.")
    assert title is None


def test_extract_heading_empty():
    title, remainder = _extract_heading("")
    assert title is None


def test_extract_heading_strips_bold_markers():
    title, remainder = _extract_heading(
        "\u00abB\u00bbABACUS\u00ab/B\u00bb, a device."
    )
    assert title == "ABACUS"


def test_extract_heading_with_accented_chars():
    title, remainder = _extract_heading("AUTO-DA-F\u00c9, a ceremony.")
    assert "F\u00c9" in title
