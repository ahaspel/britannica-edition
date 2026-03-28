from britannica.pipeline.stages.detect_boundaries import (
    _extract_candidates_from_page,
    _is_heading,
)


def test_is_heading_accepts_all_caps_line() -> None:
    assert _is_heading("ABACUS") is True


def test_is_heading_rejects_mixed_case_line() -> None:
    assert _is_heading("Abacus") is False


def test_is_heading_rejects_blank_line() -> None:
    assert _is_heading("") is False


def test_is_heading_rejects_line_without_letters() -> None:
    assert _is_heading("12345") is False


def test_extract_candidates_from_page_returns_multiple_articles() -> None:
    text = (
        "ABACUS\n"
        "The encyclopaedia entry begins here.\n\n"
        "ABALONE\n"
        "A type of shellfish."
    )

    candidates = _extract_candidates_from_page(text)

    assert len(candidates) == 2
    assert candidates[0].title == "ABACUS"
    assert candidates[0].body == "The encyclopaedia entry begins here."
    assert candidates[1].title == "ABALONE"
    assert candidates[1].body == "A type of shellfish."


def test_extract_candidates_from_page_returns_empty_for_no_heading() -> None:
    text = "Continuation of the abalone article on the next page."

    candidates = _extract_candidates_from_page(text)

    assert candidates == []


def test_extract_candidates_from_page_allows_empty_body() -> None:
    text = "ABANDON"

    candidates = _extract_candidates_from_page(text)

    assert len(candidates) == 1
    assert candidates[0].title == "ABANDON"
    assert candidates[0].body == ""