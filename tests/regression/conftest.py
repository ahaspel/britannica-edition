"""Fixtures for regression tests using real Wikisource page data."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from britannica.db.base import Base
from britannica.db.models import Article, ArticleSegment, SourcePage  # noqa: F401
from britannica.pipeline.stages import clean_pages as clean_pages_stage
from britannica.pipeline.stages import detect_boundaries as detect_boundaries_stage

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

    The real importer stores cleaned_preview as raw_text and sets
    cleaned_text=None. The clean_pages stage then populates cleaned_text.
    """
    session = session_factory()
    try:
        for p in pages_data:
            # Match import_wikisource_pages.py: cleaned_preview → raw_text
            session.add(SourcePage(
                source_name="wikisource",
                volume=volume,
                page_number=p["page_number"],
                raw_text=p["cleaned_preview"],
                cleaned_text=None,
            ))
        session.commit()
    finally:
        session.close()


def _run_pipeline(monkeypatch, session_factory, pages_data, volume):
    """Seed pages and run clean → detect_boundaries, matching the real pipeline."""
    monkeypatch.setattr(clean_pages_stage, "SessionLocal", session_factory)
    monkeypatch.setattr(detect_boundaries_stage, "SessionLocal", session_factory)
    _seed_pages(session_factory, pages_data, volume)
    clean_pages_stage.clean_pages(volume)
    detect_boundaries_stage.detect_boundaries(volume)


@pytest.fixture()
def abbey_pages():
    return _load_pages_fixture("abbey_pages.json")


@pytest.fixture()
def blank_verse_pages():
    return _load_pages_fixture("blank_verse_pages.json")


@pytest.fixture()
def alloys_pages():
    return _load_pages_fixture("alloys_pages.json")
