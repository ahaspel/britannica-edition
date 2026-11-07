"""An address naming a real article at a heading it does not print lands on the
ARTICLE — never on whatever its display word fuzzes to.

UNITED KINGDOM's `{{11link|English|England#Inhabitants}}`: ENGLAND has no
"Inhabitants" heading, the colon form gave up, and the display "English" bound
ENGLISH LANGUAGE.  A Wikisource qualifier (`Senegal (colony)`) is the wiki's,
not EB1911's; inside SENEGAL itself the result is the self-abstain, not COLONY.
"""
from __future__ import annotations

import pytest

from wikikit.link_resolver import LinkResolver

UK, ENGLAND, ENG_LANG = "27-0621-uk.json", "09-0403-england.json", "09-0587-englang.json"
SENEGAL, COLONY, D, DS = "24-0669-senegal.json", "06-0705-colony.json", "07-0700-d.json", "x.json"
ARTICLES = [
    {"filename": UK, "title": "UNITED KINGDOM OF GREAT BRITAIN AND IRELAND", "article_type": "article"},
    {"filename": ENGLAND, "title": "ENGLAND", "article_type": "article"},
    {"filename": ENG_LANG, "title": "ENGLISH LANGUAGE", "article_type": "article"},
    {"filename": SENEGAL, "title": "SENEGAL", "article_type": "article"},
    {"filename": COLONY, "title": "COLONY", "article_type": "article"},
    {"filename": D, "title": "D", "article_type": "article"},
]


class _Emb:
    def embed_text(self, text):
        return None

    def cosine(self, fn, q):
        return 0.0

    def vector_of(self, fn):
        return None


@pytest.fixture(scope="module")
def resolver():
    r = LinkResolver(article_index=ARTICLES, embeddings=_Emb(),
                     section_index={}, openings={})
    r._emb = _Emb()
    r._sec_cache = {a["filename"]: [] for a in ARTICLES}
    r._sec_cache[ENGLAND] = [{"title": "VI. Population", "slug": "vi-population", "level": 2}]
    return r


def test_an_unprinted_heading_lands_on_its_article(resolver):
    fn, sec, _ = resolver.resolve_xref("ENGLAND: INHABITANTS", "English", self_fn=UK,
                                       embedded=True)
    assert (fn, sec) == (ENGLAND, None)


def test_a_wiki_qualifier_inside_its_own_article_is_a_self_reference(resolver):
    fn, _sec, _ = resolver.resolve_xref("SENEGAL (COLONY): INHABITANTS", "native",
                                        self_fn=SENEGAL, embedded=True)
    assert fn is None


def test_a_wiki_qualifier_elsewhere_lands_on_the_article(resolver):
    fn, _sec, _ = resolver.resolve_xref("SENEGAL (COLONY): HISTORY", "Senegal",
                                        self_fn=UK, embedded=True)
    assert fn == SENEGAL


def test_the_topic_path_keeps_colon_forms_inert(resolver):
    assert resolver._resolve_colon("ENGLAND: INHABITANTS") is None
