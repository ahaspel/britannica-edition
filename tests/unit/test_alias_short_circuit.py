"""An exact ALIAS hit is not automatically the answer when the source qualified it.

`candidates()` can match the whole parenthesised string exactly — Wikisource's
own disambiguated page names are in the alias overlay — and hand back ONE
article.  `_xref_pass` then short-circuited on `len(bag) == 1` and returned it
without ever consulting the qualifier, so `Boston (Massachusetts)` bound Boston,
Lincolnshire and `Lima (Peru)` bound Lima, Ohio.  Measured on the corpus: 880
qualified references, 287 of them bypassing the picker this way.

The rule FAILS CLOSED, and that is the whole design.  A first attempt asked
"does this single candidate satisfy the qualifier?" and widened on a NO — but
that test is lexical, so `Alexander I. (tsar)`, whose lead reads "emperor of
Russia" and never says "tsar", read as a CONTRADICTION and was rebound to a
Scottish king.  An A/B over the real resolver caught 156 such changes, many of
them destroying correct links.  Not being able to verify a bind is not evidence
that it is wrong.  So: widen, and take the widened answer ONLY when the source's
own qualifier positively decided it (method `qualifier` / `qualifier-kind`); a
prose-cosine guess never overturns an exact hit.

Re-measured with that rule: 811 unchanged, 69 changed, all improvements.
"""
from __future__ import annotations

import pytest

from britannica.link_resolver import LinkResolver


ARTICLES = [
    # a same-title family: the alias points at the FIRST, the qualifier names the second
    {"filename": "01-0001-lincs.json", "title": "BOSTON", "article_type": "article"},
    {"filename": "01-0002-mass.json", "title": "BOSTON", "article_type": "article"},
    # a family whose qualifier is a SYNONYM of nothing in either lead
    {"filename": "02-0001-russia.json", "title": "ALEXANDER I", "article_type": "article"},
    {"filename": "02-0002-scot.json", "title": "ALEXANDER I", "article_type": "article"},
]

OPENINGS = {
    "01-0001-lincs.json": "a municipal and parliamentary borough and seaport of "
                          "Lincolnshire, England, on the river Witham.",
    "01-0002-mass.json": "the capital of the state of Massachusetts, U.S.A., in "
                         "Suffolk county, on Boston Bay.",
    # NEITHER lead contains the word "tsar" — the qualifier cannot be verified
    # lexically against either candidate.  The rule must stay out of it.
    "02-0001-russia.json": "emperor of Russia, son of the grand-duke Paul "
                           "Petrovich, afterwards the emperor Paul.",
    "02-0002-scot.json": "king of Scotland, was the fourth son of Malcolm "
                         "Canmore by his second wife Margaret.",
}


class _Emb:
    """A stub whose cosine is constant, so any change can only come from the
    qualifier — never from the semantic rung."""
    def embed_text(self, text):
        return None

    def cosine(self, fn, q):
        return 0.0

    def vector_of(self, fn):
        return None


@pytest.fixture(scope="module")
def resolver():
    r = LinkResolver(article_index=ARTICLES, embeddings=_Emb(),
                     section_index={}, openings=OPENINGS)
    r._emb = _Emb()
    from britannica.topic_fisher import Fisher
    r.fisher = Fisher(r._emb, r._opening)
    r._openings = OPENINGS
    r._open_cache = dict(OPENINGS)
    return r


def test_qualifier_overrides_a_single_alias_candidate(resolver, monkeypatch):
    """The alias resolves the whole string to Lincolnshire; "Massachusetts" is
    stated, and exactly one lead states it, so the qualifier wins."""
    monkeypatch.setattr(resolver, "candidates",
                        lambda name, superset=False: (
                            [("01-0001-lincs.json", "BOSTON")], "exact")
                        if "(" in name else
                        ([("01-0001-lincs.json", "BOSTON"),
                          ("01-0002-mass.json", "BOSTON")], "exact"))
    fn, _sect, _cut = resolver.resolve_xref("Boston (Massachusetts)", None,
                                            prose="", embedded=True)
    assert fn == "01-0002-mass.json"


def test_unverifiable_qualifier_leaves_the_alias_alone(resolver, monkeypatch):
    """`(tsar)` appears in NEITHER lead.  The picker abstains, so the alias
    stands — this is the case whose mishandling rebound Alexander I. of Russia
    to a king of Scotland."""
    monkeypatch.setattr(resolver, "candidates",
                        lambda name, superset=False: (
                            [("02-0001-russia.json", "ALEXANDER I")], "exact")
                        if "(" in name else
                        ([("02-0001-russia.json", "ALEXANDER I"),
                          ("02-0002-scot.json", "ALEXANDER I")], "exact"))
    fn, _sect, _cut = resolver.resolve_xref("Alexander I. (tsar)", None,
                                            prose="", embedded=True)
    assert fn == "02-0001-russia.json"


def test_unqualified_reference_is_untouched(resolver, monkeypatch):
    """No qualifier, no widening — the short-circuit behaves exactly as before."""
    monkeypatch.setattr(resolver, "candidates",
                        lambda name, superset=False: (
                            [("01-0001-lincs.json", "BOSTON")], "exact"))
    fn, _sect, _cut = resolver.resolve_xref("Boston", None, prose="",
                                            embedded=True)
    assert fn == "01-0001-lincs.json"
