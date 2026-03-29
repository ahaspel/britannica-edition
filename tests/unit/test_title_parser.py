from britannica.pipeline.stages.detect_boundaries import (
    _extract_heading,
    _is_heading,
    _parse_page,
)


# --- Existing behaviour ---


def test_is_heading_accepts_all_caps_line() -> None:
    assert _is_heading("ABACUS") is True


def test_is_heading_rejects_mixed_case_line() -> None:
    assert _is_heading("Abacus") is False


def test_is_heading_rejects_blank_line() -> None:
    assert _is_heading("") is False


def test_is_heading_rejects_line_without_letters() -> None:
    assert _is_heading("12345") is False


def test_parse_page_returns_multiple_articles() -> None:
    text = (
        "ABACUS\n"
        "The encyclopaedia entry begins here.\n\n"
        "ABALONE\n"
        "A type of shellfish."
    )

    parsed = _parse_page(text)

    assert parsed.prefix_text == ""
    assert len(parsed.candidates) == 2
    assert parsed.candidates[0].title == "ABACUS"
    assert parsed.candidates[0].body == "The encyclopaedia entry begins here."
    assert parsed.candidates[1].title == "ABALONE"
    assert parsed.candidates[1].body == "A type of shellfish."


def test_parse_page_returns_prefix_text_when_no_heading() -> None:
    text = "Continuation of the abalone article on the next page."

    parsed = _parse_page(text)

    assert parsed.prefix_text == "Continuation of the abalone article on the next page."
    assert parsed.candidates == []


def test_parse_page_splits_prefix_text_from_later_heading() -> None:
    text = (
        "Continuation of the abalone article on the next page.\n\n"
        "ABANDON\n"
        "To relinquish, desert, or give up."
    )

    parsed = _parse_page(text)

    assert parsed.prefix_text == "Continuation of the abalone article on the next page."
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABANDON"
    assert parsed.candidates[0].body == "To relinquish, desert, or give up."


def test_parse_page_allows_empty_body() -> None:
    text = "ABANDON"

    parsed = _parse_page(text)

    assert parsed.prefix_text == ""
    assert len(parsed.candidates) == 1
    assert parsed.candidates[0].title == "ABANDON"
    assert parsed.candidates[0].body == ""


# --- Author initials rejection ---


def test_is_heading_rejects_single_initial() -> None:
    assert _is_heading("J.") is False


def test_is_heading_rejects_single_letter_initial() -> None:
    assert _is_heading("O.") is False
    assert _is_heading("F.") is False


def test_is_heading_rejects_double_initial() -> None:
    assert _is_heading("J. B.") is False


def test_is_heading_rejects_multi_letter_initials() -> None:
    assert _is_heading("M. O. B. C.") is False


# --- Wikitext artifact rejection ---


def test_is_heading_rejects_chemical_formula_with_arrow() -> None:
    assert _is_heading("CH3CHO \u2192 CH3\u00b7CH \u2192 CH3\u00b7CH") is False


def test_is_heading_rejects_chemical_formula_with_middle_dot() -> None:
    assert _is_heading("R\u00b7CH2OH\u2192 R\u00b7CH2I") is False


def test_is_heading_rejects_formula_with_digits() -> None:
    assert _is_heading("C6H5NHCOCH3") is False
    assert _is_heading("CH3CO2H") is False


def test_is_heading_rejects_roman_numerals() -> None:
    assert _is_heading("II") is False
    assert _is_heading("III") is False
    assert _is_heading("IV") is False
    assert _is_heading("VI") is False
    assert _is_heading("XXXVI") is False


def test_is_heading_rejects_unknown_two_letter_title() -> None:
    assert _is_heading("CH") is False
    assert _is_heading("RO") is False
    assert _is_heading("OF") is False


def test_is_heading_accepts_known_two_letter_title() -> None:
    assert _is_heading("AA") is True
    assert _is_heading("AB") is True
    assert _is_heading("AI") is True


def test_is_heading_rejects_closing_braces() -> None:
    assert _is_heading("}}") is False


def test_is_heading_rejects_mixed_artifacts() -> None:
    assert _is_heading("+T,}}") is False


# --- Parenthetical stripping (etymologies) ---


def test_extract_heading_strips_etymology_parenthetical() -> None:
    title, remainder = _extract_heading(
        "ACANTHUS (the Greek and Latin name for the plant)"
    )
    assert title == "ACANTHUS"
    assert remainder == ""


def test_extract_heading_strips_short_etymology() -> None:
    title, remainder = _extract_heading("ACARUS (from Gr., a mite)")
    assert title == "ACARUS"
    assert remainder == ""


def test_extract_heading_strips_latin_etymology() -> None:
    title, remainder = _extract_heading(
        "ACAULESCENT (Lat. acaulescens, becoming stemless, from a, not, and caulis, a stem)"
    )
    assert title == "ACAULESCENT"
    assert remainder == ""


def test_extract_heading_strips_etymology_preserves_body() -> None:
    title, remainder = _extract_heading(
        "ACARUS (from Gr., a mite), a genus of Arachnids."
    )
    assert title == "ACARUS"
    assert remainder == "a genus of Arachnids."


# --- Parenthetical stripping (dates / alternate names) ---


def test_extract_heading_strips_dates() -> None:
    title, remainder = _extract_heading(
        "ACCIAJUOLI, DONATO (1428\u20131478)"
    )
    assert title == "ACCIAJUOLI, DONATO"
    assert remainder == ""


def test_extract_heading_strips_alternate_name_and_dates() -> None:
    title, remainder = _extract_heading(
        "ACCURSIUS (Ital. Accorso), FRANCISCUS (1182\u20131260)"
    )
    assert title == "ACCURSIUS, FRANCISCUS"
    assert remainder == ""


def test_extract_heading_strips_all_parentheticals_preserves_body() -> None:
    title, remainder = _extract_heading(
        "ACCURSIUS (Ital. Accorso), FRANCISCUS (1182\u20131260), Italian jurist, was born."
    )
    assert title == "ACCURSIUS, FRANCISCUS"
    assert remainder == "Italian jurist, was born."


# --- Trailing period removal ---


def test_extract_heading_strips_trailing_period_allcaps() -> None:
    title, remainder = _extract_heading("ACCENT.")
    assert title == "ACCENT"
    assert remainder == ""


def test_extract_heading_strips_trailing_period_multiword() -> None:
    title, remainder = _extract_heading("ACCOMMODATION BILL.")
    assert title == "ACCOMMODATION BILL"
    assert remainder == ""


def test_extract_heading_strips_trailing_period_biographical() -> None:
    title, remainder = _extract_heading(
        "ACCENT. The word has its origin in Latin."
    )
    assert title == "ACCENT"
    assert remainder == "The word has its origin in Latin."


# --- Regressions: valid headings still work ---


def test_is_heading_accepts_multiword_allcaps() -> None:
    assert _is_heading("ACCA LARENTIA") is True


def test_is_heading_accepts_short_valid_title() -> None:
    assert _is_heading("ACE") is True
    assert _is_heading("AB") is True


def test_extract_heading_simple_allcaps_returns_title_and_empty_remainder() -> None:
    title, remainder = _extract_heading("ABACUS")
    assert title == "ABACUS"
    assert remainder == ""


def test_extract_heading_strips_trailing_descriptor() -> None:
    title, remainder = _extract_heading(
        "AELIAN, Greek, military writer of the 2nd century."
    )
    assert title == "AELIAN"
    assert remainder == "military writer of the 2nd century."


def test_extract_heading_keeps_allcaps_given_name() -> None:
    title, remainder = _extract_heading(
        "ACCURSIUS, FRANCISCUS, Italian jurist."
    )
    assert title == "ACCURSIUS, FRANCISCUS"
    assert remainder == "Italian jurist."


def test_extract_heading_strips_nationality_descriptor() -> None:
    title, remainder = _extract_heading(
        "ABRAHAM IBN DAUD, Jewish, historiographer."
    )
    assert title == "ABRAHAM IBN DAUD"
    assert remainder == "historiographer."


def test_parse_page_with_normalized_titles() -> None:
    text = (
        "ACANTHUS (the Greek name)\n"
        "A genus of plants.\n\n"
        "ACARUS (from Gr., a mite)\n"
        "A genus of Arachnids."
    )

    parsed = _parse_page(text)

    assert len(parsed.candidates) == 2
    assert parsed.candidates[0].title == "ACANTHUS"
    assert parsed.candidates[0].body == "A genus of plants."
    assert parsed.candidates[1].title == "ACARUS"
    assert parsed.candidates[1].body == "A genus of Arachnids."


def test_parse_page_initials_become_body_text() -> None:
    """Author initials between articles should be treated as body text."""
    text = (
        "ABACUS\n"
        "The entry begins here.\n"
        "J.\n\n"
        "ABALONE\n"
        "A type of shellfish."
    )

    parsed = _parse_page(text)

    assert len(parsed.candidates) == 2
    assert parsed.candidates[0].title == "ABACUS"
    assert "J." in parsed.candidates[0].body
    assert parsed.candidates[1].title == "ABALONE"
