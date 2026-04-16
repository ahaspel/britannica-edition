"""Dry-run boundary detection and diff against current DB state.

Runs detect_boundaries(volume) in memory and compares the result to
the Articles table. Prints articles that would be added, removed,
renamed, or re-spanned.

Usage:
    python tools/compare_detect_boundaries.py [vol ...]
    python tools/compare_detect_boundaries.py            # all volumes
"""
import io
import sys
from collections import defaultdict

# Force UTF-8 stdout so diff output survives titles with accented chars.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from britannica.db.models import Article
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.detect_boundaries import detect_boundaries


def current_articles(volume: int):
    session = SessionLocal()
    try:
        rows = (
            session.query(Article)
            .filter(Article.volume == volume)
            .order_by(Article.page_start, Article.title)
            .all()
        )
        return [
            (a.title, a.page_start, a.page_end, a.article_type)
            for a in rows
        ]
    finally:
        session.close()


def diff_volume(volume: int) -> None:
    current = current_articles(volume)
    new = detect_boundaries(volume)
    new_tuples = [
        (a.title, a.page_start, a.page_end, a.article_type)
        for a in new
    ]

    # Map by title for matching
    cur_by_title = defaultdict(list)
    for t in current:
        cur_by_title[t[0]].append(t)
    new_by_title = defaultdict(list)
    for t in new_tuples:
        new_by_title[t[0]].append(t)

    removed = []
    added = []
    changed = []  # title present in both but span differs

    for title, rows in cur_by_title.items():
        if title not in new_by_title:
            removed.extend(rows)
    for title, rows in new_by_title.items():
        if title not in cur_by_title:
            added.extend(rows)
    for title in cur_by_title.keys() & new_by_title.keys():
        cur_rows = cur_by_title[title]
        new_rows = new_by_title[title]
        # Simple 1:1 compare when single row each side
        if len(cur_rows) == 1 and len(new_rows) == 1:
            if cur_rows[0][1:] != new_rows[0][1:]:
                changed.append((cur_rows[0], new_rows[0]))
        else:
            # Multi-row: note any difference
            if sorted(cur_rows) != sorted(new_rows):
                changed.append((cur_rows, new_rows))

    print(f"=== Volume {volume} ===")
    print(f"  current: {len(current)} articles")
    print(f"  new:     {len(new_tuples)} articles")
    print(f"  delta:   {len(new_tuples) - len(current):+d}")
    print()

    if removed:
        print(f"REMOVED ({len(removed)}):")
        for title, ps, pe, at in removed:
            print(f"  - {title}  ({at}, ws {ps}-{pe})")
        print()

    if added:
        print(f"ADDED ({len(added)}):")
        for title, ps, pe, at in added:
            print(f"  + {title}  ({at}, ws {ps}-{pe})")
        print()

    if changed:
        print(f"SPAN-CHANGED ({len(changed)}):")
        for cur, new_ in changed:
            print(f"  ~ {cur}  =>  {new_}")
        print()

    if not removed and not added and not changed:
        print("  (no changes)")
        print()


def main() -> None:
    if len(sys.argv) > 1:
        vols = [int(v) for v in sys.argv[1:]]
    else:
        vols = list(range(1, 29))
    for v in vols:
        diff_volume(v)


if __name__ == "__main__":
    main()
