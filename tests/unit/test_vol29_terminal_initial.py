"""A trailing INITIAL keeps its period; a terminal full stop does not.

The vol 29 Index of Contributors ends most entries with a full stop:

    MARSDEN, REGINALD GODFREY.      -> Reginald Godfrey Marsden
    VILLARI, PASQUALE.              -> Pasquale Villari

so `_split_name_creds` stripped trailing `.` and `,` from the whole entry.  But
some entries end with an INITIAL, whose period belongs to the name:

    GODFREY, ERNEST H.              -> Ernest H. Godfrey
    FOTHERGILL, JOHN R.             -> John R. Fothergill

Stripping there produced the roster names `Ernest H Godfrey` and `John R
Fothergill` — two contributors shipped with a malformed middle initial.  Neither
existed in the previous build; both appeared when vol 29's fuller forms began
winning the name vote, which is what made a latent bug reachable.
"""
from britannica.contributors.vol29_index import _split_name_creds


def full_name(entry: str) -> str:
    return _split_name_creds(entry)[1]


def test_a_terminal_initial_keeps_its_period():
    assert full_name("GODFREY, ERNEST H.") == "Ernest H. Godfrey"
    assert full_name("FOTHERGILL, JOHN R.") == "John R. Fothergill"


def test_a_terminal_full_stop_is_still_stripped():
    """The behaviour the strip was there for, unchanged."""
    assert full_name("MARSDEN, REGINALD GODFREY.") == "Reginald Godfrey Marsden"
    assert full_name("VILLARI, PASQUALE.") == "Pasquale Villari"


def test_credentials_after_an_initial_still_split():
    """The comma boundary is unaffected by the period rule."""
    display, name, creds = _split_name_creds(
        "WEBBER, MAJOR-GENERAL G. E., C.B., M.Inst.C.E.")
    assert name == "Major-General G. E. Webber"
    assert creds == "C.B., M.Inst.C.E"


def test_no_trailing_punctuation_at_all():
    assert full_name("VILLARI, PASQUALE") == "Pasquale Villari"
