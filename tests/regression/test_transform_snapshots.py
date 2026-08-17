"""Snapshot regression test for `_transform_text_v2`.

For each seed article snapshot under ``tests/snapshots/transform/``,
re-run ``_transform_text_v2`` on the captured input and assert that
the result matches the captured body.

Snapshots come from two sources:

1. ``capture_transform_snapshots.py`` writes the IMMEDIATE output of
   `_transform_text_v2` for a fixed seed list — pre-downstream form,
   with `«LN:Title|alt«/LN»` markers in their unresolved shape.

2. ``add_snapshot_from_production.py`` writes the previously-exported
   JSON body verbatim — post-downstream form, with resolved
   `«LN:NN-NNNN-stem.json|Title|alt«/LN»` xref markers.  This is how we add arbitrary
   existing articles to the suite quickly: the production export IS
   the baseline.

To support both, the test normalises BOTH the captured body and the
freshly-recomputed `_transform_text_v2` output for the downstream-
phase difference (xref resolution) before comparing.  Pre-downstream snapshots are
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

from britannica.pipeline.stages.elements import ElementContext, process_elements
from britannica.pipeline.stages.preprocess import _source_clean


SNAPSHOT_DIR = Path("tests/snapshots/transform")


# ── Downstream-phase normalisation ────────────────────────────────────
#
# ONE transformation gets applied AFTER `_transform_text_v2` during the
# article-export pipeline: xref resolution rewrites a link's target.  It is not
# part of the transform under test, but a snapshot captured from a production
# export carries it, so both sides are normalised past it.
#
# TWO other normalisations stood here and both are gone, because both had
# stopped normalising anything:
#
#   * `\x01PAGE:NN\x01` — page position left the marker stream
#     ([[project_page_position_out_of_band]]), so no body can contain the token.
#     It survived only because the FIXTURES did: `capture_transform_snapshots`
#     could not resolve a single seed (its `.meta.json` sidecars were deleted and
#     its export-filename fallback predates hash suffixes), so it silently
#     refreshed nothing for weeks while every seed reported MISSING.  The tool is
#     repaired and the fixtures re-captured; 0 of 21 bodies carry the token.
#   * `\x03ELEM:NN\x03` — the placeholder stabiliser, added when AFRICA's table
#     leaked a child placeholder.  That leak is gone: 0 of 21 bodies carry one.
#     Keeping it would be worse than useless — it would ABSORB the next leak
#     into a stable snapshot instead of failing the test, which is the opposite
#     of what a net is for ([[feedback_sweepers_hide_bugs]]).
_LN_RESOLVED_RE = re.compile(
    r"«LN:\d{2}-\d{4}-[^|]+\.json\|([^|]+)\|")


def _normalize_for_compare(text: str) -> str:
    """Erase the one downstream-phase artefact so a snapshot captured from a
    production export compares equal to a freshly-transformed body:

      * `«LN:NN-NNNN-stem.json|Title|…»` → `«LN:Title|…»`  (xref resolution)
    """
    return _LN_RESOLVED_RE.sub(r"«LN:\1|", text)


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
    raw_wikitext = input_path.read_text(encoding="utf-8")
    expected_raw = body_path.read_text(encoding="utf-8")
    # Volume + page from the `NN-NNNN-…` stem (e.g. 01-0426-… → vol 1, p426).
    volume, page_number = int(stem[:2]), int(stem[3:7])

    # The `.input.txt` fixtures were captured POST-quote-run but PRE-clean (they
    # still carry raw `&nbsp;`/`{{nop}}`/`<del>`).  Apply `_source_clean` — the
    # re-appliable cleans half of `preprocess` — NOT full `preprocess`, which would
    # re-run quote-run on the already-converted markup and mangle a leftover `'''`
    # from a source typo (BRACHIOPODA).  Production runs the full pass on raw.
    actual_raw = process_elements(
        _source_clean(raw_wikitext),
        ElementContext(volume=volume))

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
