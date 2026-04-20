"""Compare two JSON scan baselines (from scan_article.py --json) and
report the deltas article-by-article and rule-by-rule.

Exit code:
    0 — every article identical (fixture set unchanged in observed behavior)
    1 — one or more articles differ (regression or fix to investigate)
    2 — one or more articles render-failed on either side

Usage:
    uv run python tools/qa/scan_article.py --json \\
        --from-file tools/qa/fixtures/default.txt > before.json
    # … make code/pipeline changes, reprocess affected articles …
    uv run python tools/qa/scan_article.py --json \\
        --from-file tools/qa/fixtures/default.txt > after.json
    uv run python tools/qa/diff_baselines.py before.json after.json

Interpretation of the diff:
* **Articles that gained violations** — almost always a regression.
  The code path for that article changed behavior.
* **Articles that lost violations** — usually a fix (target article),
  but still verify: an unintended side effect may also drop valid
  violations for the wrong reason.
* **Articles where the set of violation contexts changed, even if
  total count stayed the same** — content drift. Examine.
* **Render failures on either side** — blocker; fix before shipping.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def _violation_signature(v: dict) -> tuple[str, str]:
    """A violation is identified by (rule, context). Offset is omitted
    because HTML byte offsets shift with unrelated content changes."""
    return (v["rule"], v["context"])


def _load(p: Path) -> dict[str, dict]:
    return json.loads(p.read_text(encoding="utf-8"))


def diff(before: dict, after: dict) -> tuple[list[dict], int, int]:
    """Produce per-article diffs and counts.

    Returns (per_article_diffs, articles_changed, render_fail_count).
    Each diff entry: {article, added, removed, before_error,
    after_error, unchanged_count}.
    """
    names = sorted(set(before) | set(after))
    diffs: list[dict] = []
    changed = 0
    fails = 0
    for name in names:
        b = before.get(name, {})
        a = after.get(name, {})
        b_err = b.get("error")
        a_err = a.get("error")
        if b_err or a_err:
            fails += 1
            diffs.append({
                "article": name,
                "before_error": b_err,
                "after_error": a_err,
                "added": [],
                "removed": [],
                "unchanged_count": 0,
            })
            continue
        b_sigs = {_violation_signature(v): v for v in b.get("violations", [])}
        a_sigs = {_violation_signature(v): v for v in a.get("violations", [])}
        added_keys = set(a_sigs) - set(b_sigs)
        removed_keys = set(b_sigs) - set(a_sigs)
        unchanged = set(b_sigs) & set(a_sigs)
        if not added_keys and not removed_keys:
            continue  # identical — skip from diff output
        changed += 1
        diffs.append({
            "article": name,
            "before_error": None,
            "after_error": None,
            "added": [a_sigs[k] for k in added_keys],
            "removed": [b_sigs[k] for k in removed_keys],
            "unchanged_count": len(unchanged),
        })
    return diffs, changed, fails


def _print_diff(diffs: list[dict], verbose: bool) -> None:
    if not diffs:
        print("[CLEAN] no differences.")
        return
    for d in diffs:
        name = d["article"]
        if d["before_error"] or d["after_error"]:
            print(f"[RENDER-FAIL] {name}")
            if d["before_error"]:
                print(f"  before: {d['before_error']}")
            if d["after_error"]:
                print(f"  after:  {d['after_error']}")
            continue
        added = d["added"]
        removed = d["removed"]
        tag = "REGRESSED" if added else ("IMPROVED" if removed else "CHANGED")
        print(f"[{tag}] {name}  (+{len(added)} -{len(removed)} "
              f"={d['unchanged_count']})")
        if added:
            print("  added violations:")
            show = added if verbose else added[:3]
            for v in show:
                print(f"    [{v['rule']}]  …{v['context']}…")
            if not verbose and len(added) > 3:
                print(f"    (+{len(added) - 3} more)")
        if removed:
            print("  removed violations:")
            show = removed if verbose else removed[:3]
            for v in show:
                print(f"    [{v['rule']}]  …{v['context']}…")
            if not verbose and len(removed) > 3:
                print(f"    (+{len(removed) - 3} more)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before", type=Path, help="Baseline JSON (before change)")
    ap.add_argument("after",  type=Path, help="Baseline JSON (after change)")
    ap.add_argument("--verbose", action="store_true",
                    help="Show all added/removed violations instead of "
                         "truncating to 3 per article.")
    args = ap.parse_args()

    before = _load(args.before)
    after = _load(args.after)
    diffs, changed, fails = diff(before, after)
    _print_diff(diffs, args.verbose)
    print()
    print(f"Articles compared: {len(set(before) | set(after))}  "
          f"changed: {changed}  render failures: {fails}")

    if fails:
        return 2
    if changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
