"""A jump within the page is decided by its target, never by its display.

UNITED KINGDOM's `[[#Regular Army|regular, or general service, army]]` names
the article's own Regular Army heading.  `resolve_xref` tries the side with
more content words first, so the four-word display ran ahead of the two-word
target and bound REGULAR, a word-history article (2026-11-06).  A `#…` target
(normalized `: REGULAR ARMY`) belongs to THIS article; its display is prose.
"""
from __future__ import annotations

import pytest

from wikikit.link_resolver import LinkResolver

UK, REGULAR = "27-0621-uk.json", "23-0065-regular.json"
ARTICLES = [
    {"filename": UK, "title": "UNITED KINGDOM OF GREAT BRITAIN AND IRELAND",
     "article_type": "article"},
    {"filename": REGULAR, "title": "REGULAR", "article_type": "article"},
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
    r._sec_cache = {UK: [{"title": "Army", "slug": "army", "level": 2},
                         {"title": "Regular Army", "slug": "regular-army", "level": 3}],
                    REGULAR: []}
    return r


def test_the_display_does_not_outvote_the_fragment(resolver):
    fn, sec, _cut = resolver.resolve_xref(
        ": REGULAR ARMY", "regular, or general service, army", self_fn=UK)
    assert (fn, sec) == (UK, "regular-army")


def test_a_missing_heading_binds_nothing_else(resolver):
    """OILS's "Oil Testing" is a run-in subhead, not a heading: no anchor,
    and the display must not go looking for another article."""
    fn, sec, _cut = resolver.resolve_xref(": ARMY RESERVE", "regular army", self_fn=UK)
    assert fn is None or fn == UK
