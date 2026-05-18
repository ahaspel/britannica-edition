"""Snapshot regression test for `_transform_text_v2`.

For each seed article snapshot under ``tests/snapshots/transform/``,
re-run ``_transform_text_v2`` on the captured input and assert that
the result matches the captured body byte-for-byte.

The snapshots were captured against the as-shipped behaviour
2026-05-18 (see ``tools/diagnostics/capture_transform_snapshots.py``).
The body is the IMMEDIATE output of `_transform_text_v2` — not the
exported article body, which passes through downstream phases
(resolve_xrefs, page-marker translation, qualifier strip) that this
test deliberately does not cover.  The snapshots act as a tripwire
for the `_transform_text_v2` decomposition: any structural refactor
should leave them untouched.

When you intentionally change behaviour:
  1. Run ``tools/diagnostics/capture_transform_snapshots.py`` to
     regenerate the snapshots.
  2. Inspect the resulting diffs to confirm only the intended cases
     changed.
  3. Commit the new snapshots alongside the behaviour change.
"""
from __future__ import annotations

import difflib
import json
from pathlib import Path

import pytest

from britannica.pipeline.stages.transform_articles import _transform_text_v2


SNAPSHOT_DIR = Path("tests/snapshots/transform")


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
    expected = body_path.read_text(encoding="utf-8")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    actual = _transform_text_v2(raw_wikitext, meta["volume"],
                                meta["page_number"])

    if actual != expected:
        # Use a compact, line-oriented diff for readability — full
        # output text can be megabytes for big articles.
        diff = list(difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"{stem}.body.txt (snapshot)",
            tofile=f"{stem}.body.txt (current)",
            n=2,
        ))
        # Truncate huge diffs so the failure message stays usable.
        if len(diff) > 200:
            diff = diff[:200] + [f"... ({len(diff) - 200} more lines)\n"]
        pytest.fail(
            f"transform output diverged for {stem}\n" +
            "".join(diff)
        )
