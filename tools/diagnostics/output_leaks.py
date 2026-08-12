#!/usr/bin/env python3
"""Output-leak report — the honest leak oracle over EVERY marker-stream consumer.

    uv run python tools/diagnostics/output_leaks.py [--limit N]

The article ``body`` is one marker stream with several converters over it.  Each
produces a finished text that a reader or an agent actually sees, and each is
scanned here by the SAME detector — ``britannica.render.leaks.find_leaks`` — under
the one rule that detector exists to enforce: a marker in the output is a recursion
failure, not an exemption.  There is no handled-marker manifest to strip against.

This replaces ``render_leaks.py``, which ran that rule over ``rendered_html`` alone.
Scanning one consumer is the same blindness as trusting a handled-marker list, just
at a different level: it cannot see a converter that was never looked at.  That is
not hypothetical — ``markdown.py``'s ``_OUTLINE_RE`` has matched nothing since it
was written, and the raw ``«OUTLINE»`` it lets through has been shipping in the
download bundle unseen.

Which converters exist, which are covered, and what is deliberately left out live in
``britannica.outputs`` — one list, shared with the quality report, so this tool
cannot drift from the standing signal.  The ``index.json`` previews are scanned here
too: they are one file, not a per-article field.
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout.reconfigure(encoding="utf-8")
from britannica.export.corpus import NON_ARTICLE             # noqa: E402
from britannica.outputs import outputs_for                   # noqa: E402
from britannica.markers import marker_names                  # noqa: E402
from britannica.render.leaks import find_leaks                # noqa: E402

ART = "data/derived/articles"

OUT = Path("data/derived/quality_reports/output_leaks.tsv")
CONSUMERS = ("rendered_html", "markdown", "search_text", "title",
             "contributor_bio")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after N articles")
    args = ap.parse_args()

    files = [f for f in sorted(glob.glob(f"{ART}/*.json"))
             if os.path.basename(f) not in NON_ARTICLE]
    if args.limit:
        files = files[:args.limit]

    seen = Counter()            # consumer -> articles scanned
    dirty = Counter()           # consumer -> articles with ANY leak
    cat_arts = Counter()        # (consumer, category) -> articles
    cat_occ = Counter()         # (consumer, category) -> occurrences
    names = Counter()           # (consumer, marker name) -> occurrences
    rows = []

    for f in files:
        try:
            d = json.loads(open(f, encoding="utf-8").read())
        except Exception as exc:                       # a corrupt JSON is a finding
            rows.append((os.path.basename(f)[:-5], "-", "unreadable", str(exc)[:60]))
            continue
        stem = os.path.basename(f)[:-5]
        # An article can carry SEVERAL entries under one consumer name (its
        # contributor bios), so article-level counts are taken per consumer once,
        # not per entry — otherwise a three-bio article reads as three dirty ones.
        art_cats = {}
        entries = outputs_for(d)          # computed ONCE — the converters are the cost
        for consumer in {c for c, _f, _t in entries}:
            seen[consumer] += 1
        for consumer, fmt, text in entries:
            leaks = find_leaks(text, fmt)
            # The oracle's OWN extractor, so there is no second definition of
            # "what a marker looks like" to drift from the checks.
            for nm in marker_names(text):
                names[(consumer, nm)] += 1
            if not leaks:
                continue
            art_cats.setdefault(consumer, set()).update(c for c, _ in leaks)
            for cat, snippet in leaks:
                cat_occ[(consumer, cat)] += 1
                rows.append((stem, consumer, cat,
                             snippet.replace("\t", " ").replace("\n", "\\n")))
        for consumer, cats in art_cats.items():
            dirty[consumer] += 1
            for cat in cats:
                cat_arts[(consumer, cat)] += 1

    # index.json previews — one file, scanned whole.
    prev_dirty = prev_occ = prev_total = 0
    idx = Path(ART) / "index.json"
    if idx.exists():
        for e in json.loads(idx.read_text(encoding="utf-8")):
            if not isinstance(e, dict):
                continue
            prev_total += 1
            lk = find_leaks(e.get("body_start") or "", "text")
            if lk:
                prev_dirty += 1
                prev_occ += len(lk)
                for cat, snippet in lk:
                    rows.append((str(e.get("stable_id") or e.get("id")), "preview",
                                 cat, snippet.replace("\t", " ").replace("\n", "\\n")))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write("stem\tconsumer\tcategory\tsnippet\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")

    print(f"OUTPUT-LEAK REPORT — {len(files)} articles\n")
    print(f"  {'consumer':<17}{'scanned':>9}{'dirty':>9}{'%':>8}   by category")
    for consumer in CONSUMERS:
        n, bad = seen[consumer], dirty[consumer]
        cats = sorted(((c, k) for (cn, c), k in cat_arts.items() if cn == consumer),
                      key=lambda t: -t[1])
        detail = "  ".join(f"{c}:{k}" for c, k in cats) or "clean"
        print(f"  {consumer:<17}{n:>9}{bad:>9}{100.0 * bad / max(1, n):>7.2f}%   {detail}")
    print(f"  {'preview':<17}{prev_total:>9}{prev_dirty:>9}"
          f"{100.0 * prev_dirty / max(1, prev_total):>7.2f}%   ({prev_occ} occurrences)")

    print("\n  occurrences by consumer × category:")
    for (consumer, cat), k in sorted(cat_occ.items(), key=lambda t: -t[1]):
        print(f"    {k:>8}  {consumer:<17}{cat}")

    print("\n  leaked marker NAMES (top 25):")
    for (consumer, name), k in names.most_common(25):
        print(f"    {k:>8}  {consumer:<17}{name}")

    print(f"\n  per-article detail → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
