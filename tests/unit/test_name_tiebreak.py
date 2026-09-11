"""How a contested contributor name is settled: votes, then fullest, then print.

Two ORIGINAL sources print a contributor's name — the per-volume front-matter
tables and the vol 29 master index.  Neither outranks the other as evidence, but
they do not reach us the same way.  The front matter arrives as Wikisource's
proofread wikitext for every volume; vol 29 is proofread for about twelve of its
twenty-seven index pages and comes through our own vision OCR for the rest.  So
on an untranscribed page we cannot tell a printed misprint from an OCR misread.

The cascade that follows from that:

  1. VOTES        a real majority settles it, whatever the sources
  2. LENGTH       the fuller spelling wins — monotonic, so it cannot lose
                  information: 'H. R. Haxton' -> 'Henry Raymond Haxton'
  3. FRONT MATTER settles what length cannot, because it is the reading we can
                  trust: 'G. E. Webber' (OCR, page 980, untranscribed) loses to
                  the front matter's 'C. E. Webber'
  4. folded key   determinism ([[project_determinism_arc]])

Front matter sits at step 3 and not step 2 deliberately.  Winning ALL ties would
undo the expansions, since the front matter is exactly where the abbreviated
forms come from and vol 29 is what prints them in full.

A transcription error in the front matter is reachable through
`data/corrections.json` under the usual `volume:page` key, so the rule does not
have to be perfect — it has to fail into a mechanism we already trust
([[feedback_corrections_json]]).
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pipeline"))

from resolve_contributors_post import pick_winning_spelling  # noqa: E402


def fold(raw: str) -> str:
    return "".join(c for c in raw.lower() if c.isalnum())


def groups(*variants):
    """`{folded key: Counter(raw -> votes)}` — the shape `_canon_name` builds."""
    out = {}
    for raw, n in variants:
        out.setdefault(fold(raw), Counter())[raw] += n
    return out


def test_a_majority_settles_it():
    g = groups(("C. E. Webber", 5), ("Charles Webber", 1))
    assert pick_winning_spelling(g, [fold("Charles Webber")]) == fold("C. E. Webber")


def test_length_beats_the_front_matter():
    """The expansion case, and the reason front matter is step 3 not step 2.

    The front matter prints the initials; vol 29 prints the name in full.  The
    fuller form must win, or the whole class of expansions is lost.
    """
    g = groups(("H. R. Haxton", 1), ("Henry Raymond Haxton", 1))
    assert pick_winning_spelling(
        g, [fold("H. R. Haxton")]) == fold("Henry Raymond Haxton")


def test_front_matter_settles_an_equal_length_tie():
    """Webber — vol 29 page 980, which Wikisource has not transcribed.

    Our OCR reads 'WEBBER, MAJOR-GENERAL G. E.' while that very entry signs
    itself '(C. E. W.)'.  Both spellings are twelve characters, so length cannot
    separate them; the proofread front matter can.
    """
    g = groups(("G. E. Webber", 1), ("C. E. Webber", 1))
    assert pick_winning_spelling(
        g, [fold("C. E. Webber")]) == fold("C. E. Webber")


def test_the_wentworth_contest_keeps_what_the_book_printed():
    """Every PRINTED source spells him Edward; only Wikisource says Ernest.

    The vol 29 index prints 'WENTWORTH-SHIELDS, FRANCIS EDWARD' and the vol 6
    front matter prints 'Francis Edward Wentworth-Sheilds' — a genuine
    disagreement between two printings, both 32 characters.  Front matter
    settles it, and the encyclopedia's own reading stands.

    Wikisource files the man under 'Francis Ernest' and marks the printed EDWARD
    with {{SIC}}, but that name appears nowhere in the book: it reaches us only
    through the transcriber-supplied footer argument, which does not vote.  If it
    is ever to be preferred, that is a deliberate corrections.json decision to
    override the SOURCE, not a transcription fix.
    """
    g = groups(("Francis Edward Wentworth-Shields", 1),      # vol 29, via OCR
               ("Francis Edward Wentworth-Sheilds", 1))      # vol 6 front matter
    assert pick_winning_spelling(
        g, [fold("Francis Edward Wentworth-Sheilds")]
    ) == fold("Francis Edward Wentworth-Sheilds")


def test_with_no_front_matter_it_stays_deterministic():
    """A contributor the front matter never lists — vol 29 introduces some.

    Nothing to appeal to, so the answer must at least not depend on dict order.
    """
    a = pick_winning_spelling(groups(("Alan Smith", 1), ("Alec Smith", 1)), [])
    b = pick_winning_spelling(groups(("Alec Smith", 1), ("Alan Smith", 1)), [])
    assert a == b


def test_a_single_spelling_is_unopposed():
    assert pick_winning_spelling(groups(("Thomas Ashby", 3)), []) == fold("Thomas Ashby")
