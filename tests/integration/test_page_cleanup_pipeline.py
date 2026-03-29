from britannica.db.models import SourcePage
from britannica.pipeline.stages import clean_pages as clean_pages_stage


def test_clean_pages_removes_header_and_merges_hyphenation(
    monkeypatch,
    test_session_local,
):
    monkeypatch.setattr(clean_pages_stage, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="HEADER TEXT\n\nABACUS\n\nThe encyclo-\npaedia entry begins here.",
                    cleaned_text=None,
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="HEADER TEXT\n\nABALONE\n\nA type of shellfish.",
                    cleaned_text=None,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    count = clean_pages_stage.clean_pages(1)
    assert count == 2

    session = test_session_local()
    try:
        pages = (
            session.query(SourcePage)
            .filter(SourcePage.volume == 1)
            .order_by(SourcePage.page_number)
            .all()
        )

        assert len(pages) == 2

        assert pages[0].cleaned_text == (
            "ABACUS\n\nThe encyclopaedia entry begins here."
        )
        assert pages[1].cleaned_text == "ABALONE\n\nA type of shellfish."
    finally:
        session.close()