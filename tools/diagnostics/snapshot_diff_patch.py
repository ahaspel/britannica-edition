"""Surgical snapshot updater.

For a failing snapshot under ``tests/snapshots/transform/``, re-run
``_transform_text_v2`` and compute a line-level diff against the
captured body.  Each non-equal region of the diff is one numbered
"hunk."  You can list hunks for review, or apply specific hunks
(by index) back to the body file — leaving every other line of the
snapshot byte-identical.

This preserves the regression-detection contract: a snapshot still
tests many things at once, but you can accept the IMG/LEGEND
standardization for ONE producer change without rebaselining the
whole article.

Usage:
    # List numbered hunks for a snapshot
    .venv/Scripts/python tools/diagnostics/snapshot_diff_patch.py <stem>

    # Apply specific hunks (comma-separated indices) to the body file
    .venv/Scripts/python tools/diagnostics/snapshot_diff_patch.py <stem> --accept 1,3,5

    # Apply all hunks
    .venv/Scripts/python tools/diagnostics/snapshot_diff_patch.py <stem> --accept all

Stem examples:  01-0127-s3-ACACIA, 25-0840-s3-STEAM_ENGINE

The script writes the normalised form of `_transform_text_v2`'s
output for accepted hunks: page markers as ``\\x01PAGE:N\\x01``,
xref markers in their pre-resolved shape.  This is the same
normalisation the snapshot test applies to both sides before
comparing, so it stays equivalent under the test's contract.
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# Re-encode stdout as utf-8 so the diff prints cleanly on Windows.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")

from britannica.pipeline.stages.transform_articles import (  # noqa: E402
    _transform_text_v2,
)

SNAPSHOT_DIR = REPO / "tests" / "snapshots" / "transform"

_PAGE_MARKER_RE = re.compile(r"\x01PAGE:\d+\x01")
_LN_RESOLVED_RE = re.compile(
    r"«LN:\d{2}-\d{4}-[^|]+\.json\|([^|]+)\|")


def _normalize(text: str) -> str:
    """Same normalisation as the snapshot test — strip downstream
    phase artefacts (page renumbering, xref resolution)."""
    text = _PAGE_MARKER_RE.sub("\x01PAGE:N\x01", text)
    text = _LN_RESOLVED_RE.sub(r"«LN:\1|", text)
    return text


def _load(stem: str) -> tuple[str, str, dict]:
    """Return (raw_input, body, meta) for a snapshot stem."""
    input_path = SNAPSHOT_DIR / f"{stem}.input.txt"
    body_path = SNAPSHOT_DIR / f"{stem}.body.txt"
    meta_path = SNAPSHOT_DIR / f"{stem}.meta.json"
    for p in (input_path, body_path, meta_path):
        if not p.exists():
            raise SystemExit(f"missing snapshot file: {p}")
    raw = input_path.read_text(encoding="utf-8")
    body = body_path.read_text(encoding="utf-8")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return raw, body, meta


def _compute_hunks(stem: str) -> dict:
    """Re-run the transform and compute hunks against the body.

    Returns a dict with:
      * `body_lines`        list[str]  raw body lines, keepends
      * `actual_lines`      list[str]  normalised actual lines, keepends
      * `expected_n_lines`  list[str]  normalised body lines, keepends
      * `hunks`             list[Hunk] non-equal opcodes
    """
    raw, body, meta = _load(stem)
    actual = _transform_text_v2(raw, meta["volume"], meta["page_number"])
    expected_n = _normalize(body)
    actual_n = _normalize(actual)

    body_lines = body.splitlines(keepends=True)
    expected_n_lines = expected_n.splitlines(keepends=True)
    actual_n_lines = actual_n.splitlines(keepends=True)

    # Sanity: normalisation must preserve line count (substitution-only).
    if len(body_lines) != len(expected_n_lines):
        raise SystemExit(
            f"normalisation changed line count for {stem}: "
            f"{len(body_lines)} -> {len(expected_n_lines)} — patcher "
            f"requires 1:1 line mapping; investigate.")

    sm = difflib.SequenceMatcher(
        a=expected_n_lines, b=actual_n_lines, autojunk=False)
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        hunks.append({
            "tag": tag, "i1": i1, "i2": i2, "j1": j1, "j2": j2,
            "old": expected_n_lines[i1:i2],
            "new": actual_n_lines[j1:j2],
        })
    return {
        "body_lines": body_lines,
        "actual_lines": actual_n_lines,
        "expected_n_lines": expected_n_lines,
        "hunks": hunks,
    }


def _fmt_line(s: str, width: int = 220) -> str:
    """Single-line preview; truncate long lines."""
    s = s.rstrip("\n").replace("\t", " ")
    if len(s) > width:
        s = s[:width - 1] + "…"
    return s


def list_hunks(stem: str, *, full: bool = False) -> int:
    data = _compute_hunks(stem)
    hunks = data["hunks"]
    if not hunks:
        print(f"{stem}: snapshot passes (no hunks).")
        return 0
    print(f"{stem}: {len(hunks)} differing hunk(s).\n")
    width = 0 if full else 220
    for idx, h in enumerate(hunks, 1):
        print(f"── Hunk {idx} — {h['tag']}  "
              f"snapshot[{h['i1']}:{h['i2']}]  "
              f"current[{h['j1']}:{h['j2']}]  ──")
        if h["old"]:
            for ln in h["old"]:
                print("- " + _fmt_line(ln, width if width else 10_000))
        if h["new"]:
            for ln in h["new"]:
                print("+ " + _fmt_line(ln, width if width else 10_000))
        print()
    return 0


def apply_hunks(stem: str, indices: list[int]) -> int:
    data = _compute_hunks(stem)
    hunks = data["hunks"]
    if not hunks:
        print(f"{stem}: snapshot passes (no hunks to apply).")
        return 0
    body_lines = data["body_lines"]
    n_total = len(hunks)
    if indices == ["all"]:
        chosen = list(range(1, n_total + 1))
    else:
        chosen = []
        for s in indices:
            try:
                i = int(s)
            except ValueError:
                raise SystemExit(f"bad hunk index: {s!r}")
            if i < 1 or i > n_total:
                raise SystemExit(
                    f"hunk index {i} out of range (1..{n_total})")
            chosen.append(i)
    chosen_set = set(chosen)

    # Apply in REVERSE order so earlier splices don't invalidate
    # later indices.  Each hunk's i1/i2 is into the ORIGINAL body
    # line list (preserved because normalisation is 1:1).
    out_lines = list(body_lines)
    for idx in sorted(chosen_set, reverse=True):
        h = hunks[idx - 1]
        out_lines[h["i1"]:h["i2"]] = h["new"]

    body_path = SNAPSHOT_DIR / f"{stem}.body.txt"
    body_path.write_text("".join(out_lines), encoding="utf-8")
    print(f"{stem}: applied {len(chosen_set)} hunk(s); "
          f"wrote {body_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("stem", help="snapshot stem (e.g. 01-0127-s3-ACACIA)")
    ap.add_argument("--accept", default=None,
                    help="comma-separated hunk indices, or 'all'")
    ap.add_argument("--full", action="store_true",
                    help="don't truncate long lines in list mode")
    args = ap.parse_args()

    if args.accept is None:
        return list_hunks(args.stem, full=args.full)
    indices = [s.strip() for s in args.accept.split(",") if s.strip()]
    return apply_hunks(args.stem, indices)


if __name__ == "__main__":
    sys.exit(main())
