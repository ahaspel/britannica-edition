from britannica.cleaners.reflow import reflow_paragraphs


def test_joins_hard_wrapped_lines() -> None:
    text = "The Arctic Slope region is\ndivided into the Anuktuvuk Plateau."
    assert reflow_paragraphs(text) == (
        "The Arctic Slope region is divided into the Anuktuvuk Plateau."
    )


def test_preserves_paragraph_breaks() -> None:
    text = "End of first paragraph.\n\nStart of second paragraph."
    assert reflow_paragraphs(text) == (
        "End of first paragraph.\n\nStart of second paragraph."
    )


def test_joins_wraps_and_preserves_paragraphs() -> None:
    text = (
        "The region is\ndivided into two parts.\n\n"
        "Climate.—From the foregoing\ndescription it is evident."
    )
    assert reflow_paragraphs(text) == (
        "The region is divided into two parts.\n\n"
        "Climate.\u2014From the foregoing description it is evident."
    )


def test_single_line_unchanged() -> None:
    text = "A single line of text."
    assert reflow_paragraphs(text) == "A single line of text."


def test_empty_string() -> None:
    assert reflow_paragraphs("") == ""


def test_drops_blank_lines_within_paragraph() -> None:
    text = "Line one.\n\nLine two."
    assert reflow_paragraphs(text) == "Line one.\n\nLine two."


def test_multiple_wraps_in_one_paragraph() -> None:
    text = "first\nsecond\nthird\nfourth"
    assert reflow_paragraphs(text) == "first second third fourth"
