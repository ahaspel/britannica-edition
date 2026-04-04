"""Regression tests for BLANK VERSE (Vol 4, pp. 54–55).

BLANK VERSE is a 2-page literary article with:
- 4 verse/poem quotation blocks ({{VERSE:...}VERSE})
- Heavy italic formatting (book titles, foreign phrases)
- Contributor: Edmund Gosse
"""

from britannica.db.models import Article, ArticleSegment

from .conftest import _run_pipeline


def test_blank_verse_detected(monkeypatch, regression_session, blank_verse_pages):
    """BLANK VERSE should be detected as a single article."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None, "BLANK VERSE article not found"
        assert bv.page_start == 54
        assert bv.page_end == 55
        assert bv.volume == 4
    finally:
        session.close()


def test_blank_verse_has_two_segments(monkeypatch, regression_session, blank_verse_pages):
    """BLANK VERSE spans 2 pages, so should have 2 segments."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None

        segments = (
            session.query(ArticleSegment)
            .filter(ArticleSegment.article_id == bv.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )
        assert len(segments) == 2
    finally:
        session.close()


def test_blank_verse_preserves_verse_blocks(monkeypatch, regression_session, blank_verse_pages):
    """All 4 verse quotation blocks should be preserved."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None

        verse_opens = bv.body.count("{{VERSE:")
        verse_closes = bv.body.count("}VERSE}")
        assert verse_opens >= 4, f"Expected at least 4 verse blocks, found {verse_opens}"
        assert verse_opens == verse_closes, (
            f"Mismatched verse tags: {verse_opens} opens vs {verse_closes} closes"
        )
    finally:
        session.close()


def test_blank_verse_verse_content(monkeypatch, regression_session, blank_verse_pages):
    """Verse blocks should contain recognizable poetry text."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None

        # Surrey's verse quotation
        assert "Who can express the slaughter of that night" in bv.body
        # Marlowe's verse quotation
        assert "Still climbing after knowledge infinite" in bv.body
        # Milton's Paradise Lost quotation
        assert "Arraying with reflected purple and gold" in bv.body
    finally:
        session.close()


def test_blank_verse_has_italic_formatting(monkeypatch, regression_session, blank_verse_pages):
    """Literary titles and foreign phrases should be italicized."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None

        # Book titles should be italicized
        assert "\u00abI\u00bbParadise Lost\u00ab/I\u00bb" in bv.body
        assert "\u00abI\u00bbSamson Agonistes\u00ab/I\u00bb" in bv.body
    finally:
        session.close()


def test_blank_verse_body_continuity(monkeypatch, regression_session, blank_verse_pages):
    """Body should flow continuously across the 2-page boundary."""
    _run_pipeline(monkeypatch, regression_session, blank_verse_pages, volume=4)

    session = regression_session()
    try:
        bv = (
            session.query(Article)
            .filter(Article.title == "BLANK VERSE")
            .first()
        )
        assert bv is not None

        # The article starts with Italian Renaissance origins and ends
        # with 19th-century poets — both should be present
        assert "Trissino" in bv.body, "Should mention Trissino (beginning)"
        assert "Swinburne" in bv.body, "Should mention Swinburne (end)"
    finally:
        session.close()
