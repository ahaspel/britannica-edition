"""Diff two label-distribution snapshots, group by transition direction.

Reads two JSON files produced by `label_distribution_snapshot.py` and
reports per-transition-pair counts.  Lets you verify that a predicate
change moved cases only in the expected direction (e.g. LAYOUT_WRAPPER
→ CAPTIONED_FIGURE only).

Usage:
    .venv/Scripts/python tools/diagnostics/label_distribution_diff.py \
        before after
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")


def load(tag: str) -> dict[str, str]:
    path = (Path(__file__).resolve().parents[2]
            / "tools" / "_scratch" / f"label_distribution.{tag}.json")
    if not path.exists():
        raise SystemExit(f"missing snapshot: {path}")
    out: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            out[rec["k"]] = rec["l"]
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: label_distribution_diff.py BEFORE_TAG AFTER_TAG",
              file=sys.stderr)
        return 2
    before = load(sys.argv[1])
    after = load(sys.argv[2])

    only_before = set(before) - set(after)
    only_after = set(after) - set(before)
    common = set(before) & set(after)

    transitions: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key in common:
        b, a = before[key], after[key]
        if b != a:
            transitions[(b, a)].append(key)

    print(f"BEFORE: {len(before)} classified elements")
    print(f"AFTER:  {len(after)} classified elements")
    print(f"Only in BEFORE (vanished): {len(only_before)}")
    print(f"Only in AFTER  (appeared): {len(only_after)}")
    print(f"Common: {len(common)}; transitions: "
          f"{sum(len(v) for v in transitions.values())}")
    print()

    if not transitions:
        print("No transitions — distribution unchanged.")
        return 0

    print("## Transitions by (BEFORE → AFTER)")
    print()
    sorted_pairs = sorted(transitions.items(), key=lambda kv: -len(kv[1]))
    for (b, a), keys in sorted_pairs:
        print(f"  {b} → {a}: {len(keys)}")
        for k in keys[:3]:
            print(f"    {k}")
        if len(keys) > 3:
            print(f"    … ({len(keys) - 3} more)")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
