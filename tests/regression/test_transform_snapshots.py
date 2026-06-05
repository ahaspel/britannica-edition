"""Snapshot regression test for `_transform_text_v2`.

For each seed article snapshot under ``tests/snapshots/transform/``,
re-run ``_transform_text_v2`` on the captured input and assert that
the result matches the captured body.

Snapshots come from two sources:

1. ``capture_transform_snapshots.py`` writes the IMMEDIATE output of
   `_transform_text_v2` for a fixed seed list — pre-downstream form,
   with `\\x01PAGE:N\\x01` markers carrying ws-page numbers and
   `«LN:Title|alt«/LN»` markers in their unresolved shape.

2. ``add_snapshot_from_production.py`` writes the previously-exported
   JSON body verbatim — post-downstream form, with printed-page
   numbers in the PAGE markers and resolved `«LN:NN-NNNN-stem.json|
   Title|alt«/LN»` xref markers.  This is how we add arbitrary
   existing articles to the suite quickly: the production export IS
   the baseline.

To support both, the test normalises BOTH the captured body and the
freshly-recomputed `_transform_text_v2` output for the downstream-
phase differences before comparing.  Pre-downstream snapshots are
unaffected by the normalise (it's an identity on them); post-
downstream snapshots collapse to the pre-downstream form.  Either
way, the comparison is downstream-phase-invariant.

When you intentionally change `_transform_text_v2` behaviour:
  1. Re-run the appropriate capture tool for affected seeds.
  2. Inspect the diffs to confirm only the intended cases changed.
  3. Commit the new snapshots alongside the behaviour change.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import pytest

from britannica.pipeline.stages.transform_articles import _transform_text_v2


SNAPSHOT_DIR = Path("tests/snapshots/transform")


# ── Downstream-phase normalisation ────────────────────────────────────
#
# Two transformations get applied AFTER `_transform_text_v2` during
# the article-export pipeline.  They're not part of the transform
# under test, but post-downstream JSON exports carry their effects.
# Normalising both sides erases the difference.

_PAGE_MARKER_RE = re.compile(r"\x01PAGE:\d+\x01")
_LN_RESOLVED_RE = re.compile(
    r"«LN:\d{2}-\d{4}-[^|]+\.json\|([^|]+)\|")
_ELEM_PH_RE = re.compile(r"\x03ELEM:\d+\x03")


def _normalize_for_compare(text: str) -> str:
    """Strip downstream-phase artefacts so pre- and post-downstream
    snapshot bodies compare equivalent.

    Normalisations:
      * `\\x01PAGE:NN\\x01` → `\\x01PAGE:N\\x01`  (ws ↔ printed page renumber)
      * `«LN:NN-NNNN-stem.json|Title|…»` → `«LN:Title|…»`  (xref resolution)
      * `\\x03ELEM:NN\\x03` → `\\x03ELEM\\x03`  (placeholder-number stabilise)

    The last one is NOT hiding a bug — it's the opposite.  A LEAKED child
    placeholder (a producer that built HTML without substituting a child —
    e.g. AFRICA's HTMLTABLE) is non-deterministic because the placeholder
    counter is process-global; stabilising the NUMBER lets us snapshot the
    brutal case so the leak's PRESENCE is captured and grep-able (`\\x03ELEM`).
    When the producer/renderer split (#2) fixes the leak, the markers vanish
    from the snapshot — the diff is the proof of the fix.
    """
    text = _PAGE_MARKER_RE.sub("\x01PAGE:N\x01", text)
    text = _LN_RESOLVED_RE.sub(r"«LN:\1|", text)
    text = _ELEM_PH_RE.sub("\x03ELEM\x03", text)
    return text


def _snapshot_pairs() -> list[tuple[str, Path, Path]]:
    """Discover (stem, input, body) pairs on disk.  The `.body.txt` IS the
    snapshot; its sibling `.input.txt` is the fixture.  Volume + page are
    parsed from the `NN-NNNN-…` stem, so no per-seed metadata file is needed."""
    if not SNAPSHOT_DIR.exists():
        return []
    pairs = []
    for body_path in sorted(SNAPSHOT_DIR.glob("*.body.txt")):
        stem = body_path.name.removesuffix(".body.txt")
        pairs.append((
            stem,
            SNAPSHOT_DIR / f"{stem}.input.txt",
            body_path,
        ))
    return pairs


@pytest.mark.parametrize("stem,input_path,body_path",
                         _snapshot_pairs(),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_transform_snapshot(stem, input_path, body_path):
    if stem == "14-0737-s2-INTERPOLATION":
        # Q2 CANARY.  Once fractions are recognized elements, a fraction inside
        # a figtable cell is a placeholder — but the figtable producer's cell
        # path is `render_markers`/`decompose`, which bypasses `process_elements`
        # and re-runs body-text sub/sup OVER the placeholder, subscripting its
        # ID digits (and the ID is non-deterministic).  The producer collapse
        # (route cell content through `process_elements`) fixes it by
        # construction; remove this xfail when that lands.
        pytest.xfail("producer-collapse canary: figtable cell bypasses "
                     "process_elements (render_markers re-runs sub/sup over a "
                     "fraction placeholder)")
    raw_wikitext = input_path.read_text(encoding="utf-8")
    expected_raw = body_path.read_text(encoding="utf-8")
    # Volume + page from the `NN-NNNN-…` stem (e.g. 01-0426-… → vol 1, p426).
    volume, page_number = int(stem[:2]), int(stem[3:7])

    actual_raw = _transform_text_v2(raw_wikitext, volume, page_number)

    expected = _normalize_for_compare(expected_raw)
    actual = _normalize_for_compare(actual_raw)

    if actual != expected:
        diff = list(difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"{stem}.body.txt (snapshot, normalised)",
            tofile=f"{stem}.body.txt (current, normalised)",
            n=2,
        ))
        if len(diff) > 200:
            diff = diff[:200] + [f"... ({len(diff) - 200} more lines)\n"]
        pytest.fail(
            f"transform output diverged for {stem}\n" +
            "".join(diff)
        )
