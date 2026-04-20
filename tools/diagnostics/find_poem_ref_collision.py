"""Find articles likely hit by the ``<poem>`` + ``<ref>`` placeholder
collision bug (see SHIP Table XI).

Two independent signals are scored per article.  A clean article scores
0; a SHIP-class victim typically scores high on both:

  VERSE_IMBALANCE
    ``{{VERSE:`` openers vs ``}VERSE}`` closers.  The bug emits
    openers that never close (the REF placeholder got pasted in where
    the closer should have been, truncating the VERSE).

  HTMLTABLE_NESTED
    Depth-tracking walk of ``«HTMLTABLE:`` / ``«/HTMLTABLE»``.
    Reports the maximum nesting depth.  Most articles stay at depth 1.
    Anything > 1 is either a legitimate layout-in-table (INTERPOLATION
    is the only clean case we know) or a SHIP-class collision that
    wrapped one outer table around multiple would-be-siblings.

The pre-fix state is what's on disk; use this as a before-snapshot so
we know what to look at after regen.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OPEN = "\u00abHTMLTABLE:"
CLOSE = "\u00ab/HTMLTABLE\u00bb"


def htmltable_max_depth(body: str) -> int:
    depth = 0
    max_depth = 0
    i = 0
    while i < len(body):
        if body.startswith(OPEN, i):
            depth += 1
            if depth > max_depth:
                max_depth = depth
            i += len(OPEN)
        elif body.startswith(CLOSE, i):
            depth -= 1
            i += len(CLOSE)
        else:
            i += 1
    return max_depth


def scan() -> list[dict]:
    hits: list[dict] = []
    for path in sorted(Path("data/derived/articles").glob("*.json")):
        if path.name in ("index.json", "contributors.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = data.get("body", "")
        if not body:
            continue
        verse_open = body.count("{{VERSE:")
        verse_close = body.count("}VERSE}")
        imbalance = abs(verse_open - verse_close)
        max_depth = htmltable_max_depth(body)
        # Bug signal: either unbalanced VERSE or HTMLTABLE nested > 1
        if imbalance > 0 or max_depth > 1:
            hits.append({
                "filename": path.stem,
                "id": data.get("id"),
                "title": data.get("title"),
                "volume": data.get("volume"),
                "verse_open": verse_open,
                "verse_close": verse_close,
                "imbalance": imbalance,
                "max_htmltable_depth": max_depth,
            })
    return hits


def main() -> int:
    hits = scan()
    # Sort: most-suspicious first — prefer imbalance + depth, then by size.
    hits.sort(
        key=lambda h: (-h["imbalance"], -h["max_htmltable_depth"],
                       -(h["verse_open"] + h["verse_close"]))
    )

    print(f"Total articles with either signal: {len(hits)}")
    print()
    print(f"{'filename':<50} {'vol':>4} {'imbal':>6} {'depth':>6}  title")
    print("-" * 120)
    for h in hits:
        print(
            f"{h['filename']:<50} {h['volume']:>4} "
            f"{h['imbalance']:>6} {h['max_htmltable_depth']:>6}  "
            f"{(h['title'] or '')[:40]}"
        )

    print()
    print("Distribution by (imbalance, depth):")
    bucket = Counter(
        (h["imbalance"], h["max_htmltable_depth"]) for h in hits)
    for (imb, d), n in sorted(bucket.items()):
        print(f"  imbal={imb:>2} depth={d:>2}  n={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
