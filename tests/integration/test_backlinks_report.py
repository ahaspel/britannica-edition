from britannica.db.models import SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
from britannica.pipeline.stages import extract_xrefs as extract_xrefs_stage
from britannica.pipeline.stages import resolve_xrefs as resolve_xrefs_stage
from britannica.review import reports as reports_module


def test_backlinks_report_groups_by_target_article(
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
                    wikitext='<section begin="Abacus" />\'\'\'ABACUS,\'\'\' See also CALCULATION.',
                ),
                SourcePage(
                    source_name="sample",
                    volume=1,
                    page_number=2,
                    raw_text="unused",
                    wikitext='<section begin="Calculation" />\'\'\'CALCULATION,\'\'\' The process of computing.',
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(1))
    extract_xrefs_stage.extract_xrefs_for_volume(1)
    resolve_xrefs_stage.resolve_xrefs_for_volume(1)

    report = reports_module.get_backlinks_report(1)

    assert list(report.keys()) == ["CALCULATION"]
    assert len(report["CALCULATION"]) == 1

    xref = report["CALCULATION"][0]
    assert xref.surface_text == "See also CALCULATION"
    assert xref.status == "resolved"