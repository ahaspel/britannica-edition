"""Isolate the assemble's title_display_override path on one volume.

Walk a volume via produce_article (body + title_display), build the index,
then export twice off the SAME fresh bodies + index — once WITH
title_display_override (the assemble path), once without (the stored
title_display).  Body and xrefs are identical on both sides (same override
+ index), so the only thing that can differ is title_display: a nonzero
count = articles whose stored title_display is stale relative to the fresh
produce_article value.  produce_article IS transform_articles' logic, so a
diff is staleness in the DB, not a bug in the new path.

    uv run python tools/diagnostics/verify_assemble.py 1
"""
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article
from britannica.db.session import SessionLocal
from britannica.export.article_json import export_articles_to_json
from britannica.pipeline.stages.resolve_xrefs import build_resolution_index
from britannica.pipeline.stages.transform_articles import produce_article


def main() -> None:
    vol = int(sys.argv[1])
    session = SessionLocal()
    arts = (session.query(Article).filter(Article.volume == vol)
            .order_by(Article.id).all())
    print(f"walking {len(arts)} articles via produce_article...", flush=True)
    corpus: dict[int, str] = {}
    title_disp: dict[int, str | None] = {}
    for a in arts:
        body, disp = produce_article(session, a)
        corpus[a.id] = body
        title_disp[a.id] = disp
    print("building resolution index...", flush=True)
    idx = build_resolution_index(session.query(Article).all(), corpus=corpus)

    with tempfile.TemporaryDirectory() as td:
        d_a = Path(td) / "assemble"
        d_b = Path(td) / "stored"
        export_articles_to_json(vol, d_a, body_override=corpus, link_index=idx,
                                title_display_override=title_disp)
        export_articles_to_json(vol, d_b, body_override=corpus, link_index=idx)
        fa = {p.name: p.read_text(encoding="utf-8") for p in d_a.glob("*.json")}
        fb = {p.name: p.read_text(encoding="utf-8") for p in d_b.glob("*.json")}
        names = sorted(set(fa) | set(fb))
        mism = sum(1 for n in names if fa.get(n, "") != fb.get(n, ""))
        print(f"\nvol {vol}: {mism} of {len(names)} files differ on title_display "
              f"(override=produce_article vs stored)")


if __name__ == "__main__":
    main()
