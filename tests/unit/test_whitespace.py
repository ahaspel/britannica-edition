from britannica.cleaners.whitespace import normalize_whitespace


def test_normalize_whitespace_collapses_spaces_and_tabs() -> None:
    text = "ABACUS\t\t  entry"

    result = normalize_whitespace(text)

    assert result == "ABACUS entry"


def test_normalize_whitespace_normalizes_line_endings() -> None:
    text = "ABACUS\r\n\r\nEntry\rText"

    result = normalize_whitespace(text)

    assert result == "ABACUS\n\nEntry\nText"


def test_normalize_whitespace_collapses_excess_blank_lines() -> None:
    text = "ABACUS\n\n\n\nEntry"

    result = normalize_whitespace(text)

    assert result == "ABACUS\n\nEntry"