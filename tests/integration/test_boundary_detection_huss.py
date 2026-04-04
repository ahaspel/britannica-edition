"""Real-data test: HUSS article spanning vol 14, pages 16-19.

Page 16: ends with named section <section begin="Huss, John"> with bold heading (new article)
Page 17: no section markers (pure continuation)
Page 18: no section markers (pure continuation)
Page 19: named section <section begin="Huss, John"> WITHOUT bold (continuation),
         then <section begin="Hussar"> and <section begin="Hussites"> WITH bold (new articles)

This tests that named sections without bold headings are treated as
continuations rather than creating duplicate articles.
"""
from britannica.db.models import Article, SourcePage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage


def test_huss_continuation_across_pages(
    monkeypatch,
    test_session_local,
):
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", test_session_local)

    # Trimmed real content from vol 14
    page_16 = (
        '<section begin="Husband and Wife" />'
        "(1365) placed beyond the husband's control. "
        "As regards property accruing to the wife.\n\n"
        '<section begin="Hushi" />'
        "'''HUSHI''' (Rumanian Huși), the capital of the department of Falciu.\n\n"
        '<section begin="Huskisson, William" />'
        "'''HUSKISSON, WILLIAM''' (1770-1830), English statesman and financier.\n\n"
        '<section begin="Huss, John" />'
        "'''HUSS''' (or), '''JOHN''' (c. 1373-1415), Bohemian reformer and martyr, "
        "was born at Husinec, a market-town at the foot of the Bohmerwald."
    )

    page_17 = (
        "several years he continued to act in full accord with his archbishop "
        "(Sbynjek, or Sbynko, of Hasenburg). Thus in 1405 he, with "
        "other two masters, was commissioned to examine certain "
        "reputed miracles at Wilsnack."
    )

    page_18 = (
        "against him, and was formerly considered the most important of "
        "his works, though it is mainly a transcript of Wycliffe's work "
        "of the same name."
    )

    page_19 = (
        '<section begin="Huss, John" />\n'
        "spiritual teaching. It might not be easy to formulate precisely "
        "the doctrines for which he died.\n\n"
        '<section begin="Hussar" />'
        "'''HUSSAR,''' originally the name of a soldier belonging to "
        "a corps of light horse raised by Matthias Corvinus.\n\n"
        '<section begin="Hussites" />'
        "'''HUSSITES,''' the name given to the followers of John Huss "
        "(1369-1415), the Bohemian reformer."
    )

    session = test_session_local()
    try:
        session.add_all([
            SourcePage(
                source_name="wikisource", volume=14, page_number=16,
                raw_text="unused", wikitext=page_16,
            ),
            SourcePage(
                source_name="wikisource", volume=14, page_number=17,
                raw_text="unused", wikitext=page_17,
            ),
            SourcePage(
                source_name="wikisource", volume=14, page_number=18,
                raw_text="unused", wikitext=page_18,
            ),
            SourcePage(
                source_name="wikisource", volume=14, page_number=19,
                raw_text="unused", wikitext=page_19,
            ),
        ])
        session.commit()
    finally:
        session.close()

    created = detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(14))

    session = test_session_local()
    try:
        articles = (
            session.query(Article)
            .filter(Article.volume == 14)
            .order_by(Article.page_start, Article.title)
            .all()
        )

        titles = [a.title for a in articles]

        # HUSS should be ONE article spanning pages 16-19 (not two)
        huss_articles = [a for a in articles if "HUSS" in a.title
                         and "HUSSAR" not in a.title
                         and "HUSSITES" not in a.title]
        assert len(huss_articles) == 1, (
            f"Expected 1 HUSS article, got {len(huss_articles)}: "
            f"{[(a.title, a.page_start, a.page_end) for a in huss_articles]}"
        )

        huss = huss_articles[0]
        assert huss.page_start == 16
        assert huss.page_end == 19
        assert "Bohemian reformer" in huss.body
        assert "Wilsnack" in huss.body  # from page 17
        assert "Wycliffe" in huss.body  # from page 18
        assert "spiritual teaching" in huss.body  # from page 19 continuation

        # HUSSAR and HUSSITES should be separate articles on page 19
        hussar = next(a for a in articles if a.title.startswith("HUSSAR"))
        assert hussar.page_start == 19
        assert "light horse" in hussar.body

        hussites = next(a for a in articles if a.title.startswith("HUSSITES"))
        assert hussites.page_start == 19
        assert "followers" in hussites.body

        # Husband and Wife is a continuation (no bold) — goes to prefix
        # HUSHI and HUSKISSON are separate articles
        assert any("HUSHI" in a.title for a in articles)
        assert any("HUSKISSON" in a.title for a in articles)

    finally:
        session.close()
