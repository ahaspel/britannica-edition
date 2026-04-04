"""Tests for boundary detection of articles with apostrophes, Mc/Mac prefixes,
and other non-standard casing in titles.

These use real raw wikitext from the source pages to verify detection.
"""
import json
import re
from pathlib import Path

import pytest

from britannica.pipeline.stages.detect_boundaries import (
    _preprocess_wikitext,
    _parse_page_by_sections,
    _split_on_bold_headings,
)

RAW_DIR = Path("data/raw/wikisource")


def _detect_page(vol: int, page: int):
    """Run boundary detection on a single raw page, return ParsedPage."""
    path = RAW_DIR / f"vol_{vol:02d}" / f"vol{vol:02d}-page{page:04d}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    text = _preprocess_wikitext(data["raw_text"])
    parsed = _parse_page_by_sections(text)
    if parsed is None:
        parsed = _split_on_bold_headings(text)
    return parsed


class TestMcMacPrefixes:
    """Articles with Mc/Mac prefixes must be detected as separate articles."""

    def test_mccormick_detected(self):
        """McCORMICK, CYRUS HALL on vol 17 page 221 must be a candidate."""
        parsed = _detect_page(17, 221)
        titles = [c.title for c in parsed.candidates]
        assert any("McCORMICK" in t for t in titles), f"McCORMICK not found in {titles}"

    def test_mccormick_body_clean(self):
        """McCORMICK body must not start with leftover title fragments."""
        parsed = _detect_page(17, 221)
        for c in parsed.candidates:
            if "McCORMICK" in c.title:
                assert not c.body.startswith("cCORMICK"), f"Body has leftover: {c.body[:40]}"
                assert c.body.startswith("(1809"), f"Body should start with date: {c.body[:40]}"
                break
        else:
            pytest.fail("McCORMICK not found")

    def test_mccosh_detected_and_clean(self):
        """McCOSH, JAMES on vol 17 page 221 must be a candidate with clean body."""
        parsed = _detect_page(17, 221)
        for c in parsed.candidates:
            if "McCOSH" in c.title or "MCCOSH" in c.title:
                assert not c.body.startswith("cCOSH"), f"Body has leftover: {c.body[:40]}"
                assert c.body.startswith("(1811"), f"Body should start with date: {c.body[:40]}"
                break
        else:
            titles = [c.title for c in parsed.candidates]
            pytest.fail(f"McCOSH not found in {titles}")

    def test_maccoll_detected_and_clean(self):
        """MacCOLL on vol 17 page 220 must be a candidate with clean body."""
        parsed = _detect_page(17, 220)
        for c in parsed.candidates:
            if "MacCOLL" in c.title or "MACCOLL" in c.title:
                # Body should not start with title fragments
                assert not re.match(r"^[a-z]", c.body), f"Body starts lowercase: {c.body[:40]}"
                break
        else:
            titles = [c.title for c in parsed.candidates]
            pytest.fail(f"MacCOLL not found in {titles}")


class TestApostropheTitles:
    """Articles with curly apostrophes in titles."""

    def test_aarons_rod_body_clean(self):
        """AARON'S ROD body must not start with 'S ROD."""
        parsed = _detect_page(1, 35)
        for c in parsed.candidates:
            if "AARON" in c.title and "ROD" in c.title:
                assert not c.body.startswith("'S"), f"Body has leftover: {c.body[:40]}"
                break

    def test_obrien_detected_and_clean(self):
        """O'BRIEN on vol 19 page 991 must be a candidate with clean body."""
        parsed = _detect_page(19, 991)
        for c in parsed.candidates:
            if "BRIEN" in c.title:
                assert not c.body.startswith("BRIEN"), f"Body has leftover: {c.body[:40]}"
                assert c.body.startswith("(1803"), f"Body should start with date: {c.body[:40]}"
                break
        else:
            titles = [c.title for c in parsed.candidates]
            pytest.fail(f"O'BRIEN not found in {titles}")

    def test_obrien_not_in_oboe(self):
        """O'BRIEN must not be in the prefix (which would be swallowed by OBOE)."""
        parsed = _detect_page(19, 991)
        if parsed.prefix_text:
            assert "BRIEN" not in parsed.prefix_text or any(
                "BRIEN" in c.title for c in parsed.candidates
            ), "O'BRIEN is in prefix and not detected as candidate"


class TestNoFalseSplits:
    """Ensure we don't over-split on bold text that isn't an article title."""

    def test_vol1_count_stable(self):
        """Vol 1 candidate count should not explode."""
        total = 0
        for path in sorted(RAW_DIR.glob("vol_01/*.json")):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            text = _preprocess_wikitext(data["raw_text"])
            parsed = _parse_page_by_sections(text)
            if parsed is None:
                parsed = _split_on_bold_headings(text)
            if parsed:
                total += len(parsed.candidates)
        # Old count was ~1624, should be slightly higher but not wildly
        assert 1600 < total < 1800, f"Vol 1 has {total} candidates (expected ~1640)"
