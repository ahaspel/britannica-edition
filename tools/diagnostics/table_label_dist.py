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
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import classify_article


def walk(tree, path):
    for idx, (_ph, ce) in enumerate(tree.items()):
        node = f"{path}/{idx}" if path else str(idx)
        if ce.label:
            yield node, ce.label
        if ce.inner_registry:
            yield from walk(ce.inner_registry, node)


def main():
    tag = sys.argv[1]
    s = SessionLocal()
    arts = (
        s.query(Article)
        .join(ArticleSegment, ArticleSegment.article_id == Article.id)
        .filter(ArticleSegment.segment_text.like("%{|%"))
        .distinct().order_by(Article.volume, Article.page_start).all()
    )
    dist = {}
    cur = None
    for a in arts:
        if a.article_type == "plate":
            continue  # production routes plates to parse_plate, not here
        if a.volume != cur:
            cur = a.volume
            print(f"  vol {cur}", flush=True)
        segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                .order_by(ArticleSegment.sequence_in_article).all())
        body = "\n\n".join(x.segment_text or "" for x in segs)
        try:
            _ph, tree = classify_article(body)
        except Exception:
            continue
        for node, label in walk(tree, ""):
            dist[f"{a.volume:02d}/{a.page_start:04d}/{node}"] = label
    out = Path(f"tools/_scratch/tld.{tag}.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for k in sorted(dist):
            f.write(json.dumps({"k": k, "l": dist[k]}) + "\n")
    print(f"wrote {len(dist)} labels -> {out}", flush=True)


if __name__ == "__main__":
    main()
