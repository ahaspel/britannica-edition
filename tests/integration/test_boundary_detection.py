from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage

SEC = "\u00abSEC:"
END = "\u00bb"


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
                    cleaned_text=(
                        f"{SEC}Abacus{END}ABACUS\n"
                        "The encyclopaedia entry begins here.\n\n"
                        f"{SEC}Abalone{END}ABALONE\n"
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
                    cleaned_text=f"{SEC}Abandon{END}ABANDON\nTo relinquish, desert, or give up.",
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
                    cleaned_text=f"{SEC}Abalone{END}ABALONE\nA type of shellfish.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    cleaned_text="Continuation text with no section markers.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    cleaned_text=f"{SEC}Abandon{END}ABANDON\nTo relinquish.",
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
        abalone = (
            session.query(Article)
            .filter(Article.title == "ABALONE")
            .first()
        )
        assert abalone.page_end == 2
        assert "Continuation" in abalone.body
    finally:
        session.close()
