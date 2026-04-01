"""Real-data tests using EGYPT article (vol 9).

Tests shoulder headings and plate page handling using actual
Wikisource content from the EGYPT article.
"""
import json
import re
from pathlib import Path

import pytest


RAW_DIR = Path("data/raw/wikisource/vol_09")


def _load_raw(page_number: int) -> str:
    """Load raw_text from cached JSON."""
    path = RAW_DIR / f"vol09-page{page_number:04d}.json"
    if not path.exists():
        pytest.skip(f"Raw data not available: {path}")
    return json.loads(path.read_text(encoding="utf-8"))["raw_text"]


def _clean(raw_text: str) -> str:
    """Run the fetch cleaner on raw wikitext."""
    import sys
    sys.path.insert(0, str(Path("tools/fetch")))
    from fetch_wikisource_pages import clean_wikisource_page_text
    return clean_wikisource_page_text(raw_text)


class TestEgyptShoulderHeadings:
    """Page 43 has shoulder headings for EGYPT article sections."""

    def test_shoulder_headings_preserved(self):
        raw = _load_raw(43)
        cleaned = _clean(raw)

        headings = re.findall(
            r"\u00abSH\u00bb(.*?)\u00ab/SH\u00bb", cleaned
        )
        assert len(headings) >= 2
        assert any("Physical" in h for h in headings)
        assert any("Dress" in h for h in headings)

    def test_shoulder_headings_not_stripped(self):
        """Shoulder headings must not be silently removed."""
        raw = _load_raw(43)
        assert "Shoulder Heading" in raw  # confirm source has them
        cleaned = _clean(raw)
        assert "\u00abSH\u00bb" in cleaned  # they survive cleaning

    def test_shoulder_heading_nested_templates_unwrapped(self):
        """Headings wrapped in {{Fs|108%|...}} should have the wrapper stripped."""
        raw = _load_raw(43)
        cleaned = _clean(raw)
        headings = re.findall(
            r"\u00abSH\u00bb(.*?)\u00ab/SH\u00bb", cleaned
        )
        for h in headings:
            assert "{{" not in h, f"Unstripped template in heading: {h}"
            assert "Fs|" not in h, f"Font-size template leaked: {h}"


class TestEgyptPlatePage:
    """Page 78 is Plate I with images of earliest Egyptian art."""

    def test_plate_has_images(self):
        raw = _load_raw(78)
        cleaned = _clean(raw)

        images = re.findall(r"\{\{IMG:[^}]+\}\}", cleaned)
        assert len(images) >= 5, f"Expected >=5 images on plate, got {len(images)}"

    def test_plate_images_have_filenames(self):
        raw = _load_raw(78)
        cleaned = _clean(raw)

        for m in re.finditer(r"\{\{IMG:([^|}]+)", cleaned):
            filename = m.group(1)
            assert len(filename) > 5, f"Empty or tiny image filename: {filename}"
            assert "Egypt" in filename or "EB1911" in filename

    def test_plate_captions_preserved(self):
        """Image captions from the plate table should survive cleaning."""
        raw = _load_raw(78)
        cleaned = _clean(raw)

        # These captions are in the original plate table
        expected_fragments = [
            "TATOOED FEMALE",
            "IVORY HAWK",
        ]
        for fragment in expected_fragments:
            assert fragment in cleaned, (
                f"Plate caption '{fragment}' missing from cleaned output"
            )

    def test_plate_captions_readable(self):
        """Captions should be readable text, not garbled with image dimensions."""
        raw = _load_raw(78)
        cleaned = _clean(raw)

        # Image dimension strings (x250px}}) should not appear in text
        # outside of IMG markers
        text_outside_imgs = re.sub(r"\{\{IMG:[^}]+\}\}", "", cleaned)
        assert "x250px" not in text_outside_imgs, (
            "Image dimensions leaked into caption text"
        )
