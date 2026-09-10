"""A footer votes once per SPELLING, not once per article it appears in.

The roster's canonical name is decided by a vote over sources.  Footers were
excluded from that vote entirely, with good reason: they are per-article, so a
prolific signer casts one ballot per article and drowns everyone else.  Measured
on the corpus, footers outnumbered the index and front matter 8,628 to 2,931,
and Thomas Ashby alone carried 254 votes against roughly 2.

But the exclusion cost real fidelity — the roster shipped `Adolf Gotthard
Noreen, Ph.D` and `Sir Henry Thompson, Bart` with academic tails flattened into
the name, and was actively shortening `Charles Edmond Akers` to `C. E. Akers`.

The cap resolves it: 254 identical footers are ONE witness repeated, not 254
witnesses, so they get one vote.  What makes this safe rather than merely
balanced is that the footer splits its own vote wherever it disagrees with
itself — which is exactly where a fuller name was at risk.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pipeline"))

from resolve_contributors_post import cap_footer_spellings  # noqa: E402

identity = str


def test_a_repeated_spelling_votes_once():
    """Thomas Ashby's 254 footers are one witness repeated."""
    obs = [("Thomas Ashby", "T. A.")] * 254
    assert cap_footer_spellings(obs, identity) == ["Thomas Ashby"]


def test_each_distinct_spelling_votes_once():
    """Kropotkin, the case that makes the cap safe.

    Raw, `Peter Kropotkin` beat `Peter Alexeivitch Kropotkin` 64-26 and erased
    the middle name.  Capped they are 1-1, and the index breaks the tie toward
    the fuller form.
    """
    obs = ([("Peter Kropotkin", "P. A. K.")] * 64
           + [("Peter Alexeivitch Kropotkin", "P. A. K.")] * 26)
    assert sorted(cap_footer_spellings(obs, identity)) == [
        "Peter Alexeivitch Kropotkin", "Peter Kropotkin"]


def test_frequency_cannot_outweigh_a_rival_spelling():
    """The property, not the instance: 999 to 1 still comes out 1 to 1."""
    obs = [("Short Name", "S. N.")] * 999 + [("Longer Full Name", "S. N.")]
    assert len(cap_footer_spellings(obs, identity)) == 2


def test_order_is_first_seen():
    """Deterministic output — a set here would make the ballot order-dependent
    across runs ([[project_determinism_arc]])."""
    obs = [("B Name", "x"), ("A Name", "x"), ("B Name", "x")]
    assert cap_footer_spellings(obs, identity) == ["B Name", "A Name"]


def test_nameless_signatures_contribute_nothing():
    """A bare `{{EB1911 TAs}}` shortcut carries initials and no name."""
    obs = [(None, "T. A."), ("", "T. A.")]
    assert cap_footer_spellings(obs, identity) == []


def test_spellings_are_compared_after_normalisation():
    """Variants that normalise to one name-proper are ONE spelling.

    `_name_proper` strips dates and titles, so `Adam Sedgwick (1854-1913)` and
    `Adam Sedgwick` must not vote twice for the same person.
    """
    obs = [("Adam Sedgwick (1854-1913)", "A. S."), ("Adam Sedgwick", "A. S.")]
    strip_dates = lambda s: s.split(" (")[0]
    assert cap_footer_spellings(obs, strip_dates) == ["Adam Sedgwick"]
