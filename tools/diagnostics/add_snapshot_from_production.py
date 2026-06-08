"""Add a snapshot for an existing article using its
production-exported body as the baseline.

For each named article stem, pulls:
  * the raw segments from the DB (snapshot input)
  * the article metadata (volume, page numbers)
  * the *previously-exported* JSON body from
    ``data/derived/articles/<stem>.json`` (snapshot baseline)

Writes the standard snapshot triple under
``tests/snapshots/transform/<stem>.{input,body,meta}.txt|json``.

The JSON body has had downstream phases applied (LN xref resolution,
page-marker translation).  The snapshot test normalises both the
stored body and the freshly-computed `_transform_text_v2` output
before comparing, so a JSON-sourced body and a directly-captured
body can coexist in the suite — the comparison is downstream-
phase-invariant.

Usage::

    .venv/Scripts/python tools/diagnostics/add_snapshot_from_production.py STEM [STEM...]

where STEM is a JSON filename stem under ``data/derived/articles/``
(e.g. ``01-0042-s5-ABBEY``).
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")

from britannica.db.models import Article, ArticleSegment, SourcePage  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402


SNAPSHOT_DIR = Path("tests/snapshots/transform")
EXPORT_DIR = Path("data/derived/articles")


def _build_joined_raw(segments: list) -> str:
    """Same join used by `transform_articles` and `capture_transform_snapshots`:
    concatenate the segments with NO separator.  Each segment already carries its
    `\\x01PAGE:N\\x01` marker (stamped at detection) and the seam was healed
    upstream — nothing to re-stamp, nothing to re-heal."""
    return "".join(seg.segment_text or "" for seg, page_number in segments)


def add_one(session, stem: str) -> tuple[str, str]:
    json_path = EXPORT_DIR / f"{stem}.json"
    if not json_path.exists():
        return ("MISSING", f"no JSON at {json_path}")
    art_json = json.loads(json_path.read_text(encoding="utf-8"))

    db_id = art_json.get("id")
    if db_id is None:
        return ("MISSING", "JSON has no 'id' field")
    article = session.get(Article, db_id)
    if article is None:
        return ("MISSING", f"no DB row for id={db_id}")
    if article.article_type == "plate":
        return ("SKIP", "plate articles use parse_plate, not _transform_text_v2")

    segments = (
        session.query(ArticleSegment)
        .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
        .filter(ArticleSegment.article_id == article.id)
        .order_by(ArticleSegment.sequence_in_article)
        .add_columns(SourcePage.page_number)
        .all()
    )
    if not segments:
        return ("MISSING", "no segments found")

    joined_raw = _build_joined_raw(segments)
    first_page = segments[0][1]
    body = art_json.get("body", "")

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT_DIR / f"{stem}.input.txt").write_text(joined_raw,
                                                      encoding="utf-8")
    (SNAPSHOT_DIR / f"{stem}.body.txt").write_text(body, encoding="utf-8")
    (SNAPSHOT_DIR / f"{stem}.meta.json").write_text(
        json.dumps({
            "stable_id": art_json.get("stable_id"),
            "title": article.title,
            "volume": article.volume,
            "page_number": first_page,
            "page_start": article.page_start,
            "page_end": article.page_end,
            "segments": len(segments),
            "input_bytes": len(joined_raw),
            "body_bytes": len(body),
            "body_source": "json_export",
        }, indent=2),
        encoding="utf-8",
    )
    return ("OK", f"vol {article.volume} pp.{article.page_start}-"
                   f"{article.page_end}  in={len(joined_raw):>7,}  "
                   f"out={len(body):>7,}")


def main() -> int:
    stems = sys.argv[1:]
    if not stems:
        print("usage: add_snapshot_from_production.py STEM [STEM...]",
              file=sys.stderr)
        return 2
    widest = max(len(s) for s in stems)
    session = SessionLocal()
    try:
        ok = miss = skip = 0
        for stem in stems:
            status, msg = add_one(session, stem)
            print(f"  [{status:7}] {stem:<{widest}}  {msg}")
            if status == "OK":   ok += 1
            elif status == "SKIP": skip += 1
            else:                miss += 1
        print()
        print(f"Added {ok}/{len(stems)} (skipped {skip}, missing {miss})")
        return 0 if miss == 0 else 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
