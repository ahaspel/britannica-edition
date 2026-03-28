from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage


def test_detect_boundaries_handles_continuation_then_new_heading_same_page(
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
                    cleaned_text="ABALONE\nA type of shellfish.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    cleaned_text=(
                        "Continuation of the abalone article on the next page.\n\n"
                        "ABANDON\n"
                        "To relinquish, desert, or give up."
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

        abalone = next(a for a in articles if a.title == "ABALONE")
        abandon = next(a for a in articles if a.title == "ABANDON")

        assert abalone.page_start == 1
        assert abalone.page_end == 2
        assert abalone.body == (
            "A type of shellfish.\n"
            "Continuation of the abalone article on the next page."
        )

        assert abandon.page_start == 2
        assert abandon.page_end == 2
        assert abandon.body == "To relinquish, desert, or give up."

        abalone_segments = (
            session.query(ArticleSegment)
            .filter(ArticleSegment.article_id == abalone.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )

        assert len(abalone_segments) == 2
        assert abalone_segments[0].segment_text == "A type of shellfish."
        assert (
            abalone_segments[1].segment_text
            == "Continuation of the abalone article on the next page."
        )
    finally:
        session.close()