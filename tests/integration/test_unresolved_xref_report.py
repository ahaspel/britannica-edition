from britannica.db.models import SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
from britannica.pipeline.stages import extract_xrefs as extract_xrefs_stage
from britannica.pipeline.stages import resolve_xrefs as resolve_xrefs_stage
from britannica.review import reports as reports_module


def test_unresolved_xref_report_groups_by_article(
    monkeypatch,
    test_session_local,
):
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(extract_xrefs_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(resolve_xrefs_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(reports_module, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        session.add_all(
            [
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=1,
                    raw_text="unused",
                    cleaned_text="«SEC:Abacus»ABACUS\nA calculating device. See also CALCULATION.",
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    cleaned_text="\u00abSEC:Abandon\u00bbABANDON\nTo relinquish. See ABANDONMENT.",
                ),
                # Only CALCULATION exists, so ABANDONMENT should remain unresolved
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=3,
                    raw_text="unused",
                    cleaned_text="«SEC:Calculation»CALCULATION\nThe process of computing.",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    created_articles = detect_boundaries_stage.detect_boundaries(1)
    assert created_articles == 3

    created_xrefs = extract_xrefs_stage.extract_xrefs_for_volume(1)
    assert created_xrefs == 2

    resolved_xrefs = resolve_xrefs_stage.resolve_xrefs_for_volume(1)
    assert resolved_xrefs == 1

    report = reports_module.get_unresolved_xrefs_report(1)

    assert list(report.keys()) == ["ABANDON"]
    assert len(report["ABANDON"]) == 1

    xref = report["ABANDON"][0]
    assert xref.xref_type == "see"
    assert xref.surface_text == "See ABANDONMENT"
    assert xref.normalized_target == "ABANDONMENT"
    assert xref.status == "unresolved"