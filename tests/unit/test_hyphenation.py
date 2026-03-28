from britannica.cleaners.hyphenation import fix_hyphenation


def test_fix_hyphenation_merges_single_split_word() -> None:
    text = "encyclo-\npaedia"

    new_text, changes = fix_hyphenation(text)

    assert new_text == "encyclopaedia"
    assert changes == [("encyclo-\npaedia", "encyclopaedia")]


def test_fix_hyphenation_merges_multiple_split_words() -> None:
    text = "encyclo-\npaedia and shell-\nfish"

    new_text, changes = fix_hyphenation(text)

    assert new_text == "encyclopaedia and shellfish"
    assert changes == [
        ("encyclo-\npaedia", "encyclopaedia"),
        ("shell-\nfish", "shellfish"),
    ]


def test_fix_hyphenation_leaves_unsplit_words_alone() -> None:
    text = "ABALONE\nA type of shellfish."

    new_text, changes = fix_hyphenation(text)

    assert new_text == text
    assert changes == []