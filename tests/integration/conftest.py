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

from britannica.pipeline.stages import super_detect as super_detect_stage
from britannica.pipeline.stages import super_walker as super_walker_stage


@pytest.fixture(autouse=True)
def _patch_walk_session(monkeypatch, test_session_local):
    monkeypatch.setattr(super_detect_stage, "SessionLocal", test_session_local)
    monkeypatch.setattr(super_walker_stage, "SessionLocal", test_session_local)
