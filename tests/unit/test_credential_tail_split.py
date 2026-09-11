"""A degree tail is credentials, not part of the contributor's name.

The front matter prints a contributor as NAME, POST-NOMINALS, and the roster
keeps those as two fields — `full_name` and `credentials`.  `_clean_name` splits
them at the first comma and then validates the tail, and the validation was

    re.search(r"[A-Z]\\.", credentials)

an upper-case letter IMMEDIATELY followed by a period.  `M.A., LL.D` passes.
`Ph.D` does not — its capital is followed by a lower-case `h` — and neither do
`Litt.D`, `Lic. Theol`, `Bart` or `Jr`.  A tail that failed was folded back into
the name, so the roster shipped these as NAMES with an empty credentials field
beside them:

    'Adolf Gotthard Noreen, Ph.D'
    'Count Ugo Balzani, Litt.D'
    'Sir Henry Thompson, Bart'
    'John Torrey Morse, Jr'
    'William Walker Rockwell, Lic. Theol'
    'Christian Pfister, D-ès.-L'

The source distinguishes name from post-nominals and we merged them — a dropped
attribute, not a naming dispute ([[feedback_forks_are_dropped_attributes]]).  It
needs no vote and no appeal to Wikisource: the book itself carries both parts.

Every string below is taken from the roster as it shipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pipeline"))

from build_contributor_table import _clean_name  # noqa: E402


def test_the_tail_that_already_worked():
    """Regression guard: periods-after-capitals must keep splitting."""
    assert _clean_name("Anson Daniel Morse, M.A., LL.D") == (
        "Anson Daniel Morse", "M.A., LL.D")


def test_a_mixed_case_degree_splits():
    """`Ph.D` — the capital is followed by `h`, which defeated the old test."""
    assert _clean_name("Adolf Gotthard Noreen, Ph.D") == (
        "Adolf Gotthard Noreen", "Ph.D")
    assert _clean_name("Count Ugo Balzani, Litt.D") == (
        "Count Ugo Balzani", "Litt.D")


def test_a_post_nominal_with_no_period_at_all_splits():
    """`Bart` and `Jr` carry no abbreviation point; the word list catches them."""
    assert _clean_name("Sir Henry Thompson, Bart") == (
        "Sir Henry Thompson", "Bart")
    assert _clean_name("John Torrey Morse, Jr") == ("John Torrey Morse", "Jr")


def test_a_semicolon_separates_too():
    """The front matter uses both separators."""
    assert _clean_name("Edward Cuthbert Butler; O.S.B") == (
        "Edward Cuthbert Butler", "O.S.B")


def test_accented_and_multiword_degrees():
    assert _clean_name("Christian Pfister, D-ès.-L") == (
        "Christian Pfister", "D-ès.-L")
    assert _clean_name("William Walker Rockwell, Lic. Theol") == (
        "William Walker Rockwell", "Lic. Theol")


def test_a_name_with_no_tail_is_untouched():
    assert _clean_name("Thomas Ashby") == ("Thomas Ashby", "")


def test_a_non_credential_tail_is_not_split_off():
    """The validation's whole purpose: a comma tail that is NOT post-nominals
    must stay with the name rather than be filed as a degree."""
    base, creds = _clean_name("Agnes Muriel Clay and Edward Wilde")
    assert creds == ""
    assert "Edward Wilde" in base
