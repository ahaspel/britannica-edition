"""Integration-test fixtures.

Post-FLIP, ``detect_boundaries(volume)`` moved to ``super_detect`` and delegates
the volume-stream + heading walk to ``super_walker``; both modules hold their
OWN ``SessionLocal`` import.  Tests still patch ``detect_boundaries.SessionLocal``
(its home for ``persist_articles`` / ``wipe_articles``), so without also patching
the two walk modules the heading walk reads the real DB instead of the seeded
test DB (page numbers then mismatch → KeyError, or wrong articles surface).

This autouse fixture mirrors the patch onto ``super_detect`` and ``super_walker``
for every integration test, so each test only has to patch the legacy site as
before and call ``super_detect.detect_boundaries``.
"""
import pytest

from britannica.db.models import Article
from britannica.pipeline.stages import super_detect as super_detect_stage
from britannica.pipeline.stages import super_walker as super_walker_stage
from britannica.pipeline.stages import transform_articles as transform_articles_stage


@pytest.fixture(autouse=True)
def _patch_walk_session(monkeypatch, test_session_local):
    monkeypatch.setattr(super_detect_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(super_walker_stage, "SessionLocal", test_session_local)


@pytest.fixture()
def transform_titles():
    """MOVE 2: the title is produced in the transform (``walk_article``, the sole
    title site), not at detection.  Returns a callable that, after
    ``persist_articles``, runs the transform to populate ``Article.title``/
    ``title_raw``/``title_display`` — mirrors the real pipeline, where the
    transform stage (classify / assemble) walks each article."""
    def _run(session_factory, volume):
        session = session_factory()
        try:
            for a in (session.query(Article)
                      .filter(Article.volume == volume).all()):
                a.body, a.title_display = transform_articles_stage.walk_article(
                    session, a)
            session.commit()
        finally:
            session.close()
    return _run
