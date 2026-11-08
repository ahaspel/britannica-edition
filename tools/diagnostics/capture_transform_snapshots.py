"""Capture element-transform snapshots for a fixed set of seed articles, used
by `tests/regression/test_transform_snapshots.py`.

Each seed is a pair under ``tests/snapshots/transform/``:

  <stem>.input.txt   the FIXTURE — the article's raw body (`Article.body`)
  <stem>.body.txt    the SNAPSHOT — ``process_elements(_source_clean(input))``

The test re-runs the transform on the input and asserts the body.  Any
divergence is a behaviour change that must be intentional; re-run this tool
for the seeds it changes, read the diff, commit it with the change.  Do NOT
re-run after a purely structural refactor — snapshots should not move.

THE INPUT IS FROZEN.  By default a seed's body is regenerated from its
COMMITTED input, so a refresh records the code's change and nothing else.  It
used to re-read every input from the database, which has the source's later
edits in it (Wikisource is edited continuously — 21.7% of pages in five
months): refreshing STEAM ENGINE for a link fix on 2026-11-08 also rewrote 135
lines of its input with upstream fraction and table edits, burying the one
intended change.  Re-reading the source is a separate, deliberate act:
``--reinput``, or a seed that has no input yet.

Files are written with LF line endings — on Windows `write_text` translates to
CRLF, which git then reports as a whole-file change.

Usage::
    uv run python tools/diagnostics/capture_transform_snapshots.py [--reinput] [STEM …]
"""
from __future__ import annotations

from wikikit.corpora import current_corpus
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from wikikit.db.models import Article  # noqa: E402
from wikikit.db.session import SessionLocal  # noqa: E402
from wikikit.pipeline.stages.elements import (  # noqa: E402
    ElementContext, process_elements)
from wikikit.pipeline.stages.preprocess import _source_clean  # noqa: E402
from wikikit.util.strings import section_slug  # noqa: E402


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
EXPORT_DIR = current_corpus().derived("articles")


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


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _read_input_from_db(session, filename_stem: str):
    """(raw body, None) from the database, or (None, (status, message))."""
    article = _article_for_stem(session, filename_stem)
    if not article:
        return None, ("MISSING", f"no DB row matching stem {filename_stem}")
    if article.article_type == "plate":
        return None, ("SKIP", "plate articles are parsed by the plate path, not here")
    if not article.body:
        return None, ("MISSING", "article has no body")
    return article.body, None


def capture_one(session, filename_stem: str, *, reinput: bool) -> tuple[str, str]:
    """Regenerate a seed's body — from its committed input, or with ``reinput``
    (or no input on disk) from a fresh read of the database."""
    input_path = SNAPSHOT_DIR / f"{filename_stem}.input.txt"
    fresh = reinput or not input_path.exists()
    if fresh:
        raw, failed = _read_input_from_db(session, filename_stem)
        if failed:
            return failed
    else:
        raw = input_path.read_text(encoding="utf-8")

    # The IMMEDIATE output of the element transform, not the exported body: the
    # export's later phases (xref resolution, page-position mapping) are not
    # under test.  Produced EXACTLY as `test_transform_snapshots` does —
    # `_source_clean`, the re-appliable half of `preprocess`, NOT the full pass,
    # which would re-run quote-run over already-converted markup.  Volume comes
    # from the stem, as the test reads it.
    body = process_elements(_source_clean(raw),
                            ElementContext(volume=int(filename_stem[:2])))

    if fresh:
        _write(input_path, raw)
    _write(SNAPSHOT_DIR / f"{filename_stem}.body.txt", body)
    return ("OK", f"{'input re-read' if fresh else 'input kept   '}  "
                  f"in={len(raw):>7,}  out={len(body):>7,}")


def main() -> int:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    # Optional positional args restrict capture to those seed stems — so a new
    # seed can be captured WITHOUT rewriting the other baselines (some of which
    # are post-downstream form from add_snapshot_from_production).  No args =
    # capture every seed.
    args = sys.argv[1:]
    reinput = "--reinput" in args
    only = {a for a in args if a != "--reinput"}
    unknown = only - set(SEED_FILENAMES)
    if unknown:
        print(f"not a seed: {sorted(unknown)}; known: {SEED_FILENAMES}")
        return 1
    seeds = tuple(f for f in SEED_FILENAMES if f in only) if only else SEED_FILENAMES
    s = SessionLocal()
    try:
        widest = max(len(f) for f in seeds)
        ok = miss = skip = 0
        for stem in seeds:
            status, msg = capture_one(s, stem, reinput=reinput)
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
