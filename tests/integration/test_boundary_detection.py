from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage


def test_detect_boundaries_handles_multi_article_page_and_continuation(
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
                    cleaned_text=(
                        "ABACUS\n"
                        "The encyclopaedia entry begins here.\n\n"
                        "ABALONE\n"
                        "A type of shellfish."
                    ),
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    cleaned_text="Continuation of the abalone article on the next page.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    cleaned_text="ABANDON\nTo relinquish, desert, or give up.",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.detect_boundaries(1)
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
        assert abacus.body == "The encyclopaedia entry begins here."

        assert abalone.page_start == 1
        assert abalone.page_end == 2
        assert abalone.body == (
            "A type of shellfish. "
            "Continuation of the abalone article on the next page."
        )

        assert abandon.page_start == 3
        assert abandon.page_end == 3
        assert abandon.body == "To relinquish, desert, or give up."

        abalone_segments = (
            session.query(ArticleSegment)
            .filter(ArticleSegment.article_id == abalone.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )

        assert len(abalone_segments) == 2
        assert abalone_segments[0].sequence_in_article == 1
        assert abalone_segments[0].segment_text == "A type of shellfish."
        assert abalone_segments[1].sequence_in_article == 2
        assert (
            abalone_segments[1].segment_text
            == "Continuation of the abalone article on the next page."
        )
    finally:
        session.close()


def test_detect_boundaries_filters_false_positive_initials(
    monkeypatch,
    test_session_local,
):
    """Author initials between real articles should not create articles."""
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
                    cleaned_text=(
                        "ABACUS\n"
                        "The encyclopaedia entry begins here.\n"
                        "J.\n\n"
                        "ABALONE\n"
                        "A type of shellfish."
                    ),
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.detect_boundaries(1)
    assert created == 2

    session = test_session_local()
    try:
        articles = (
            session.query(Article)
            .filter(Article.volume == 1)
            .order_by(Article.page_start, Article.title)
            .all()
        )

        assert len(articles) == 2
        titles = [a.title for a in articles]
        assert "J." not in titles
        assert "J" not in titles
        assert "ABACUS" in titles
        assert "ABALONE" in titles

        abacus = next(a for a in articles if a.title == "ABACUS")
        assert "J." in abacus.body
    finally:
        session.close()