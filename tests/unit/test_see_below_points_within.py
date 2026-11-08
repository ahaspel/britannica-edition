"""A see the text places in the article ("see History, below") that names one of
its own headings points within the page — PORTUGAL's and TUNISIA's bound
HISTORY, the article on historiography.  Without a heading of that name, or
without the cue, the see is an article reference as before ("see FLINT
IMPLEMENTS, below" is the article that follows)."""
from __future__ import annotations

import pytest

from wikikit.export.article_json import _placed_here
from wikikit.link_resolver import LinkResolver

PORTUGAL, HISTORY, FLINT = "22-0148-portugal.json", "13-0543-history.json", "10-0500-flint.json"
ARTICLES = [
    {"filename": PORTUGAL, "title": "PORTUGAL", "article_type": "article"},
    {"filename": HISTORY, "title": "HISTORY", "article_type": "article"},
    {"filename": FLINT, "title": "FLINT IMPLEMENTS", "article_type": "article"},
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
    r = LinkResolver(article_index=ARTICLES, embeddings=_Emb(), section_index={}, openings={})
    r._emb = _Emb()
    r._sec_cache = {a["filename"]: [] for a in ARTICLES}
    r._sec_cache[PORTUGAL] = [{"title": "History", "slug": "history", "level": 1}]
    return r


def test_see_a_heading_below_is_a_jump_within(resolver):
    fn, sec, _ = resolver.resolve_xref("HISTORY", "History", self_fn=PORTUGAL,
                                       trusted=False, here=True)
    assert (fn, sec) == (PORTUGAL, "history")


def test_below_without_an_own_heading_is_the_article(resolver):
    fn, sec, _ = resolver.resolve_xref("FLINT IMPLEMENTS", "Flint Implements",
                                       self_fn=PORTUGAL, trusted=False, here=True)
    assert (fn, sec) == (FLINT, None)


def test_the_cue_is_read_after_the_reference_past_its_closers():
    body = "interest (see «SC»«LN[see]:History|History«/LN»«/SC», below). By"
    assert _placed_here(body, "«LN[see]:History|History«/LN»")
    assert not _placed_here("see «LN[see]:History|History«/LN» and more",
                            "«LN[see]:History|History«/LN»")
