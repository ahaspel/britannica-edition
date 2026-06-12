"""Tests for plate-title composition (``_compose_plate_title``).

NOTE: this file previously also held Mc/Mac- and apostrophe-title
boundary tests that ran through the per-page parser
(``_parse_page_by_sections`` / ``_split_on_bold_headings``).  That parser
was deleted when plate detection moved onto the walk's heading recognizer
(``super_walker.has_article_heading``).  That title-*recognition* behavior
now belongs to ``super_walker._is_title`` + ``elements/_title.produce_title``
and its coverage should live in their tests — TODO: port the McCORMICK /
O'BRIEN / MacCOLL cases there.
"""
import json
from pathlib import Path

from britannica.pipeline.stages.detect_boundaries import _compose_plate_title

RAW_DIR = Path("data/raw/wikisource")


def _raw_page(vol: int, page: int) -> str:
    """Raw wikitext of one source page — the input ``_compose_plate_title``
    sees before any cleaning."""
    path = RAW_DIR / f"vol_{vol:02d}" / f"vol{vol:02d}-page{page:04d}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["raw_text"]


class TestPlateTitleComposition:
    """Plate-title composition must survive the plate-walk migration
    byte-for-byte — a plate title is the only title the detection path
    still composes (every other title is produce_title's now).  These two
    real AEGEAN CIVILIZATION plate inserts pin that output."""

    def test_aegean_plate_i(self):
        raw = _raw_page(1, 278)
        assert _compose_plate_title(raw, 1, 278) == "AEGEAN CIVILIZATION, PLATE I"

    def test_aegean_plate_iii(self):
        raw = _raw_page(1, 284)
        assert _compose_plate_title(raw, 1, 284) == "AEGEAN CIVILIZATION, PLATE III"
