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
import json
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


def _normalize_for_compare(text: str) -> str:
    """Strip downstream-phase artefacts so pre- and post-downstream
    snapshot bodies compare equivalent.

    Normalisations:
      * `\\x01PAGE:NN\\x01` → `\\x01PAGE:N\\x01`  (ws ↔ printed page renumber)
      * `«LN:NN-NNNN-stem.json|Title|…»` → `«LN:Title|…»`  (xref resolution)
    """
    text = _PAGE_MARKER_RE.sub("\x01PAGE:N\x01", text)
    text = _LN_RESOLVED_RE.sub(r"«LN:\1|", text)
    return text


def _snapshot_triples() -> list[tuple[str, Path, Path, Path]]:
    """Discover (stem, input, body, meta) triples on disk."""
    if not SNAPSHOT_DIR.exists():
        return []
    triples = []
    for meta_path in sorted(SNAPSHOT_DIR.glob("*.meta.json")):
        stem = meta_path.name.removesuffix(".meta.json")
        triples.append((
            stem,
            SNAPSHOT_DIR / f"{stem}.input.txt",
            SNAPSHOT_DIR / f"{stem}.body.txt",
            meta_path,
        ))
    return triples


@pytest.mark.parametrize("stem,input_path,body_path,meta_path",
                         _snapshot_triples(),
                         ids=lambda v: v if isinstance(v, str) else "")
def test_transform_snapshot(stem, input_path, body_path, meta_path):
    raw_wikitext = input_path.read_text(encoding="utf-8")
    expected_raw = body_path.read_text(encoding="utf-8")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    actual_raw = _transform_text_v2(raw_wikitext, meta["volume"],
                                    meta["page_number"])

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
