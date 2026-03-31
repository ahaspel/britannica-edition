"""Tests for section-based article boundary detection."""
from britannica.pipeline.stages.detect_boundaries import _parse_page_by_sections


def test_named_section_creates_article():
    text = "\u00abSEC:Abacus\u00bbABACUS\nA calculating device."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABACUS"


def test_multiple_named_sections():
    text = (
        "\u00abSEC:Abacus\u00bbABACUS\nA calculating device.\n\n"
        "\u00abSEC:Abalone\u00bbABALONE\nA type of shellfish."
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 2
    assert parsed.candidates[0].title == "ABACUS"
    assert parsed.candidates[1].title == "ABALONE"


def test_prefix_text_before_first_section():
    text = (
        "Continuation of previous article.\n\n"
        "\u00abSEC:Abandon\u00bbABANDON\nTo relinquish."
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "Continuation" in parsed.prefix_text
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABANDON"


def test_no_section_markers_returns_none():
    text = "Just plain text with no section markers."
    parsed = _parse_page_by_sections(text)
    assert parsed is None


def test_anonymous_section_with_heading():
    text = "\u00abSEC:s1\u00bbACARUS, a genus of Arachnids."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ACARUS"


def test_anonymous_section_without_heading_is_continuation():
    text = (
        "\u00abSEC:s1\u00bbcontinuation of previous article text.\n\n"
        "\u00abSEC:Abacus\u00bbABACUS\nA device."
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "continuation" in parsed.prefix_text
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABACUS"


def test_named_section_uses_heading_over_id():
    """The all-caps heading in text takes priority over the section ID."""
    text = "\u00abSEC:Aagesen, Andrew\u00bbAAGESEN, ANDREW (1826-1879), Danish jurist."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    # Title from heading, parenthetical stripped
    assert "AAGESEN" in parsed.candidates[0].title


def test_named_section_falls_back_to_id():
    """If no all-caps heading, use the section ID uppercased."""
    text = "\u00abSEC:Aagesen, Andrew\u00bba Danish jurist born in 1826."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert parsed.candidates[0].title == "AAGESEN, ANDREW"


def test_body_extracted_after_heading():
    text = "\u00abSEC:Abacus\u00bbABACUS, a calculating device used in antiquity."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    body = parsed.candidates[0].body
    assert "calculating device" in body
    assert "ABACUS" not in body


def test_bold_markers_stripped_for_heading_detection():
    text = "\u00abSEC:Abacus\u00bb\u00abB\u00bbABACUS\u00ab/B\u00bb, a calculating device."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert parsed.candidates[0].title == "ABACUS"


def test_single_letter_section():
    text = "\u00abSEC:A\u00bbThis letter corresponds to the first symbol."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert parsed.candidates[0].title == "A"


def test_section_with_accented_title():
    text = "\u00abSEC:Auto-da-f\u00e9\u00bbAUTO-DA-F\u00c9, the name of a ceremony."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "F\u00c9" in parsed.candidates[0].title
