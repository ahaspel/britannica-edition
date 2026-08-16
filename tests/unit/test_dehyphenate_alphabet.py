"""The dehyphenator repairs WRAPS, reads WHOLE words, and never edits print.

Two rules, each pinned by the failure that forced it:

* One Unicode alphabet.  With an ASCII `[A-Za-z]` word class the runtime
  regex fragmented accented words and applied ANOTHER pair's corpus vote:
  `arrière-pensée` matched as `re-pens` (a real "drop" pair) and lost its
  hyphen corpus-wide; `Saint-Germain-des-Prés` matched as `des-Pr` and
  joined to `desPrés`.  `strings.LETTER` is now the class in BOTH the
  runtime `_HYPHEN_RE` and the map builder.

* The vote applies ONLY across a real separator (a wrap).  A contiguous
  hyphen is what the page prints (user-verified against the scan:
  ALPHABET's `Süd-arabische Chrestomathie` is a full mid-line note), and
  the edition spells the same title solid elsewhere — corpus-majority must
  not overwrite per-page print.  Break-agnostic application was rewriting
  10,540 printed hyphens (`table-land`, `small-pox`) across 4,971 articles.
"""
from britannica.pipeline.stages.elements import _dehyphenate


def test_accented_words_keep_their_hyphens():
    assert _dehyphenate("without arrière-pensée, with") == \
        "without arrière-pensée, with"
    assert _dehyphenate("Saint-Germain-des-Prés") == "Saint-Germain-des-Prés"


def test_contiguous_hyphens_are_print_and_stay():
    """`small-pox` is a "drop" pair by corpus vote, but mid-line it is the
    page's own typography — no separator, no vote."""
    assert _dehyphenate("a small-pox epidemic") == "a small-pox epidemic"
    assert _dehyphenate("Süd-arabische Chrestomathie") == \
        "Süd-arabische Chrestomathie"


def test_wrap_votes_still_apply():
    """Across a real separator the corpus map's verdicts are untouched:
    a mapped wrap split still joins, a kept compound keeps its hyphen."""
    assert _dehyphenate("some-\ntimes") == "sometimes"
    assert _dehyphenate("well-\nknown") == "well-known"


def test_shoulder_headings_vote_contiguously():
    """A shoulder heading is a print INSERT with a narrow measure — its
    contiguous hyphens are the insert's own wraps, transcribed joined, and
    the site gives shoulders the full margin (user ruling): the SH producer
    votes with `contiguous=True`, and the slug is minted from the joined
    form ("differentiation-…", the stable anchor)."""
    from britannica.pipeline.stages.elements import process_shoulder
    out = process_shoulder(None, "Differenti-ation of Roman from Greek alphabet",
                           None, None)
    assert out == ("«SH:differentiation-of-roman-from-greek-alphabet»"
                   "Differentiation of Roman from Greek alphabet«/SH»")
