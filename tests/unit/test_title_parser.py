from britannica.pipeline.stages.detect_boundaries import _is_heading, _parse_page


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