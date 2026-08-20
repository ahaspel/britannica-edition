"""Scoped label-distribution snapshot for table-classification changes.

Records every classified element's label keyed by (vol/page/tree-path), but
ONLY for the ~1500 table-bearing articles — fast enough to run before/after a
classifier change and diff.  Captures any transition involving a table
(DATA_TABLE↔MATH, MATH↔VERSE, etc.).

Usage: table_label_dist.py TAG   (writes tools/_scratch/tld.<TAG>.jsonl)
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

from britannica.db.session import SessionLocal
from britannica.db.models import Article
from britannica.pipeline.stages.elements._classifier import classify_article

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ast_shapes import walk_labels          # noqa: E402


def main():
    tag = sys.argv[1]
    s = SessionLocal()
    # Filter on the body itself — the segments hold page KEYS now, not text
    # ([[project_page_position_out_of_band]]).  No join, no DISTINCT.
    arts = (
        s.query(Article)
        .filter(Article.body.like("%{|%"))
        .order_by(Article.volume, Article.page_start).all()
    )
    dist = {}
    cur = None
    _walk_failures = []
    for a in arts:
        if a.article_type == "plate":
            continue  # production routes plates to parse_plate, not here
        if a.volume != cur:
            cur = a.volume
            print(f"  vol {cur}", flush=True)
        body = a.body or ""
        try:
            _ph, tree = classify_article(body)
        except Exception as exc:
            # A walk failure is DATA about the corpus, not a broken net, so
            # it is COUNTED rather than raised — but never silently dropped:
            # an article missing from a distribution report is one the report
            # says nothing about ([[feedback_honesty_surface_failures]]).
            _walk_failures.append((getattr(a, 'title', '?'), repr(exc)[:90]))
            continue
        for node, label in walk_labels(tree, ""):
            dist[f"{a.volume:02d}/{a.page_start:04d}/{node}"] = label
    out = Path(f"tools/_scratch/tld.{tag}.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for k in sorted(dist):
            f.write(json.dumps({"k": k, "l": dist[k]}) + "\n")
    if _walk_failures:
        print(f"  WARNING: {len(_walk_failures)} article(s) failed to walk "
              f"and are ABSENT from this report:", flush=True)
        for _t, _why in _walk_failures[:5]:
            print(f"    {_t}: {_why}", flush=True)
    print(f"wrote {len(dist)} labels -> {out}", flush=True)


if __name__ == "__main__":
    main()
