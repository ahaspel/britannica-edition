"""The roster carries the spelling the SOURCE uses most, not the longest one.

`accrete_author_link_contributors` picked its canonical name with
`max(names, key=len)`.  Length is not evidence: when a person's name is spelled
several ways across the corpus, the longest string wins by accident, and when
the variants are the same length the winner is whatever order the dict happened
to yield.

Wentworth-Sheilds is the case that exposed it.  The corpus spells him three
times:

    vol  6 p7    [[Author:Francis Edward Wentworth-Sheilds|…]]   (front matter)
    vol  6 p864  {{EB1911 footer initials|Francis Ernest …|F. E. W.-S.}}
    vol 29 p981  [[Author:Francis Ernest Wentworth-Sheilds|…]]   (master index)

and vol 29 wraps the printed forms in `{{SIC}}` with a transcriber's note:
"(The original has the error EDWARD instead of ERNEST.)"  Every variant is
exactly 32 characters, so the old rule was a coin flip — and it landed on the
misprint, shipping "Francis Edward Wentworth-Sheilds" to the live site.

By mode, Ernest wins 2-1.  This is what `harvest_author_links` already documents
its `votes` for: "the MODE of what the source actually wrote, not a single index
line".
"""
from britannica.contributors.author_links import _canonical_name


def test_the_mode_wins_not_the_longest():
    """Two spellings of the same length; the frequent one is the evidence."""
    names = [
        "Francis Edward Wentworth-Sheilds",   # the printed error, once
        "Francis Ernest Wentworth-Sheilds",   # the article's own footer
        "Francis Ernest Wentworth-Sheilds",   # the vol 29 master index
    ]
    assert len(set(map(len, names))) == 1, "the point is that length cannot separate these"
    assert _canonical_name(names) == "Francis Ernest Wentworth-Sheilds"


def test_a_longer_name_does_not_beat_a_more_frequent_one():
    """The old rule's actual failure mode, stated as a property.

    A single florid variant must not outvote the spelling the source uses
    repeatedly.
    """
    names = ["John Smith", "John Smith", "John Smith",
             "John Fitzgerald Smith"]
    assert _canonical_name(names) == "John Smith"


def test_length_still_breaks_a_genuine_tie():
    """With no mode to appeal to, prefer the fuller form.

    One occurrence each: nothing says which is right, and the longer form
    carries more of what the source wrote — the old behaviour, kept for the
    case it was actually reasonable for.
    """
    assert _canonical_name(["J. Smith", "John Smith"]) == "John Smith"


def test_a_single_name_is_its_own_canon():
    assert _canonical_name(["Solitary Author"]) == "Solitary Author"
