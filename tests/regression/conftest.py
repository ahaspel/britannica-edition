"""Fixtures for regression tests using real Wikisource page data."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from britannica.db.base import Base
from britannica.db.models import Article, ArticleSegment, SourcePage  # noqa: F401
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
from britannica.pipeline.stages import super_detect as super_detect_stage
from britannica.pipeline.stages import super_walker as super_walker_stage
from britannica.pipeline.stages import transform_articles as transform_articles_stage

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "regression"


def _load_pages_fixture(name: str) -> list[dict]:
    path = FIXTURE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def regression_session(tmp_path):
    db_path = tmp_path / "regression.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    TestSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestSession
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _seed_pages(session_factory, pages_data: list[dict], volume: int):
    """Insert page data matching the real import pipeline.

    The importer stores the raw wikitext in both raw_text and wikitext;
    the walk reads wikitext.  Quote-run conversion (``'''X'''``/``''X''`` →
    ``«B»``/``«I»``) happens in ``preprocess`` (the single source-prep step,
    run by detect's ``volume_stream``), so the seed stores raw wikitext
    exactly as the importer does — no pre-conversion here.
    """
    session = session_factory()
    try:
        for p in pages_data:
            wikitext = p.get("raw_text") or ""
            session.add(SourcePage(
                source_name="wikisource",
                volume=volume,
                page_number=p["page_number"],
                raw_text=wikitext,
                wikitext=wikitext,
            ))
        session.commit()
    finally:
        session.close()


def _run_pipeline(monkeypatch, session_factory, pages_data, volume):
    """Seed pages and run detect_boundaries → transform_articles, matching the real pipeline."""
    # `detect_boundaries` lives in super_detect.py (renamed from
    # super_detect_boundaries last session); `persist_articles` /
    # `wipe_articles` still live in detect_boundaries.py.  Both modules
    # need their `SessionLocal` patched so the test DB is used.
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", session_factory)
    monkeypatch.setattr(super_detect_stage, "SessionLocal", session_factory)
    # Post-FLIP, `detect_boundaries` delegates the stream + heading walk to
    # super_walker (`volume_stream` / `super_walk`), which holds its OWN
    # SessionLocal — patch it too or the walk reads the wrong DB (page numbers
    # then mismatch `pid` → KeyError).
    monkeypatch.setattr(super_walker_stage, "SessionLocal", session_factory)
    _seed_pages(session_factory, pages_data, volume)
    detect_boundaries_stage.persist_articles(
        super_detect_stage.detect_boundaries(volume))
    # Walk each article into its body the way the assemble does
    # (transform_articles is gone; walk_article is the shared one-walk).
    session = session_factory()
    try:
        for a in session.query(Article).filter(Article.volume == volume).all():
            a.body = transform_articles_stage.walk_article(session, a)
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def abbey_pages():
    return _load_pages_fixture("abbey_pages.json")


@pytest.fixture()
def blank_verse_pages():
    return _load_pages_fixture("blank_verse_pages.json")


@pytest.fixture()
def alloys_pages():
    return _load_pages_fixture("alloys_pages.json")
