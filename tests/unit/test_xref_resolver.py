from britannica.db.models.article import Article
from britannica.db.models.cross_reference import CrossReference
from britannica.xrefs.resolver import resolve_xref_exact


def test_resolve_xref_exact_matches_article_title_case_insensitively() -> None:
    articles = [
        Article(id=1, title="ABACUS", volume=1, page_start=1, page_end=1, body=""),
        Article(id=2, title="CALCULATION", volume=1, page_start=2, page_end=2, body=""),
    ]

    xref = CrossReference(
        article_id=1,
        surface_text="See also CALCULATION",
        normalized_target="CALCULATION",
        xref_type="see_also",
        target_article_id=None,
        status="unresolved",
    )

    result = resolve_xref_exact(xref, articles)

    assert result == 2


def test_resolve_xref_exact_returns_none_when_no_match_exists() -> None:
    articles = [
        Article(id=1, title="ABACUS", volume=1, page_start=1, page_end=1, body=""),
    ]

    xref = CrossReference(
        article_id=1,
        surface_text="See ABANDONMENT",
        normalized_target="ABANDONMENT",
        xref_type="see",
        target_article_id=None,
        status="unresolved",
    )

    result = resolve_xref_exact(xref, articles)

    assert result is None