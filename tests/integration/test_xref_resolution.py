from britannica.db.models import Article, CrossReference, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
from britannica.pipeline.stages import extract_xrefs as extract_xrefs_stage
from britannica.pipeline.stages import resolve_xrefs as resolve_xrefs_stage


def test_extract_and_resolve_xrefs_exact_match(
    monkeypatch,
    test_session_local,
):
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(extract_xrefs_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(resolve_xrefs_stage, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="unused",
                    cleaned_text="ABACUS\nA calculating device. See also CALCULATION.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    cleaned_text="CALCULATION\nThe process of computing.",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created_articles = detect_boundaries_stage.detect_boundaries(1)
    assert created_articles == 2

    created_xrefs = extract_xrefs_stage.extract_xrefs_for_volume(1)
    assert created_xrefs == 1

    resolved_xrefs = resolve_xrefs_stage.resolve_xrefs_for_volume(1)
    assert resolved_xrefs == 1

    session = test_session_local()
    try:
        xrefs = session.query(CrossReference).all()
        assert len(xrefs) == 1

        xref = xrefs[0]
        assert xref.surface_text == "See also CALCULATION"
        assert xref.normalized_target == "CALCULATION"
        assert xref.status == "resolved"
        assert xref.target_article_id is not None

        target = session.get(Article, xref.target_article_id)
        assert target is not None
        assert target.title == "CALCULATION"
    finally:
        session.close()