"""Verify that every article in a known-articles fixture exists in the
current DB.  Used as a regression net after any structural pipeline
change (converter, detect-boundaries, etc.) to catch silent article
losses.

Match rule: same as missing_articles_diff.normalize — quote-marker
stripped, brackets stripped, apostrophes regularized, whitespace
collapsed, uppercase.  Page numbers ignored (boundaries can shift by
a leaf).  Volume is enforced (an article moving volumes is treated as
missing — that would be a real bug).

Fixtures live in tests/fixtures/regression/*.tsv with the same schema
as data/derived/article_index*.tsv (vol, page_start, page_end,
printed_page_start, printed_page_end, article_type, title).

Usage:
  python tools/diagnostics/verify_known_articles.py [FIXTURE.tsv]

Defaults to all *.tsv under tests/fixtures/regression/ that match the
articles_*.tsv pattern.  Exits nonzero if any fixture article is
missing from the DB.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

sys.path.insert(0, "tools/diagnostics")
from missing_articles_diff import normalize  # type: ignore

from britannica.db.session import SessionLocal
from britannica.db.models import Article


def _load_fixture(path):
    """Return list of (vol, normalized_title, original_title) tuples."""
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        title_idx = len(header) - 1
        for row in reader:
            if len(row) <= title_idx:
                continue
            vol = int(row[0])
            title = row[title_idx]
            rows.append((vol, normalize(title), title))
    return rows


def _db_titles_by_vol():
    """Return {vol: set(normalized_titles)} for current DB."""
    s = SessionLocal()
    try:
        by_vol = defaultdict(set)
        for a in s.query(Article).all():
            by_vol[a.volume].add(normalize(a.title))
        return by_vol
    finally:
        s.close()


def check_fixture(path, db_titles):
    fixture = _load_fixture(path)
    missing = []
    for vol, ntitle, original in fixture:
        if ntitle not in db_titles.get(vol, set()):
            missing.append((vol, original))
    return fixture, missing


def main():
    if len(sys.argv) > 1:
        fixtures = [Path(p) for p in sys.argv[1:]]
    else:
        fixtures = sorted(
            Path("tests/fixtures/regression").glob("articles_*.tsv"))

    if not fixtures:
        print("No fixtures found.")
        return 1

    db_titles = _db_titles_by_vol()
    total_missing = 0
    for f in fixtures:
        fixture, missing = check_fixture(f, db_titles)
        status = "OK" if not missing else f"FAIL ({len(missing)} missing)"
        print(f"[{status}] {f}  ({len(fixture)} articles)")
        for vol, orig in missing:
            print(f"        vol {vol:>2}: {orig}")
        total_missing += len(missing)

    if total_missing:
        print()
        print(f"TOTAL: {total_missing} fixture articles missing from DB.")
        return 1
    print()
    print("All fixture articles present in DB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
