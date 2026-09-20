"""Turn the scan adjudication into `corrections.json` entries, safely.

`{{img float}}` is `{{{align|right}}}` -- omitting `align` means RIGHT on
Wikisource, while our producer defaults LEFT.  227 instances state no align, so
for all of them the side is whichever renderer's default you happen to hit.  The
scans were read one by one; this writes that answer into the source.

THE TRAP THIS GUARDS: `corrections.apply_corrections` looks entries up by VOLUME
prefix and applies each as a literal `str.replace` over the whole volume.  The
page number in the key is informational.  So a `from` string that occurs twice
anywhere in its volume would silently rewrite both, and a `from` that occurs zero
times (whitespace differing from what we reconstructed) would silently do
nothing.  Every entry is therefore counted against the real volume text first,
and anything that is not exactly 1 is refused rather than written.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from img_float_side import collect                     # noqa: E402
from britannica.source_pages import load_pages         # noqa: E402

_OPEN_RE = re.compile(r"(\{\{\s*[Ii]mg float)", re.I)


def volume_text(vol: int) -> str:
    """Every raw page of a volume, concatenated -- the haystack a correction hits.

    Through `load_pages`, the ONE reader for raw pages.  Its text carries the
    corrections already applied, which is exactly the haystack a NEW correction
    has to be unique in: corrections are applied in sequence, so a `from` string
    is matched against text earlier ones have already touched.  And it RAISES on
    a page it cannot read -- the `except Exception: continue` this replaces made
    an unreadable page into a page the uniqueness gate silently ignored, which
    is how a `from` string that occurs twice could be counted once.
    """
    pages, failures = load_pages(volume=vol)
    if failures:
        raise SystemExit(
            "unreadable source pages in vol %d: %d (first: %s -- %s)"
            % (vol, len(failures), failures[0][0], failures[0][1]))
    return "\n".join(p.text for p in pages)


def insert_align(body: str, side: str) -> str:
    """`{{img float |file=...}}` -> `{{img float |align=right |file=...}}`."""
    return _OPEN_RE.sub(lambda m: m.group(1) + f" |align={side}", body, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers", help="the adjudication JSON from the form")
    ap.add_argument("--out", help="write corrections fragment here")
    ap.add_argument("--survey", help="write the full adjudication record here")
    ap.add_argument("--sides", default="right",
                    help="'right' = only entries that change OUR output (default); "
                         "'both' = make align explicit on every adjudicated instance")
    args = ap.parse_args()

    answers = json.load(open(args.answers, encoding="utf-8"))
    rows = collect(only_alignless=True)
    if len(rows) != len(answers):
        raise SystemExit(f"answer count {len(answers)} != template count {len(rows)}")

    want = {"right"} if args.sides == "right" else {"left", "right"}
    vol_cache: dict[int, str] = {}
    entries: dict[str, list] = defaultdict(list)
    survey, refused = [], []
    counts = Counter()

    for r, a in zip(rows, answers):
        if r["file"] != a["file"] or r["vol"] != a["vol"] or r["ws_page"] != a["page"]:
            raise SystemExit(f"row/answer mismatch at i={a['i']}: {r['file']!r} vs {a['file']!r}")
        side = a["answer"]
        counts[side] += 1
        survey.append({"vol": r["vol"], "ws_page": r["ws_page"], "leaf": r["leaf"],
                       "file": r["file"], "scan_side": side, "detector_guess": a["guess"]})
        if side not in want:
            continue
        body = r["body"]
        vol = r["vol"]
        if vol not in vol_cache:
            vol_cache[vol] = volume_text(vol)
        n = vol_cache[vol].count(body)
        if n != 1:
            refused.append({"vol": vol, "ws_page": r["ws_page"], "file": r["file"],
                            "occurrences": n})
            continue
        entries[f"{vol}:{r['ws_page']}"].append({"from": body, "to": insert_align(body, side)})

    total = sum(len(v) for v in entries.values())
    print(f"adjudicated: {dict(counts)}")
    print(f"correction entries built: {total} across {len(entries)} page keys")
    if refused:
        print(f"\nREFUSED {len(refused)} (a `from` that is not unique-in-volume would be unsafe):")
        for x in refused:
            print(f"   vol {x['vol']} ws {x['ws_page']}  occurrences={x['occurrences']}  {x['file'][:58]}")

    if args.out:
        Path(args.out).write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nwrote {args.out}")
    if args.survey:
        Path(args.survey).write_text(json.dumps(survey, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {args.survey} ({len(survey)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
