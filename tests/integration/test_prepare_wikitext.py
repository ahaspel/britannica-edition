from britannica.db.models import SourcePage
from britannica.pipeline.stages import prepare_wikitext as prepare_wikitext_stage


def test_prepare_wikitext_converts_quote_runs_to_markers(
    monkeypatch,
    test_session_local,
):
    """prepare_wikitext should rewrite `page.wikitext`, replacing
    MediaWiki bold/italic quote-run markup with the internal `«B»` /
    `«I»` markers every downstream stage expects.  `raw_text` is left
    untouched."""
    monkeypatch.setattr(prepare_wikitext_stage, "SessionLocal", test_session_local)

    raw = "HEADER\n\nABACUS\n\nA word."
    wiki_in = "'''ABACUS'''\n\nA ''bold'' and an <i>italic</i> word."

    session = test_session_local()
    try:
        session.add_all([
            SourcePage(
                source_name="sample",
                volume=1,
                page_number=1,
                raw_text=raw,
                wikitext=wiki_in,
            ),
        ])
        session.commit()
    finally:
        session.close()

    count = prepare_wikitext_stage.prepare_wikitext(1)
    assert count == 1

    session = test_session_local()
    try:
        page = (
            session.query(SourcePage)
            .filter(SourcePage.volume == 1, SourcePage.page_number == 1)
            .one()
        )
        # raw_text is untouched.
        assert page.raw_text == raw
        # wikitext has quote-runs converted.
        assert page.wikitext == (
            "«B»ABACUS«/B»\n\nA «I»bold«/I» and an «I»italic«/I» word."
        )
    finally:
        session.close()
