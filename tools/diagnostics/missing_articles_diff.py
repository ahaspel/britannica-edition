"""Produce the canonical missing/spurious-articles list by diffing two
article-index TSV files.

CANONICAL RULE: an article is "missing" iff its NORMALIZED TITLE does
not appear anywhere in the same VOLUME of the NEW file (and vice versa
for "spurious").  Page numbers are ignored — page boundaries can
shift by a leaf or two without changing article identity.

Normalization:
  - Strip quote markers: «I», «/I», «B», «/B», ''' , ''
  - Strip square-bracketed annotations [...]   (editor additions)
  - Collapse whitespace
  - Uppercase

Parentheticals (X) are KEPT because they distinguish articles (e.g.
PROTEUS (AMPHIBIAN) vs PROTEUS (mythology)).

Usage:
  python tools/diagnostics/missing_articles_diff.py OLD.tsv NEW.tsv
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8") if hasattr(
    sys.stdout, "reconfigure") else None

DEFAULT_OLD = "data/derived/article_index_OLD_detect.tsv"
DEFAULT_NEW = "data/derived/article_index_full_new.tsv"
BASELINED = {3, 7, 8, 12, 13, 18, 19, 22, 23, 25, 26, 27, 28}

QUOTE_RE = re.compile(r"«/?(?:B|I|SC)»|'{2,}")
BRACKET_RE = re.compile(r"\s*\[[^\]]*\]\s*")
WS_RE = re.compile(r"\s+")


_APOSTROPHE_RE = re.compile(r"[‘’ʼʻʽ'`]")


def normalize(title):
    t = QUOTE_RE.sub("", title)
    t = BRACKET_RE.sub("", t)
    t = _APOSTROPHE_RE.sub("'", t)  # all apostrophe forms → straight
    t = WS_RE.sub(" ", t).strip().upper().rstrip(",.;:")
    return t


def _title_col(header):
    """The title column is always last in the index TSV schema.
    Schema may be 5-col (legacy) or 7-col (with printed pages)."""
    return len(header) - 1


def load(path, vols=None):
    """Return (header, {vol: {normalized_title: row}}).  Later duplicates
    overwrite (rare — we'd want to flag but for now last-wins)."""
    by_vol = defaultdict(dict)
    with Path(path).open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        title_idx = _title_col(header)
        for row in reader:
            if len(row) <= title_idx:
                continue
            vol = int(row[0])
            if vols is not None and vol not in vols:
                continue
            by_vol[vol][normalize(row[title_idx])] = row
    return header, by_vol


def diff(old_path, new_path, vols, label_old="OLD", label_new="NEW"):
    """Returns (header, missing, spurious).  header is taken from OLD
    so the caller can re-emit rows with whatever schema OLD used."""
    old_header, old = load(old_path, vols)
    _new_header, new = load(new_path, vols)
    missing = []
    spurious = []
    for vol in sorted(vols):
        old_titles = set(old.get(vol, {}).keys())
        new_titles = set(new.get(vol, {}).keys())
        for ntitle in old_titles - new_titles:
            missing.append((vol, old[vol][ntitle]))
        for ntitle in new_titles - old_titles:
            spurious.append((vol, new[vol][ntitle]))
    missing.sort(key=lambda r: (r[0], int(r[1][1])))
    spurious.sort(key=lambda r: (r[0], int(r[1][1])))
    return old_header, missing, spurious


def main():
    old_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OLD
    new_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_NEW

    header, missing, spurious = diff(old_path, new_path, BASELINED)
    title_idx = _title_col(header)
    # printed pages live at indices 3,4 in the 7-col schema; absent in 5-col
    has_printed = "printed_page_start" in header

    out_m = Path("data/derived/missing_articles.tsv")
    out_s = Path("data/derived/spurious_articles.tsv")
    for out_path, rows in [(out_m, missing), (out_s, spurious)]:
        with out_path.open("w", encoding="utf-8") as f:
            f.write("\t".join(header) + "\n")
            for _, row in rows:
                f.write("\t".join(row) + "\n")

    print(f"Comparing volumes: {sorted(BASELINED)}")
    print(f"  OLD: {old_path}")
    print(f"  NEW: {new_path}")
    print()
    print(f"MISSING ({len(missing)}) → {out_m}")
    print(f"SPURIOUS ({len(spurious)}) → {out_s}")
    print()
    for label, rows in [("MISSING", missing), ("SPURIOUS", spurious)]:
        print(f"=== {label} ({len(rows)}) ===")
        if has_printed:
            print(f"{'vol':>3}  {'printed':>11}  {'leaves':>10}  title")
            for vol, row in rows:
                pps, ppe = row[3], row[4]
                ls, le = row[1], row[2]
                pstr = pps if pps == ppe else f"{pps}-{ppe}"
                lstr = ls if ls == le else f"{ls}-{le}"
                print(f"{vol:>3}  {pstr:>11}  {lstr:>10}  {row[title_idx]}")
        else:
            print(f"{'vol':>3}  {'leaves':>10}  title")
            for vol, row in rows:
                ls, le = row[1], row[2]
                lstr = ls if ls == le else f"{ls}-{le}"
                print(f"{vol:>3}  {lstr:>10}  {row[title_idx]}")
        print()


if __name__ == "__main__":
    main()
