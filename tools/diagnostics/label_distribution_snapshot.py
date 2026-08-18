"""Capture per-element label distribution across the corpus.

For each ClassifiedElement in every article, records its label keyed
by a stable identifier: ``(article_volume, article_page_start,
element_path_in_tree)`` where the path is a `/`-separated sequence
of indices walking the classified tree.

The output is a sorted-by-key JSON file at
``tools/_scratch/label_distribution.<TAG>.json`` where TAG is the
caller-supplied label (e.g. ``before``, ``after``).

The intended workflow:

  1. Capture ``before`` distribution under one TAG.
  2. Make the predicate change.
  3. Capture ``after`` distribution under a second TAG.
  4. Diff the two JSON files line by line.  Any element whose label
     differs is a candidate for misclassification.  Verify the
     transitions are only in the expected direction.

Usage:
    .venv/Scripts/python tools/diagnostics/label_distribution_snapshot.py TAG
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from britannica.db.session import SessionLocal  # noqa: E402
from britannica.db.models import Article  # noqa: E402
from britannica.pipeline.stages.elements._classifier import (  # noqa: E402
    classify_article,
)


def walk(tree, path):
    """Yield (path, label) for every element in the tree."""
    for idx, (_ph, ce) in enumerate(tree.items()):
        node_path = f"{path}/{idx}" if path else str(idx)
        if ce.label:
            yield node_path, ce.label
        if ce.inner_registry:
            yield from walk(ce.inner_registry, node_path)


def main() -> int:
    _walk_failures = []
    if len(sys.argv) != 2:
        print("usage: label_distribution_snapshot.py TAG", file=sys.stderr)
        return 2
    tag = sys.argv[1]

    session = SessionLocal()
    distribution: dict[str, str] = {}
    try:
        # Article pages only.  Plate pages (`article_type == "plate"`) fork
        # to `parsers/plate/` in production and never reach the element
        # classifier — including them here would classify plate bodies with
        # the article pipeline (inflating figure labels) and mis-mirror prod.
        articles = (
            session.query(Article)
            .filter(Article.article_type != "plate")
            .all()
        )
        print(f"Articles (non-plate): {len(articles)}", flush=True)
        start = time.time()
        for i, art in enumerate(articles):
            if i % 1000 == 0 and i > 0:
                elapsed = time.time() - start
                rate = i / elapsed
                eta = (len(articles) - i) / rate if rate > 0 else 0
                print(f"  {i}/{len(articles)} "
                      f"({elapsed:.0f}s, ~{eta:.0f}s left)", flush=True)

            # Stored whole — read, don't rebuild
            # ([[project_page_position_out_of_band]]).
            body = art.body or ""
            if not body:
                continue

            try:
                _ph, tree = classify_article(body)
            except Exception as exc:
                # A walk failure is DATA about the corpus, not a broken net, so it is
                # COUNTED rather than raised — but never silently dropped: an article
                # absent from a distribution report is one the report says nothing
                # about ([[feedback_honesty_surface_failures]]).
                _walk_failures.append(repr(exc)[:90])
                continue

            for elem_path, label in walk(tree, ""):
                # Include art.id: multiple articles can share (volume,
                # page_start) (e.g. GERMANTOWN + GERMANY both at 11/825),
                # so a vol/page/path key COLLIDES and silently overwrites —
                # undercounting and leaving the diff blind to the hidden
                # element.  art.id makes the key unique per element.
                key = f"{art.volume:02d}/{art.page_start:04d}/{art.id}/{elem_path}"
                distribution[key] = label
        elapsed = time.time() - start
        print(f"Done in {elapsed:.0f}s.  "
              f"{len(distribution)} classified elements.", flush=True)
    finally:
        session.close()

    out = (Path(__file__).resolve().parents[2]
           / "tools" / "_scratch" / f"label_distribution.{tag}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for key in sorted(distribution):
            f.write(json.dumps({"k": key, "l": distribution[key]}) + "\n")
    if _walk_failures:
        print(f"  WARNING: {len(_walk_failures)} article(s) failed to walk "
              f"and are ABSENT from this report", flush=True)
    print(f"Written: {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
