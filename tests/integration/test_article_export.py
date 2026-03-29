import json

from britannica.db.models import SourcePage
from britannica.export import article_json as article_json_module
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
from britannica.pipeline.stages import extract_xrefs as extract_xrefs_stage


def test_export_articles_to_json_writes_article_files(
    monkeypatch,
    test_session_local,
    tmp_path,
):
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(extract_xrefs_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(article_json_module, "SessionLocal", test_session_local)

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

    detect_boundaries_stage.detect_boundaries(1)
    extract_xrefs_stage.extract_xrefs_for_volume(1)

    out_dir = tmp_path / "exports"
    count = article_json_module.export_articles_to_json(1, out_dir)

    assert count == 2

    meta_files = {"index.json", "contributors.json"}
    article_files = sorted(p for p in out_dir.glob("*.json") if p.name not in meta_files)
    assert len(article_files) == 2
    assert (out_dir / "index.json").exists()

    abacus_file = next(p for p in article_files if "ABACUS" in p.name)
    payload = json.loads(abacus_file.read_text(encoding="utf-8"))

    assert payload["title"] == "ABACUS"
    assert payload["volume"] == 1
    assert payload["page_start"] == 1
    assert payload["page_end"] == 1
    assert payload["body"] == "A calculating device. See also CALCULATION."
    assert len(payload["segments"]) == 1
    assert payload["segments"][0]["segment_text"] == "A calculating device. See also CALCULATION."
    assert len(payload["xrefs"]) == 1
    assert payload["xrefs"][0]["surface_text"] == "See also CALCULATION"
    assert payload["xrefs"][0]["normalized_target"] == "CALCULATION"