"""Regression tests for ALLOYS (Vol 1, pp. 746–751).

ALLOYS is a multi-page article with:
- 1 plate page (747) with 15 microscopy images in an HTML table grid
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


def test_alloys_plate_page_creates_single_plate(monkeypatch, regression_session, alloys_pages):
    """Page 747 should produce one plate entry (not split by internal headings)."""
    _run_pipeline(monkeypatch, regression_session, alloys_pages, volume=1)

    session = regression_session()
    try:
        plates = (
            session.query(Article)
            .filter(Article.article_type == "plate", Article.volume == 1)
            .all()
        )
        assert len(plates) == 1, (
            f"Plate page should produce exactly one plate article, got {len(plates)}: "
            f"{[p.title for p in plates]}"
        )
        assert plates[0].title == "ALLOYS"
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
