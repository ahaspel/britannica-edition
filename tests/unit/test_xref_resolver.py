from britannica.db.models.article import Article
from britannica.db.models.cross_reference import CrossReference
from britannica.xrefs.resolver import disambiguate_among, resolve_xref_exact


def test_resolve_xref_exact_matches_article_title_case_insensitively() -> None:
    articles = [
        Article(id=1, title="ABACUS", volume=1, page_start=1, page_end=1, body=""),
        Article(id=2, title="CALCULATION", volume=1, page_start=2, page_end=2, body=""),
    ]

    xref = CrossReference(
        article_id=1,
        surface_text="See also CALCULATION",
        normalized_target="CALCULATION",
        xref_type="see_also",
        target_article_id=None,
        status="unresolved",
    )

    result = resolve_xref_exact(xref, articles)

    assert result == 2


def test_resolve_xref_exact_returns_none_when_no_match_exists() -> None:
    articles = [
        Article(id=1, title="ABACUS", volume=1, page_start=1, page_end=1, body=""),
    ]

    xref = CrossReference(
        article_id=1,
        surface_text="See ABANDONMENT",
        normalized_target="ABANDONMENT",
        xref_type="see",
        target_article_id=None,
        status="unresolved",
    )

    result = resolve_xref_exact(xref, articles)

    assert result is None


# ---------- collision disambiguation ----------

def _make_article(id_, title, body=""):
    return Article(
        id=id_, title=title, volume=28, page_start=1084, page_end=1084,
        body=body, article_type="article",
    )


def _link_xref(article_id, target, display):
    surface = f"«LN:{target}|{display}«/LN»"
    return CrossReference(
        article_id=article_id,
        surface_text=surface,
        normalized_target=target.upper(),
        xref_type="link",
        target_article_id=None,
        status="unresolved",
    )


def test_disambiguate_drops_self_reference() -> None:
    """The ZÜRICH case: canton article links to 'Zürich' which matches
    both the canton (self) and the city; self-reference should be
    excluded, leaving only the city as the target."""
    canton = _make_article(101, "ZÜRICH", body="one of the cantons of Switzerland")
    city = _make_article(102, "ZÜRICH", body="the capital of the Swiss canton")
    xref = _link_xref(canton.id, "Zürich", "Zürich (city)")

    result = disambiguate_among(xref, [canton, city])

    assert result == city.id


def test_disambiguate_uses_display_parenthesis_with_synonym() -> None:
    """Editor wrote `(city)` in display; city article's body says
    'the capital' (synonym of city).  Should pick the city even when
    the linking article is unrelated (not in the candidate set)."""
    canton = _make_article(101, "ZÜRICH", body="one of the cantons of Switzerland")
    city = _make_article(102, "ZÜRICH", body="the capital of the Swiss canton; the finest town")
    xref = _link_xref(999, "Zürich", "Zürich (city)")  # unrelated linker

    result = disambiguate_among(xref, [canton, city])

    assert result == city.id


def test_disambiguate_picks_shah_over_pasha() -> None:
    """ABBAS I: two historical figures (shah of Persia vs pasha of
    Egypt).  Display disambiguator '(shah)' should pick the shah."""
    pasha = _make_article(
        201, "ABBAS I",
        body="(1813–1854), pasha of Egypt, was a son of Tusun Pasha",
    )
    shah = _make_article(
        202, "ABBAS I",
        body="(c. 1557–1628), shah of Persia, called the Great",
    )
    xref = _link_xref(999, "Abbas I", "Abbas I (shah)")

    result = disambiguate_among(xref, [pasha, shah])

    assert result == shah.id


def test_disambiguate_falls_back_to_first_on_no_signal() -> None:
    """No self-reference, no display disambiguator: fall back to
    the first candidate deterministically (matches pre-fix silent-
    pick behavior so no working link regresses)."""
    a1 = _make_article(301, "ABDERA", body="an ancient seaport town in Spain")
    a2 = _make_article(302, "ABDERA", body="a town on the coast of Thrace")
    xref = _link_xref(999, "Abdera", "Abdera")  # unrelated linker, no hint

    result = disambiguate_among(xref, [a1, a2])

    # First candidate wins — deterministic, matches the legacy
    # first-wins behavior of resolve_xref_exact.
    assert result == a1.id


def test_resolve_xref_exact_is_collision_aware() -> None:
    """Verify the collision-aware logic lands through the public
    `resolve_xref_exact` entry point too (not just disambiguate_among)."""
    canton = _make_article(401, "ZÜRICH", body="one of the cantons")
    city = _make_article(402, "ZÜRICH", body="the capital, a town")
    xref = _link_xref(canton.id, "Zürich", "Zürich (city)")

    result = resolve_xref_exact(xref, [canton, city])

    assert result == city.id


def test_disambiguate_single_candidate_returns_it() -> None:
    """Baseline: one candidate, no collision, no rules fire."""
    only = _make_article(501, "PARIS", body="the capital of France")
    xref = _link_xref(999, "Paris", "Paris")

    result = disambiguate_among(xref, [only])

    assert result == only.id


def test_disambiguate_empty_candidates_returns_none() -> None:
    xref = _link_xref(999, "Nowhere", "Nowhere")
    assert disambiguate_among(xref, []) is None