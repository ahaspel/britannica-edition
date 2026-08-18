"""Add a snapshot for an existing article using its
production-exported body as the baseline.

For each named article stem, pulls:
  * the raw body from the DB (snapshot input)
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")

from britannica.db.models import Article  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402


SNAPSHOT_DIR = Path("tests/snapshots/transform")
EXPORT_DIR = Path("data/derived/articles")


def _raw_body(article: Article) -> str:
    """The article's raw body — read, not rebuilt.

    Was a segment fetch plus a join that MIRRORED what `transform_articles` did.
    Mirroring a reassembly is only necessary while there is a reassembly, and the
    body is now stored whole, exactly as sliced from the clean volume stream
    ([[project_page_position_out_of_band]]).  Nothing here can join it wrongly
    because nothing here joins."""
    return article.body or ""


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

    joined_raw = _raw_body(article)
    if not joined_raw:
        return ("MISSING", "article has no body")
    first_page = article.page_start
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
