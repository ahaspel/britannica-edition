"""Diff two table-label-distribution snapshots (tld.<TAG>.jsonl from
table_label_dist.py).  Reports every key whose label changed, grouped by
transition (old->new) with counts, plus net per-label deltas.  This is the
corpus-wide regression net for a classifier change: confirm ONLY the intended
transition direction occurs, zero collateral.

Usage: diff_tld.py BEFORE_TAG AFTER_TAG
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def load(tag):
    d = {}
    for line in Path(f"tools/_scratch/tld.{tag}.jsonl").read_text(
            encoding="utf-8").splitlines():
        o = json.loads(line)
        d[o["k"]] = o["l"]
    return d


def main():
    before, after = load(sys.argv[1]), load(sys.argv[2])
    keys = set(before) | set(after)
    transitions = Counter()
    examples = {}
    net = Counter()
    for k in keys:
        b, a = before.get(k), after.get(k)
        if b == a:
            continue
        transitions[(b, a)] += 1
        examples.setdefault((b, a), []).append(k)
        if b is not None:
            net[b] -= 1
        if a is not None:
            net[a] += 1
    print(f"=== {len(transitions)} distinct transitions, "
          f"{sum(transitions.values())} elements changed ===\n")
    for (b, a), n in transitions.most_common():
        print(f"  {n:4}  {b} -> {a}")
        for ex in examples[(b, a)][:6]:
            print(f"          {ex}")
    print("\n=== net per-label delta ===")
    for lbl, d in sorted(net.items(), key=lambda x: -x[1]):
        if d:
            print(f"  {d:+4}  {lbl}")


if __name__ == "__main__":
    main()
