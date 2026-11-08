"""An address names its article AND a heading; among same-named articles the
heading picks the one that prints it, and the address leads a wordier display.

ROME is four articles (the city's history and three towns): `Rome#Republic`
bound a town; `China#History` and `Turkey#History` bound nothing at their
heading; `Senegal (colony)#Inhabitants` reached the river, or COLONY.  And
CALIPHATE's `Egypt#Mahommedan`, displayed "Egypt: History (§ Mahommedan)",
lost its section to the display's colon reading, tried first for its words.
"""
from __future__ import annotations

import pytest

from wikikit.link_resolver import LinkResolver

REF = "05-0000-referrer.json"
ROME, ROME_NY, ROME_GA = "23-0614-rome.json", "23-0718-romeny.json", "23-0718-romega.json"
RIVER, COLONY_SN, COLONY = "24-0669-senriver.json", "24-0670-sencolony.json", "06-0705-colony.json"
EGYPT = "09-0033-egypt.json"
POPES, FAMILY = "12-0591-gregory.json", "12-0601-gregory.json"
ARTICLES = [
    {"filename": POPES, "title": "GREGORY", "article_type": "article"},
    {"filename": FAMILY, "title": "GREGORY", "article_type": "article"},
    {"filename": REF, "title": "CALIPHATE", "article_type": "article"},
    {"filename": ROME, "title": "ROME", "article_type": "article"},
    {"filename": ROME_NY, "title": "ROME", "article_type": "article"},
    {"filename": ROME_GA, "title": "ROME", "article_type": "article"},
    {"filename": RIVER, "title": "SENEGAL", "article_type": "article"},
    {"filename": COLONY_SN, "title": "SENEGAL", "article_type": "article"},
    {"filename": COLONY, "title": "COLONY", "article_type": "article"},
    {"filename": EGYPT, "title": "EGYPT", "article_type": "article"},
]


class _Emb:
    def embed_text(self, text):
        return None

    def cosine(self, fn, q):
        return 0.0

    def vector_of(self, fn):
        return None


def _sec(title):
    slug = title.lower().replace(" ", "-")
    return {"title": title, "slug": slug, "level": 2}


@pytest.fixture(scope="module")
def resolver():
    r = LinkResolver(article_index=ARTICLES, embeddings=_Emb(), section_index={},
                     openings={POPES: "the name of sixteen popes and one anti-pope.",
                               FAMILY: "the name of a Scottish family, many members of "
                                       "which attained high eminence"})
    r._emb = _Emb()
    r._sec_cache = {a["filename"]: [] for a in ARTICLES}
    r._sec_cache[ROME] = [_sec("Republic"), _sec("Middle Ages")]
    r._sec_cache[COLONY_SN] = [_sec("Inhabitants"), _sec("History")]
    r._sec_cache[RIVER] = [_sec("Course")]
    r._sec_cache[EGYPT] = [_sec("Mahommedan"), _sec("Ancient")]
    return r


def test_the_heading_picks_the_homonym_that_prints_it(resolver):
    fn, sec, _ = resolver.resolve_xref("ROME: REPUBLIC", "Rome", self_fn=REF, embedded=True)
    assert (fn, sec) == (ROME, "republic")


def test_a_qualified_name_with_homonyms_is_picked_by_its_heading(resolver):
    fn, sec, _ = resolver.resolve_xref("SENEGAL (COLONY): HISTORY", "Senegal",
                                       self_fn=REF, embedded=True)
    assert (fn, sec) == (COLONY_SN, "history")


def test_inside_the_picked_article_it_is_a_jump_within_the_page(resolver):
    fn, sec, _ = resolver.resolve_xref("SENEGAL (COLONY): INHABITANTS", "native",
                                       self_fn=COLONY_SN, embedded=True)
    assert (fn, sec) == (COLONY_SN, "inhabitants")


def test_homonyms_none_of_which_print_the_heading_stay_unpicked(resolver):
    assert resolver._resolve_colon("ROME: COUNCILS", whole_article=True) is None


def test_without_a_heading_the_qualifier_picks_through_the_fisher(resolver):
    # GREGORY the popes prints no per-pope heading; `(Popes)` decides — not the
    # Scottish family.  The address `Gregory (Popes)/Gregory XII` folds to `#`.
    fn, sec, _ = resolver.resolve_xref("GREGORY (POPES): GREGORY XII", "Gregory XII.",
                                       self_fn=REF, embedded=True)
    assert (fn, sec) == (POPES, None)


def test_an_address_leads_a_wordier_display(resolver):
    fn, sec, _ = resolver.resolve_xref("EGYPT: MAHOMMEDAN", "Egypt: History (§ Mahommedan)",
                                       self_fn=REF, embedded=True)
    assert (fn, sec) == (EGYPT, "mahommedan")
