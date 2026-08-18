"""Capture ``_transform_text_v2`` input/output snapshots for a fixed
set of seed articles, used by `tests/regression/test_transform_snapshots.py`
to lock in current behaviour during the `_transform_text_v2`
decomposition.

For each seed article, reads the SAME raw body that ``transform_articles``
reads during a real run — `Article.body`, stored whole — and writes:

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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from britannica.db.models import Article  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.pipeline.stages.elements import (  # noqa: E402
    ElementContext, process_elements)
from britannica.pipeline.stages.preprocess import _source_clean  # noqa: E402
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
    "01-0426-agriculture-AGRICULTURE",  # DATA_TABLE per-cell align + |+ caption + TABLE
    "01-0358-africa-AFRICA",         # BRUTAL TABLE case — currently leaks child
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


def raw_body(article) -> str:
    """The article's raw body — read, not rebuilt.

    This function used to MIRROR the re-join in `transform_articles`, and its
    docstring argued at length about whether to put a ``\\n`` between the
    segments.  That argument existed only because the body had been cut up; it is
    stored whole now, so there is no join to get right
    ([[project_page_position_out_of_band]]).  Matches production by reading the
    same bytes production reads, not by imitating it."""
    return article.body or ""


def _article_for_stem(session, filename_stem: str):
    """Resolve a seed from its FILENAME — `NN-NNNN-slug-TITLE`.

    Both older routes are gone and neither failed loudly: the `.meta.json`
    sidecars were removed (the test parses volume/page from the stem instead),
    and the export-JSON fallback keys on a filename the exporter stopped using
    when it went to hash suffixes (`01-0032-86f7e4.json`).  So every seed
    resolved to MISSING, this tool quietly stopped refreshing anything, and the
    fixtures kept a `\\x01PAGE:N\\x01` token the stream had long since stopped
    carrying ([[project_page_sentinel_leftovers]]).

    The stem itself carries what the lookup needs — volume, page, and the
    section slug — so it is the durable key, no sidecar required.  The slug is
    matched as a prefix of the remainder because the TITLE tail may hold its own
    hyphens (`03-0219-s5-BAG-PIPE`); the longest matching slug wins.
    """
    try:
        vol, page = int(filename_stem[:2]), int(filename_stem[3:7])
    except ValueError:
        return None
    rest = filename_stem[8:]
    best = None
    for a in (session.query(Article)
              .filter(Article.volume == vol, Article.page_start == page,
                      Article.article_type != "plate").all()):
        slug = section_slug(a.section_name) if a.section_name else ""
        if not slug:
            slug = section_slug(a.title)
        if rest == slug or rest.startswith(slug + "-"):
            if best is None or len(slug) > best[0]:
                best = (len(slug), a)
    return best[1] if best else None


def capture_one(session, filename_stem: str) -> tuple[str, str]:
    """Capture input + body for a seed, located by its filename stem."""
    article = _article_for_stem(session, filename_stem)
    if not article:
        return ("MISSING", f"no DB row matching stem {filename_stem}")
    if article.article_type == "plate":
        return ("SKIP", "plate articles use parse_plate, not _transform_text_v2")

    joined_raw = raw_body(article)
    if not joined_raw:
        return ("MISSING", "article has no body")
    first_page = article.page_start

    # IMPORTANT: snapshot the IMMEDIATE output of `_transform_text_v2`,
    # not the eventually-exported article body.  The exported body
    # passes through downstream phases (resolve_xrefs translates `LN`
    # markers to filename targets; a page-marker translator converts
    # ws-page numbers to printed-page numbers; per-article qualifier
    # strip) that are not part of the transform under test.  Locking
    # those in would defeat the snapshot's purpose.
    # Produce EXACTLY as `test_transform_snapshots` does — `_source_clean`, the
    # re-appliable half of `preprocess`, NOT the full pass.  The full pass
    # re-runs quote-run over already-converted markup; the test says so and
    # computes the other way, so a fixture captured through `preprocess` would
    # disagree with its own check the moment the two diverged.
    body = process_elements(_source_clean(joined_raw),
                            ElementContext(volume=article.volume))

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
