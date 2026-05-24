"""Capture ``_transform_text_v2`` input/output snapshots for a fixed
set of seed articles, used by `tests/regression/test_transform_snapshots.py`
to lock in current behaviour during the `_transform_text_v2`
decomposition.

For each seed article, queries the live DB for its segments + page
numbers, builds the SAME ``joined_raw`` input that
``transform_articles`` builds during a real run, and writes:

  tests/snapshots/transform/<stable_id>.input.txt
  tests/snapshots/transform/<stable_id>.body.txt
  tests/snapshots/transform/<stable_id>.meta.json

The regression test loads each triple, runs ``_transform_text_v2``
on the input, and asserts equality with the captured body.  Any
divergence is a behaviour change that must be intentional.

Re-run this script whenever you intentionally change behaviour (and
update each seed's body snapshot accordingly).  Do NOT re-run after
purely structural refactors — those should leave snapshots
untouched, which is the whole point of the scaffolding.

Usage::
    uv run python tools/diagnostics/capture_transform_snapshots.py
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
from britannica.pipeline.stages.transform_articles import (  # noqa: E402
    _transform_text_v2,
)


# Seed list — JSON filenames (without .json) under
# data/derived/articles/.  Each entry exercises a different
# element-producer concern.  Grow over time; never shrink without
# explicit reason (a removed seed is one less canary against
# regression).
SEED_FILENAMES: tuple[str, ...] = (
    "01-0032-a-A",                   # inline glyphs (alphabet initials, brief)
    "01-0036-s5-ABACUS",             # table-figure
    "01-0042-s5-ABBEY",              # multi-poem-cell external-image legend
    "01-0127-s3-ACACIA",             # simple captioned figure
    "01-0157-s2-ACCUMULATOR",        # captioned figures (GLUED_BR)
    "01-0426-agriculture-AGRICULTURE",  # DATA_TABLE per-cell align + |+ caption + HTMLTABLE
    "01-0358-africa-AFRICA",         # BRUTAL HTMLTABLE case — currently leaks child
                                     # placeholders (#2 target; the leak is captured,
                                     # not hidden — see _normalize_for_compare)
    "01-0571-s4-ALDEHYDES",          # chemistry-layout / Langle bracket tables
    "01-0766-s5-ALPHABET",           # inline glyphs at scale
    "02-0302-s5-ARACHNIDA",          # user-flagged trouble article
    "02-0723-s2-ARTHUR",             # verse-quotation in wikitable (DATA_TABLE)
    "03-0219-s5-BAG-PIPE",           # SCORE + img/caption
    "04-0375-brachiopoda-BRACHIOPODA",  # wikitable-legend
    "06-0411-cithara-CITHARA",       # img-float
    "08-0783-dynamics-DYNAMICS",     # math-heavy
    "14-0147-hydromedusae-HYDROMEDUSAE",  # captioned figures + legends
    "18-0684-s2-MOLECULE",           # FN named-ref cross-paragraph
    "20-0215-s3-ORDNANCE",           # plate figures
    "25-0840-s3-STEAM_ENGINE",       # complex layout
    "26-0933-s2-THUCYDIDES",         # wikilink attribution (currently buggy)
)


SNAPSHOT_DIR = Path("tests/snapshots/transform")
EXPORT_DIR = Path("data/derived/articles")


def build_joined_raw(segments: list) -> str:
    """Mirror the build in `transform_articles` (lines ~757-768).
    Joins each segment's text with a page marker, then applies the
    cross-page hyphenation fix."""
    raw_parts = []
    for seg, page_number in segments:
        raw = seg.segment_text or ""
        raw_parts.append(f"\x01PAGE:{page_number}\x01{raw}")
    joined_raw = "\n".join(raw_parts)
    joined_raw = re.sub(
        r"(\w)-\n(\x01PAGE:\d+\x01)(\w)",
        r"\1\2\3", joined_raw,
    )
    return joined_raw


def capture_one(session, filename_stem: str) -> tuple[str, str]:
    """Look up an article by JSON filename stem, capture input/body/meta.
    Returns (status, message)."""
    json_path = EXPORT_DIR / f"{filename_stem}.json"
    if not json_path.exists():
        return ("MISSING", f"no JSON at {json_path}")
    art_json = json.loads(json_path.read_text(encoding="utf-8"))

    db_id = art_json.get("id")
    if db_id is None:
        return ("MISSING", "JSON has no 'id' field")

    article = session.get(Article, db_id)
    if not article:
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

    joined_raw = build_joined_raw(segments)
    first_page = segments[0][1]

    # IMPORTANT: snapshot the IMMEDIATE output of `_transform_text_v2`,
    # not the eventually-exported article body.  The exported body
    # passes through downstream phases (resolve_xrefs translates `LN`
    # markers to filename targets; a page-marker translator converts
    # ws-page numbers to printed-page numbers; per-article qualifier
    # strip) that are not part of the transform under test.  Locking
    # those in would defeat the snapshot's purpose.
    body = _transform_text_v2(joined_raw, article.volume, first_page)

    (SNAPSHOT_DIR / f"{filename_stem}.input.txt").write_text(joined_raw,
                                                              encoding="utf-8")
    (SNAPSHOT_DIR / f"{filename_stem}.body.txt").write_text(body,
                                                             encoding="utf-8")
    (SNAPSHOT_DIR / f"{filename_stem}.meta.json").write_text(
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
        }, indent=2),
        encoding="utf-8",
    )
    return ("OK", f"vol {article.volume} pp.{article.page_start}-"
                  f"{article.page_end}  in={len(joined_raw):>7,}  "
                  f"out={len(body):>7,}")


def main() -> int:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    s = SessionLocal()
    try:
        widest = max(len(f) for f in SEED_FILENAMES)
        ok = miss = skip = 0
        for stem in SEED_FILENAMES:
            status, msg = capture_one(s, stem)
            print(f"  [{status:7}] {stem:<{widest}}  {msg}")
            if status == "OK":   ok += 1
            elif status == "SKIP": skip += 1
            else:                miss += 1
        print()
        print(f"Captured {ok} / {len(SEED_FILENAMES)} "
              f"(skipped {skip}, missing {miss})")
        return 0 if miss == 0 else 1
    finally:
        s.close()


if __name__ == "__main__":
    sys.exit(main())
