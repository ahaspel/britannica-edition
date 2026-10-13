"""Where the patch chain reads and writes (paths from the book root).

  data/readings/vol_NN/STEM.json   our scan readings, judged and corrected
                                   (each correction in provenance.corrected)
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
  data/staging/patches/            the chain's working files (not kept)"""
from pathlib import Path

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
WORK = Path("data/staging/patches")
WORK.mkdir(parents=True, exist_ok=True)


def reading(stem: str) -> Path:
    """Our reading of a page, e.g. vol22-page0706."""
    return READINGS / ("vol_" + stem[3:5]) / (stem + ".json")
