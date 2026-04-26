"""Tests for _wrap_resolved_xrefs_in_body.

The export stage takes the extractor's already-resolved xrefs and
propagates them into the body text as «LN:filename|target|display«/LN»
markers so prose mentions render as links, not just the xref panel
at the bottom.
"""
from britannica.db.models import Article, CrossReference
from britannica.export.article_json import _wrap_resolved_xrefs_in_body


class _FakeSession:
    """Minimal stand-in for SQLAlchemy Session — only .get(Article, id)
    is called by the wrap function."""
    def __init__(self, articles_by_id: dict[int, Article]):
        self._by_id = articles_by_id

    def get(self, cls, id_):
        if cls is Article:
            return self._by_id.get(id_)
        return None


def _make_article(id_, volume, page, section, title):
    return Article(
        id=id_, volume=volume, page_start=page, page_end=page,
        section_name=section, title=title, article_type="article",
    )


def _make_xref(xref_type, surface, target, target_id=None, status="resolved"):
    return CrossReference(
        article_id=999,
        surface_text=surface,
        normalized_target=target,
        xref_type=xref_type,
        target_article_id=target_id,
        status=status,
    )


# ---------- basic wrap ----------

def test_wraps_qv_target_in_body() -> None:
    target = _make_article(1, 25, 630, "sparta", "SPARTA")
    session = _FakeSession({1: target})
    body = "some text about the earliest of those at Sparta (q.v.) here"
    xref = _make_xref(
        "qv", "those at Sparta (q.v.)", "SPARTA", target_id=1,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "02-0390-s5", session)
    assert "«LN:25-0630-sparta-SPARTA.json|SPARTA|Sparta«/LN»" in out
    # The rest of the body is untouched.
    assert "those at " in out
    assert "(q.v.) here" in out


def test_wraps_see_target_in_parenthetical() -> None:
    target = _make_article(2, 1, 295, "s2", "AERONAUTICS")
    session = _FakeSession({2: target})
    body = "quotation ends. (See Aeronautics.) then more text"
    xref = _make_xref(
        "see", "(See Aeronautics.)", "AERONAUTICS", target_id=2,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "02-0483-s2", session)
    assert "(See «LN:01-0295-s2-AERONAUTICS.json|AERONAUTICS|Aeronautics«/LN».)" in out


def test_wraps_see_also_target() -> None:
    target = _make_article(3, 20, 656, "palestine", "PALESTINE: HISTORY")
    session = _FakeSession({3: target})
    body = "content. (See also Palestine: History.)"
    xref = _make_xref(
        "see_also", "(See also Palestine: History.)",
        "PALESTINE: HISTORY", target_id=3,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "15-0398-jews", session)
    assert "|PALESTINE: HISTORY|Palestine: History«/LN»" in out


# ---------- position-precise: don't wrap unrelated mentions ----------

def test_position_precise_wrap_stays_in_surface_range() -> None:
    """If the target word also appears elsewhere in the body (e.g.
    a different 'Pocock'), only the mention inside the xref's own
    surface_text should be wrapped.  Here we test the mechanism by
    using a legit see target and an unrelated earlier mention of
    the same word."""
    target = _make_article(4, 5, 100, "thing", "THING")
    session = _FakeSession({4: target})
    body = (
        "earlier a thing appears here. then a big gap. "
        "and finally (See Thing.) at the end."
    )
    xref = _make_xref("see", "(See Thing.)", "THING", target_id=4)
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    # Wrap lands inside the parenthetical, not on the earlier 'thing'.
    assert "(See «LN:" in out
    assert "earlier a thing appears" in out  # untouched


# ---------- bibliographic filter ----------

def test_bibliographic_year_citation_skipped() -> None:
    target = _make_article(5, 21, 906, "pocock", "POCOCK")
    session = _FakeSession({5: target})
    body = "R. I. Pocock observed patterns. (See Pocock, Quart. Jour. Micr. Sci., 1901.)"
    xref = _make_xref(
        "see", "(See Pocock, Quart. Jour. Micr. Sci., 1901.)",
        "POCOCK", target_id=5,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "02-0302-s5", session)
    # No wrap should happen anywhere — surface is bibliographic noise.
    assert "«LN:" not in out


def test_bibliographic_vol_pp_pattern_skipped() -> None:
    target = _make_article(6, 3, 152, "s7", "BACON")
    session = _FakeSession({6: target})
    body = "see in the notes. (See Letters and Life, i. 268.)"
    xref = _make_xref(
        "see", "(See Letters and Life, i. 268.)",
        "LETTERS", target_id=6,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "03-0152-s7", session)
    assert "«LN:" not in out


# ---------- defensive skips ----------

def test_self_reference_not_wrapped() -> None:
    target = _make_article(7, 2, 483, "s2", "ARCHYTAS")
    session = _FakeSession({7: target})
    body = "Archytas himself wrote that (See Archytas.)"
    xref = _make_xref("see", "(See Archytas.)", "ARCHYTAS", target_id=7)
    # self_stable_id matches the target's stable id — skip.
    out = _wrap_resolved_xrefs_in_body(body, [xref], "02-0483-s2", session)
    assert "«LN:" not in out


def test_unresolved_xref_not_wrapped() -> None:
    session = _FakeSession({})
    body = "text. (See Phantom.)"
    xref = _make_xref("see", "(See Phantom.)", "PHANTOM", target_id=None)
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    assert "«LN:" not in out


def test_already_wrapped_surface_not_rewrapped() -> None:
    target = _make_article(8, 4, 616, "zambezi", "ZAMBEZI")
    session = _FakeSession({8: target})
    body = (
        "prose about «LN:04-0616-zambezi-ZAMBEZI.json|ZAMBEZI|Zambezi«/LN»"
        " (q.v.) and more"
    )
    xref = _make_xref(
        "qv",
        "«LN:04-0616-zambezi-ZAMBEZI.json|ZAMBEZI|Zambezi«/LN» (q.v.)",
        "ZAMBEZI", target_id=8,
    )
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    # Exactly one LN marker, not two.
    assert out.count("«LN:") == 1


def test_link_xref_type_skipped() -> None:
    target = _make_article(9, 1, 1, "alpha", "ALPHA")
    session = _FakeSession({9: target})
    body = "plain Alpha here without any wrap"
    xref = _make_xref("link", "Alpha", "ALPHA", target_id=9)
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    # link type is handled by the transform-stage marker flow, not here.
    assert "«LN:" not in out


def test_surface_not_in_body_skipped() -> None:
    target = _make_article(10, 1, 1, "thing", "THING")
    session = _FakeSession({10: target})
    body = "alpha beta gamma"
    xref = _make_xref("see", "(See Thing.)", "THING", target_id=10)
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    # Surface isn't present verbatim — don't guess at a different
    # occurrence.
    assert "«LN:" not in out


# ---------- protected spans ----------

def test_htmltable_span_is_not_wrapped_inside() -> None:
    target = _make_article(11, 1, 1, "thing", "THING")
    session = _FakeSession({11: target})
    # Target word sits inside an HTMLTABLE span; the surface happens
    # to match the whole thing, but we must refuse to wrap inside.
    body = (
        "prose «HTMLTABLE:<table><tr><td>See Thing.</td></tr></table>"
        "«/HTMLTABLE» more prose"
    )
    xref = _make_xref("see", "See Thing.", "THING", target_id=11)
    out = _wrap_resolved_xrefs_in_body(body, [xref], "99-9999-xyz", session)
    assert "«LN:" not in out
    # Original table content is intact.
    assert "See Thing.</td>" in out


def test_multiple_xrefs_each_wrapped_once() -> None:
    t1 = _make_article(12, 25, 630, "sparta", "SPARTA")
    t2 = _make_article(13, 1, 295, "s2", "AERONAUTICS")
    session = _FakeSession({12: t1, 13: t2})
    body = (
        "first Sparta (q.v.) then later (See Aeronautics.) at the end"
    )
    x1 = _make_xref("qv", "Sparta (q.v.)", "SPARTA", target_id=12)
    x2 = _make_xref(
        "see", "(See Aeronautics.)", "AERONAUTICS", target_id=13,
    )
    out = _wrap_resolved_xrefs_in_body(body, [x1, x2], "99-9999-xyz", session)
    assert "|SPARTA|Sparta«/LN»" in out
    assert "|AERONAUTICS|Aeronautics«/LN»" in out
    assert out.count("«LN:") == 2


def test_duplicate_same_target_wrapped_only_once() -> None:
    target = _make_article(14, 25, 630, "sparta", "SPARTA")
    session = _FakeSession({14: target})
    body = "first Sparta (q.v.) and again Sparta (q.v.) later"
    x1 = _make_xref("qv", "Sparta (q.v.)", "SPARTA", target_id=14)
    x2 = _make_xref("qv", "Sparta (q.v.)", "SPARTA", target_id=14)
    out = _wrap_resolved_xrefs_in_body(body, [x1, x2], "99-9999-xyz", session)
    # One wrap for the target, not two.
    assert out.count("«LN:") == 1
