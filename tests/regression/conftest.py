"""Fixtures for regression tests using real Wikisource page data."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from britannica.db.base import Base
from britannica.db.models import Article, ArticleSegment, SourcePage  # noqa: F401
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage
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

    The real importer stores cleaned_preview as raw_text, raw wikitext
    as wikitext, and sets cleaned_text=None.
    """
    session = session_factory()
    try:
        for p in pages_data:
            session.add(SourcePage(
                source_name="wikisource",
                volume=volume,
                page_number=p["page_number"],
                raw_text=p["cleaned_preview"],
                cleaned_text=None,
                wikitext=p.get("raw_text"),
            ))
        session.commit()
    finally:
        session.close()


def _run_pipeline(monkeypatch, session_factory, pages_data, volume):
    """Seed pages and run detect_boundaries → transform_articles, matching the real pipeline."""
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", session_factory)
    monkeypatch.setattr(transform_articles_stage, "SessionLocal", session_factory)
    _seed_pages(session_factory, pages_data, volume)
    detect_boundaries_stage.persist_articles(detect_boundaries_stage.detect_boundaries(volume))
    transform_articles_stage.transform_articles(volume)


@pytest.fixture()
def abbey_pages():
    return _load_pages_fixture("abbey_pages.json")


@pytest.fixture()
def blank_verse_pages():
    return _load_pages_fixture("blank_verse_pages.json")


@pytest.fixture()
def alloys_pages():
    return _load_pages_fixture("alloys_pages.json")
