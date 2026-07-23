"""The contributor-signoff RECOGNIZER — the local, structural half, split out.

`recognize_signoff_initials` decides "is this parenthetical part signoff-shaped,
and what are its initials" from the part's OWN content — no roster, no corpus.
It is the piece that moves from the late re-scan into the producers: the harvest
runs it on re-scanned parens today, a producer will run it on its own `(…)` next,
and because it is ONE function the candidate set is provably identical
([[feedback_tune_dont_fork]]).  The roster match that CONFIRMS which contributor
is the separate, deferred resolution and is NOT tested here.

Pinned so the recognition contract can't drift as it relocates.
"""
from britannica.pipeline.stages.extract_contributors import (
    recognize_signoff_initials,
)


def test_spaced_initials_are_recognized():
    assert recognize_signoff_initials("A. D.") == "A. D."
    assert recognize_signoff_initials("F. R. C.") == "F. R. C."


def test_marker_wrapping_is_stripped_before_recognition():
    # A signoff rendered inside markup still recognizes to its bare initials.
    assert recognize_signoff_initials("«SC»E. V.«/SC»") == "E. V."


def test_run_together_forms_are_not_signoffs():
    # Dates / abbreviations with no internal space — gate 1.
    assert recognize_signoff_initials("A.D.") is None
    assert recognize_signoff_initials("q.v.") is None


def test_single_initial_is_not_a_signoff():
    # No space → dropped; the ABBEY figure-key collision the gate exists for.
    assert recognize_signoff_initials("M.") is None


def test_lowercase_lead_is_not_a_signoff():
    # A contributor's first initial is always capitalized — gate 2.
    assert recognize_signoff_initials("q. v.") is None
    assert recognize_signoff_initials("l. c.") is None


def test_recognition_is_corpus_free():
    """The whole point of the split: recognition needs no roster.  It returns the
    initials for anything signoff-shaped, INCLUDING an unknown contributor — the
    roster (deferred) is what later keeps or drops it."""
    # "Z. Q." is well-formed initials for nobody in particular; recognition still
    # yields them, and the (untested here) roster match is what would drop it.
    assert recognize_signoff_initials("Z. Q.") == "Z. Q."
