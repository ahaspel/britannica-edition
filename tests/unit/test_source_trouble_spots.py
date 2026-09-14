"""The read-only triage must not invent precise locations or truncate phrases."""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "diagnostics"))
from source_trouble_spots import detect, locate
from britannica.source_pages import SourcePage


def test_period_candidate_includes_next_whole_word_and_locates():
    text = "They defeated the army He took refuge in London."
    rows = detect(text, "TEST", Counter(), Counter(), {})
    assert len(rows) == 1
    row = rows[0]
    assert row["token"] == "army He took"
    row["volume"] = 1
    locate(row, [SourcePage(1, 32, Path("fixture"), text)])
    assert row["location"] == "literal_unique"
    assert row["source_offset"] == text.index("army")


def test_tied_source_matches_are_not_given_a_page():
    row = dict(token="rnodern", signals=["ocr_variant"], context="rnodern", volume=1)
    pages = [SourcePage(1, n, Path(f"fixture{n}"), "A rnodern account.") for n in (32, 33)]
    locate(row, pages)
    assert row["location"] == "ambiguous"
    assert "ws_page" not in row


def test_unmatched_candidate_remains_in_report_without_a_page():
    row = dict(token="rnodern", signals=["ocr_variant"], context="rnodern", volume=1)
    locate(row, [SourcePage(1, 32, Path("fixture"), "A modern account.")])
    assert row["location"] == "unmatched"
    assert "ws_page" not in row


def test_local_attestation_strengthens_candidate_without_changing_source():
    text = "A rnodern account."
    vocab = Counter({"rnodern": 1, "modern": 100})
    rows = detect(text, "TEST", Counter({"modern": 3}), vocab, {"rnodern": ["modern"]})
    assert rows[0]["signals"] == ["local_variant"]
    assert rows[0]["token"] == "rnodern"
    assert rows[0]["suggested"] == "modern"


def test_encoding_detector_preserves_legitimate_circumflex_words():
    text = "Les Âmes and Âge occur in French titles. The damaged coordinate is 108Â° east."
    rows = detect(text, "TEST", Counter(), Counter(), {})
    encoding = [r for r in rows if "encoding" in r["signals"]]
    assert [r["token"] for r in encoding] == ["Â°"]
