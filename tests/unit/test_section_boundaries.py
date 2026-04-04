"""Tests for section-based article boundary detection."""
from britannica.pipeline.stages.detect_boundaries import _parse_page_by_sections


def test_named_section_with_bold_creates_article():
    text = '<section begin="Abacus" />\'\'\'ABACUS\'\'\' A calculating device.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABACUS"


def test_multiple_named_sections_with_bold():
    text = (
        '<section begin="Abacus" />\'\'\'ABACUS\'\'\' A calculating device.\n\n'
        '<section begin="Abalone" />\'\'\'ABALONE\'\'\' A type of shellfish.'
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 2
    assert parsed.candidates[0].title == "ABACUS"
    assert parsed.candidates[1].title == "ABALONE"


def test_prefix_text_before_first_section():
    text = (
        "Continuation of previous article.\n\n"
        '<section begin="Abandon" />\'\'\'ABANDON\'\'\' To relinquish.'
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


def test_anonymous_section_with_bold_heading():
    text = '<section begin="s1" />\'\'\'ACARUS,\'\'\' a genus of Arachnids.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ACARUS"


def test_anonymous_section_without_bold_is_continuation():
    """An anonymous section with uppercase text but no bold is continuation."""
    text = '<section begin="s1" />ACARUS, a genus of Arachnids.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 0
    assert "ACARUS" in parsed.prefix_text


def test_anonymous_section_without_heading_is_continuation():
    text = (
        '<section begin="s1" />continuation of previous article text.\n\n'
        '<section begin="Abacus" />\'\'\'ABACUS\'\'\' A device.'
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "continuation" in parsed.prefix_text
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABACUS"


def test_named_section_uses_heading_over_id():
    """The all-caps heading in text takes priority over the section ID."""
    text = '<section begin="Aagesen, Andrew" />\'\'\'AAGESEN, ANDREW\'\'\' (1826-1879), Danish jurist.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "AAGESEN" in parsed.candidates[0].title


def test_named_section_without_bold_first_on_page_creates_article():
    """A named section without bold, if first on the page, creates an article."""
    text = '<section begin="Aagesen, Andrew" />a Danish jurist born in 1826.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "AAGESEN, ANDREW"


def test_named_section_without_bold_after_content_is_continuation():
    """A named section without bold, after other content, is continuation."""
    text = (
        '<section begin="Abacus" />\'\'\'ABACUS\'\'\' A calculating device.\n\n'
        '<section begin="Abacus" />continuation of previous article.'
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABACUS"
    # The second Abacus section (no bold) should be in prefix or continuation
    assert "continuation" in (parsed.prefix_text + " ".join(c.body for c in parsed.candidates))


def test_body_extracted_after_heading():
    text = '<section begin="Abacus" />\'\'\'ABACUS,\'\'\' a calculating device used in antiquity.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    body = parsed.candidates[0].body
    assert "calculating device" in body
    assert "ABACUS" not in body


def test_bold_markers_stripped_for_heading_detection():
    text = '<section begin="Abacus" />\'\'\'ABACUS\'\'\', a calculating device.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert parsed.candidates[0].title == "ABACUS"


def test_single_letter_section_with_bold():
    text = '<section begin="A" />\'\'\'A\'\'\' This letter corresponds to the first symbol.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert parsed.candidates[0].title == "A"


def test_section_with_accented_title():
    text = '<section begin="Auto-da-f\u00e9" />\'\'\'AUTO-DA-F\u00c9\'\'\' the name of a ceremony.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert "F\u00c9" in parsed.candidates[0].title


def test_single_letter_article_about_letter():
    """SEC:T with text about the letter T creates an article."""
    text = "<section begin=\"T\" />'''T''' the last letter in the Semitic alphabet."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "T"


def test_single_letter_section_not_about_letter_is_continuation():
    """SEC:T with bibliography text (not about the letter) is continuation."""
    text = '<section begin="T" />amil. (Portug.), 1679, 8vo.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 0
    assert "amil" in parsed.prefix_text


def test_mixed_case_bold_heading_uses_section_id():
    """SEC:Transvaal with '''Transvaal,''' uses the section ID as title."""
    text = "<section begin=\"Transvaal\" />'''Transvaal,''' an inland colony."
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "TRANSVAAL"


def test_numbered_continuation_section_merges():
    """SEC:Egypt2 without bold heading is continuation, not a new article."""
    text = (
        '<section begin="Egypt" />\'\'\'EGYPT\'\'\' A country in Africa.\n\n'
        '<section begin="Egypt2" />continuation of the Egypt article.'
    )
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "EGYPT"
    assert "continuation" in parsed.prefix_text or "continuation" in parsed.candidates[0].body


def test_part_section_is_continuation():
    """SEC:part1 without bold heading is continuation, not a new article."""
    text = '<section begin="part1" />continuation of previous article text.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 0
    assert "continuation" in parsed.prefix_text


def test_link_wrapped_bold_heading():
    """Bold heading wrapped in [[link|'''TITLE''']] is detected."""
    text = '<section begin="s5" /> [[Portal:Architecture|\'\'\'ARCHITECTURE\'\'\']] (Lat. architectura), the art of building.'
    parsed = _parse_page_by_sections(text)
    assert parsed is not None
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ARCHITECTURE"
