"""Where the patch chain reads and writes (paths from the book root).

  data/readings/vol_NN/STEM.json   our scan readings, judged and corrected
                                   (each correction in provenance.corrected)
  data/readings/tables/vol_NN/     pages re-read for their TABLES with the table
                                   vocabulary (rules, headings, alignment, braces)
                                   — used for their tables only, whose words and
                                   figures must match the judged reading's
  data/readings/judge/             the evaluation: the disputes between each
                                   reading and Wikisource's page, the judge's
                                   answers, the rulings, the pages judged
  data/readings/vocab.json         the corpus's real words (3+ letters, 5+
                                   uses) the formula builder aligns by
  data/readings/vocab_filter.json  the same, 2+ letters, for the filter's
                                   real-word test (stored when first made)
  data/readings/drop.json          patches dropped after the filter: those the
                                   validator faulted, and those a combination
                                   on one page faulted (drop_faulted.py)
  data/readings/leaks_reviewed.json  patches check_leaks.py flags that were read
                                   and found right, each with why
  data/readings/patch_rulings.json  a person's rulings at the desk's patch
                                   screen, keep or drop: final over every
                                   check (install.py)
  data/staging/patches/            the chain's working files (not kept)"""
import hashlib
import json
from functools import cache
from pathlib import Path

from eb1911.scans import _printed

READINGS = Path("data/readings")
JUDGE = READINGS / "judge"
DISPUTES = JUDGE / "disputes.json"
ANSWERS = JUDGE / "judge.json"
RULINGS = JUDGE / "rulings.json"
PAGES = JUDGE / "judged.txt"
VOCAB = READINGS / "vocab.json"
FILTER_VOCAB = READINGS / "vocab_filter.json"
DROP = READINGS / "drop.json"
LEAKS_REVIEWED = READINGS / "leaks_reviewed.json"
PATCH_RULINGS = READINGS / "patch_rulings.json"
WORK = Path("data/staging/patches")
WORK.mkdir(parents=True, exist_ok=True)


TABLE_READINGS = READINGS / "tables"


def reading(stem: str) -> Path:
    """Our reading of a page, e.g. vol22-page0706."""
    return READINGS / ("vol_" + stem[3:5]) / (stem + ".json")


def text_sha(text: str) -> str:
    """The fingerprint disputes.py records of the page it compared."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def judged_text(stem: str, disputes: dict) -> str:
    """Our page as the judge compared it: the reading's stored raw_text, never
    reassembled.  A ruling holds for the text it was made on; reassembled by
    the live engine, the page moved under the rulings (2026-10-15: figures set
    after their paragraphs) and 32 installed patches lost their sites,
    silently.  Refuses a page whose stored text has changed since it was
    disputed: dispute and judge it again."""
    text = json.loads(reading(stem).read_text(encoding="utf-8"))["raw_text"]
    if text_sha(text) != disputes[stem]["text_sha"]:
        raise SystemExit(f"{label(stem)} ({stem}): our page has changed since the judge compared it "
                         f"— dispute and judge it again")
    return text


@cache
def _printed_pages() -> dict:
    return _printed("printed_pages.json")


def label(stem: str) -> str:
    """A page as the book numbers it: "vol 22 p. 690" for vol22-page0706."""
    v, ws = str(int(stem[3:5])), str(int(stem[-4:]))
    return f"vol {v} p. {_printed_pages().get(v, {}).get(ws, f'?(ws {ws})')}"


def table_reading(stem: str) -> Path:
    """Our re-reading of a page for its tables."""
    return TABLE_READINGS / ("vol_" + stem[3:5]) / (stem + ".json")


def page_files(root: Path) -> list[Path]:
    """Every page's file under `root` (READINGS, TABLE_READINGS), in order."""
    return sorted(root.glob("vol_*/vol*-page*.json"))
