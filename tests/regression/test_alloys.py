"""Regression tests for ALLOYS (Vol 1, pp. 746–751).

ALLOYS is a multi-page article with:
- 3 plates on page 747, each with a different title (ALLOYS, GUN-MAKING, IRON AND STEEL)
- Footnotes
- 2 inline images
- 2 contributors (Roberts-Austen, Neville)
- The plate page should NOT break the article boundary
"""

from britannica.db.models import Article, ArticleSegment

from .conftest import _run_pipeline


def test_alloys_boundary_detection(monkeypatch, regression_session, alloys_pages):
    """ALLOYS should be detected as a single article spanning pages 746–751."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        alloys = (
            session.query(Article)
            .filter(Article.title == "ALLOYS", Article.article_type != "plate")
            .first()
        )
        assert alloys is not None, "ALLOYS article not found"
        assert alloys.page_start == 746
        # The article should continue past the plate page
        assert alloys.page_end >= 748, (
            f"ALLOYS should continue past plate page 747, but ends at {alloys.page_end}"
        )
    finally:
        session.close()


def test_alloys_plate_page_creates_plate_entries(monkeypatch, regression_session, alloys_pages):
    """Page 747 should produce plate entries, not regular articles."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        plates = (
            session.query(Article)
            .filter(Article.article_type == "plate", Article.volume == 1)
            .all()
        )
        plate_titles = sorted(p.title for p in plates)

        # Should have separate plate entries for each section
        assert len(plates) >= 2, (
            f"Expected multiple plate entries for multi-section plate page, got {len(plates)}: {plate_titles}"
        )
    finally:
        session.close()


def test_alloys_plate_has_distinct_titles(monkeypatch, regression_session, alloys_pages):
    """Multi-section plate page should produce plates with different titles."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        plates = (
            session.query(Article)
            .filter(Article.article_type == "plate", Article.volume == 1)
            .all()
        )
        plate_titles = [p.title for p in plates]

        # The plate page has sections titled ALLOYS, GUN-MAKING, IRON AND STEEL
        unique_titles = set(plate_titles)
        assert len(unique_titles) >= 2, (
            f"Multi-section plate should have distinct titles, got: {plate_titles}"
        )
    finally:
        session.close()


def test_alloys_article_continues_past_plate(monkeypatch, regression_session, alloys_pages):
    """The plate page should not break the ALLOYS article boundary."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        alloys = (
            session.query(Article)
            .filter(Article.title == "ALLOYS", Article.article_type != "plate")
            .first()
        )
        assert alloys is not None

        # Body should contain content from pages before AND after the plate
        body = alloys.body
        assert len(body) > 10000, (
            f"ALLOYS body seems incomplete: {len(body)} chars (expected >10k for multi-page article)"
        )
    finally:
        session.close()


def test_alloys_has_footnotes(monkeypatch, regression_session, alloys_pages):
    """ALLOYS article should preserve footnote markers."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        alloys = (
            session.query(Article)
            .filter(Article.title == "ALLOYS", Article.article_type != "plate")
            .first()
        )
        assert alloys is not None
        assert "\u00abFN:" in alloys.body, "ALLOYS should contain footnote markers"
    finally:
        session.close()


def test_alloys_no_false_article_splits(monkeypatch, regression_session, alloys_pages):
    """ALLOYS should not be split by internal headings or the plate page."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        # Get all non-plate articles
        articles = (
            session.query(Article)
            .filter(
                Article.volume == 1,
                Article.article_type != "plate",
            )
            .order_by(Article.page_start)
            .all()
        )

        titles = [a.title for a in articles]
        # ALLOYS starts on 746. Other articles on nearby pages are expected
        # (ALLOTROPY, ALLOWANCE, etc.) — those are real articles.
        # What we're checking is that ALLOYS itself is one article, not split.
        alloys_articles = [a for a in articles if a.title == "ALLOYS"]
        assert len(alloys_articles) == 1, (
            f"ALLOYS should be a single article, found {len(alloys_articles)}"
        )
    finally:
        session.close()
