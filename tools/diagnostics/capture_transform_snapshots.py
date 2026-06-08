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
from britannica.util.strings import section_slug  # noqa: E402


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
    "14-0737-s2-INTERPOLATION",      # math html_wrapper: {| positioning an
                                     # inner <table> equation display (Newton
                                     # interpolation coeffs) — guards the
                                     # table-collapse / html_wrapper boundary
    "18-0684-s2-MOLECULE",           # FN named-ref cross-paragraph
    "20-0215-s3-ORDNANCE",           # plate figures
    "25-0840-s3-STEAM_ENGINE",       # complex layout
    "26-0933-s2-THUCYDIDES",         # wikilink attribution (currently buggy)
)


SNAPSHOT_DIR = Path("tests/snapshots/transform")
EXPORT_DIR = Path("data/derived/articles")


def build_joined_raw(segments: list) -> str:
    """Mirror the FAITHFUL re-join in `transform_articles`: concatenate the
    segments with NO separator.  Each segment already carries its «PAGE» marker
    (stamped at detection) and is a slice of the preprocess-healed stream, so
    there is nothing to re-stamp and nothing to re-heal; re-inserting a ``\\n``
    between segments would invent a page-seam newline production no longer has.
    Matches ``snapshot_corpus._build_joined_raw`` and production exactly."""
    return "".join(seg.segment_text or "" for seg, page_number in segments)


def _find_article(session, stable_id: str):
    """Resolve an article by its DURABLE stable_id (``vol-page-slug``), NOT the
    autoincrement PK — the PK is reassigned on every re-detect, so a seed JSON's
    stored ``id`` goes stale after any rebuild.  Mirrors the stable_id
    construction in ``snapshot_corpus`` / the exporter."""
    parts = stable_id.split("-", 2)
    if len(parts) < 3:
        return None
    vol, page, slug = int(parts[0]), int(parts[1]), parts[2]
    for a in (session.query(Article)
              .filter(Article.volume == vol, Article.page_start == page,
                      Article.article_type != "plate").all()):
        s = section_slug(a.section_name) if a.section_name else ""
        if not s:
            s = section_slug(a.title)
        if s == slug:
            return a
    return None


def capture_one(session, filename_stem: str) -> tuple[str, str]:
    """Capture input/body/meta for a seed, located by its durable stable_id.
    The stable_id comes from the existing snapshot meta (falls back to the
    export JSON) — robust to PK reassignment across rebuilds."""
    meta_path = SNAPSHOT_DIR / f"{filename_stem}.meta.json"
    stable_id = None
    if meta_path.exists():
        stable_id = json.loads(meta_path.read_text(encoding="utf-8")).get("stable_id")
    if not stable_id:
        json_path = EXPORT_DIR / f"{filename_stem}.json"
        if not json_path.exists():
            return ("MISSING", f"no meta/JSON to resolve stable_id for {filename_stem}")
        stable_id = json.loads(json_path.read_text(encoding="utf-8")).get("stable_id")
    if not stable_id:
        return ("MISSING", "no stable_id available")

    article = _find_article(session, stable_id)
    if not article:
        return ("MISSING", f"no DB row for stable_id={stable_id}")
    art_json = {"stable_id": stable_id}
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

    # The `.body.txt` IS the snapshot; `.input.txt` is its fixture.  No
    # per-seed meta file: the test parses volume + page from the `NN-NNNN-…`
    # stem (the article's first ws page == `first_page`), so a metadata
    # sidecar would only drift with the DB (it carried the now-removed
    # stable_id/sizes).
    (SNAPSHOT_DIR / f"{filename_stem}.input.txt").write_text(joined_raw,
                                                              encoding="utf-8")
    (SNAPSHOT_DIR / f"{filename_stem}.body.txt").write_text(body,
                                                             encoding="utf-8")
    return ("OK", f"vol {article.volume} pp.{article.page_start}-"
                  f"{article.page_end}  in={len(joined_raw):>7,}  "
                  f"out={len(body):>7,}")


def main() -> int:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    # Optional positional args restrict capture to those seed stems — so a new
    # seed can be captured WITHOUT rewriting the other baselines (some of which
    # are post-downstream form from add_snapshot_from_production).  No args =
    # capture every seed.
    only = set(sys.argv[1:])
    seeds = tuple(f for f in SEED_FILENAMES if f in only) if only else SEED_FILENAMES
    if only and not seeds:
        print(f"no seed matches {sorted(only)}; known: {SEED_FILENAMES}")
        return 1
    s = SessionLocal()
    try:
        widest = max(len(f) for f in seeds)
        ok = miss = skip = 0
        for stem in seeds:
            status, msg = capture_one(s, stem)
            print(f"  [{status:7}] {stem:<{widest}}  {msg}")
            if status == "OK":   ok += 1
            elif status == "SKIP": skip += 1
            else:                miss += 1
        print()
        print(f"Captured {ok} / {len(seeds)} "
              f"(skipped {skip}, missing {miss})")
        return 0 if miss == 0 else 1
    finally:
        s.close()


if __name__ == "__main__":
    sys.exit(main())
