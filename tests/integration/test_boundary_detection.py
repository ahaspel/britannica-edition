from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage


def test_detect_boundaries_with_section_markers(
    monkeypatch,
    test_session_local,
):
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="unused",
                    wikitext=(
                        '<section begin="Abacus" />\'\'\'ABACUS,\'\'\'\n'
                        "The encyclopaedia entry begins here.\n\n"
                        '<section begin="Abalone" />\'\'\'ABALONE,\'\'\'\n'
                        "A type of shellfish."
                    ),
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    wikitext="Continuation of the abalone article on the next page.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    wikitext='<section begin="Abandon" />\'\'\'ABANDON,\'\'\' To relinquish, desert, or give up.',
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(1))
    assert created == 3

    session = test_session_local()
    try:
        articles = (
            session.query(Article)
            .filter(Article.volume == 1)
            .order_by(Article.page_start, Article.title)
            .all()
        )

        assert len(articles) == 3

        abacus = next(a for a in articles if a.title == "ABACUS")
        abalone = next(a for a in articles if a.title == "ABALONE")
        abandon = next(a for a in articles if a.title == "ABANDON")

        assert abacus.page_start == 1
        assert abacus.page_end == 1
        assert "encyclopaedia entry" in abacus.body

        assert abalone.page_start == 1
        assert abalone.page_end == 2
        assert "shellfish" in abalone.body
        assert "Continuation" in abalone.body

        assert abandon.page_start == 3
        assert abandon.page_end == 3
        assert "relinquish" in abandon.body

    finally:
        session.close()


def test_detect_boundaries_continuation_without_sections(
    monkeypatch,
    test_session_local,
):
    """Pages without section markers are pure continuation."""
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="unused",
                    wikitext='<section begin="Abalone" />\'\'\'ABALONE,\'\'\' A type of shellfish.',
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    wikitext="Continuation text with no section markers.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    wikitext='<section begin="Abandon" />\'\'\'ABANDON,\'\'\' To relinquish.',
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(1))
    assert created == 2

    session = test_session_local()
    try:
        abalone = (
            session.query(Article)
            .filter(Article.title == "ABALONE")
            .first()
        )
        assert abalone.page_end == 2
        assert "Continuation" in abalone.body
    finally:
        session.close()


def test_named_section_without_bold_is_continuation(
    monkeypatch,
    test_session_local,
):
    """A named section without a bold heading is continuation, not a new article."""
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="unused",
                    wikitext='<section begin="Huss" />\'\'\'HUSS,\'\'\' John (c. 1373-1415), Bohemian reformer.',
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    wikitext='<section begin="Huss, John" />spiritual teaching that influenced later movements.',
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    wikitext='<section begin="Hussar" />\'\'\'HUSSAR,\'\'\' a light cavalry soldier.',
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(1))
    assert created == 2

    session = test_session_local()
    try:
        huss = session.query(Article).filter(Article.title.like("HUSS%")).first()
        assert huss.page_end == 2
        assert "spiritual teaching" in huss.body

        hussar = session.query(Article).filter(Article.title == "HUSSAR").first()
        assert hussar.page_start == 3
    finally:
        session.close()
