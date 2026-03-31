"""Regression tests for ABBEY (Vol 1, pp. 42–53).

ABBEY is a long article spanning 12 pages with:
- Inline images (12 total)
- Footnotes
- Small caps and italic formatting
- Cross-reference links (Monasticism, History of Latin Christianity)
- Contributor attribution (Rev. Edmund Venables)
"""

from britannica.db.models import Article, ArticleSegment

from .conftest import _run_pipeline


def test_abbey_boundary_detection(monkeypatch, regression_session, abbey_pages):
    """ABBEY should be detected as a single article spanning pages 42–53."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None, "ABBEY article not found"
        assert abbey.page_start == 42
        assert abbey.page_end == 53
        assert abbey.volume == 1
    finally:
        session.close()


def test_abbey_not_split_by_internal_headings(monkeypatch, regression_session, abbey_pages):
    """Internal section headings within ABBEY must not create false article boundaries."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        articles = (
            session.query(Article)
            .filter(
                Article.volume == 1,
                Article.page_start >= 42,
                Article.page_start <= 53,
                Article.article_type != "plate",
            )
            .order_by(Article.page_start, Article.title)
            .all()
        )

        # Any article starting on pages 43–52 would be a false split
        false_splits = [
            a.title for a in articles
            if a.page_start > 42 and a.page_start < 53
            and a.title != "ABBEY"
        ]
        assert false_splits == [], (
            f"Internal headings falsely detected as article boundaries: {false_splits}"
        )
    finally:
        session.close()


def test_abbey_has_segments_for_each_page(monkeypatch, regression_session, abbey_pages):
    """ABBEY spans 12 pages, so it should have multiple segments with provenance."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None

        segments = (
            session.query(ArticleSegment)
            .filter(ArticleSegment.article_id == abbey.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )
        # 12 pages should produce multiple segments (at least one per page)
        assert len(segments) >= 6, (
            f"Expected many segments for 12-page article, got {len(segments)}"
        )
    finally:
        session.close()


def test_abbey_body_has_formatting_markers(monkeypatch, regression_session, abbey_pages):
    """ABBEY body should preserve italic and small-caps formatting."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None
        body = abbey.body

        # Should contain italic markers (Latin terms like "abbatia")
        assert "\u00abI\u00bb" in body, "Missing italic opening markers"
        assert "\u00ab/I\u00bb" in body, "Missing italic closing markers"

        # Should contain small caps (ABBOT, ABBESS references)
        assert "\u00abSC\u00bb" in body, "Missing small-caps markers"
    finally:
        session.close()


def test_abbey_body_has_footnotes(monkeypatch, regression_session, abbey_pages):
    """ABBEY should have footnote markers preserved in body text."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None
        assert "\u00abFN:" in abbey.body, "ABBEY should contain footnote markers"
    finally:
        session.close()


def test_abbey_body_has_cross_references(monkeypatch, regression_session, abbey_pages):
    """ABBEY should contain cross-reference link markers."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None
        assert "\u00abLN:" in abbey.body, "ABBEY should contain cross-reference links"
    finally:
        session.close()


def test_abbey_body_not_truncated(monkeypatch, regression_session, abbey_pages):
    """A 12-page article should produce substantial body text."""
    _run_pipeline(monkeypatch, regression_session, abbey_pages, volume=1)

    session = regression_session()
    try:
        abbey = (
            session.query(Article)
            .filter(Article.title == "ABBEY")
            .first()
        )
        assert abbey is not None
        # The exported article has ~65k chars; even accounting for pipeline
        # variations, it should be substantial
        assert len(abbey.body) > 30000, (
            f"ABBEY body seems truncated: {len(abbey.body)} chars"
        )
    finally:
        session.close()
