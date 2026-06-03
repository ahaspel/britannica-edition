"""Differential test: re-run transform + export, compare to baseline.

The baseline is whatever's currently in the DB (``article.body``) and on
disk (``data/derived/articles/*.json``).  This script does not mutate
either — it computes what the current code would produce for each
article and reports any mismatch.

What it catches:

  * Behavior changes in ``transform_articles._transform_text_v2`` and
    everything it calls (``elements/*``, body-text pipeline).
  * Behavior changes in ``parsers.plate.parse_plate`` for plate articles.
  * Behavior changes in ``export.article_json.export_articles_to_json``
    and what it composes (sections, body_postprocess, pages, xref wrap,
    contributor resolution).

What it does not catch:

  * Behavior changes in stages whose outputs landed in the DB before
    transform (boundary detection, classification, image extraction,
    contributor / xref extraction).  Those are unchanged by this
    refactor; a full rebuild would still verify them.

There is also a *full-pipeline* shadow (``--full``): for every article it
recomputes the body via ``_shadow_transform`` and feeds that body into
``export_articles_to_json`` (via its ``body_override`` seam), then diffs
the resulting JSON against ``data/derived/articles/``.  This is the check
to use for burndown work that fixes a leak at its producer: the transform
output legitimately changes, but the shipped JSON should stay
byte-identical — which the plain ``--transform-only`` / ``--export-only``
runs can't confirm because the DB still holds the pre-change body.

Usage:

    uv run python tools/diagnostics/verify_refactor.py
    uv run python tools/diagnostics/verify_refactor.py --volume 1
    uv run python tools/diagnostics/verify_refactor.py --limit 200
    uv run python tools/diagnostics/verify_refactor.py --transform-only
    uv run python tools/diagnostics/verify_refactor.py --export-only
    uv run python tools/diagnostics/verify_refactor.py --full
    uv run python tools/diagnostics/verify_refactor.py --full --volume 15
    uv run python tools/diagnostics/verify_refactor.py --diff 5
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.export.article_json import export_articles_to_json
from britannica.pipeline.stages.elements._figure_faithful import (
    produce_faithful_figure,
)
from britannica.pipeline.stages.transform_articles import _transform_text_v2

# Note: there is no longer any body-cleanup pass — each producer
# (transform/parse_plate) emits its body cleanly in isolation, so the
# export shadow output already matches what ships.


ARTICLES_DIR = Path("data/derived/articles")


# ── progress logging ─────────────────────────────────────────────────────
#
# A long shadow run must be inspectable mid-flight (and killable if it's
# gone wrong) — not a black box that only prints on exit.  Stdout here is
# usually a harness-captured pipe that buffers until the process ends, so
# per-unit `print(flush=True)` lines never reach an on-disk file while the
# run is live.  `log()` therefore also writes to a script-owned log file
# opened line-buffered, which IS flushed per line regardless of how stdout
# is redirected.  `tail -f` that file to watch progress; kill the process
# if the mismatch count starts climbing.
_LOG_FH = None


def log(msg: str = "") -> None:
    print(msg, flush=True)
    if _LOG_FH is not None:
        _LOG_FH.write(msg + "\n")
        _LOG_FH.flush()


# ── transform shadow ────────────────────────────────────────────────────


def _shadow_transform(session, article: Article) -> str:
    """Replicate what ``transform_articles.transform_articles()`` does
    for a single article, but return the would-be body instead of
    writing it to the DB.  Mirrors __init__.py:670-722.
    """
    segments = (
        session.query(ArticleSegment)
        .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
        .filter(ArticleSegment.article_id == article.id)
        .order_by(ArticleSegment.sequence_in_article)
        .add_columns(SourcePage.page_number)
        .all()
    )
    if not segments:
        return ""

    if article.article_type == "plate":
        raw = segments[0][0].segment_text or ""
        return produce_faithful_figure(raw) if raw else ""

    raw_parts = []
    for seg, page_number in segments:
        raw = seg.segment_text or ""
        raw_parts.append(f"\x01PAGE:{page_number}\x01{raw}")
    joined_raw = "\n".join(raw_parts)
    joined_raw = re.sub(
        r"(\w)-\n(\x01PAGE:\d+\x01)(\w)",
        r"\1\2\3", joined_raw,
    )
    if not joined_raw:
        return ""

    body = _transform_text_v2(
        joined_raw, article.volume,
        segments[0][1] if segments else 0,
    )

    # Strip redundant title qualifier (driver does this after transform).
    if body and ", " in article.title:
        qualifier = article.title.split(", ", 1)[1]
        body_clean = re.sub(
            r"[«»](?:SC|/SC|I|/I|B|/B)[«»]",
            "", body[:200],
        )
        paren_q = f"({qualifier})"
        if body_clean.lstrip("\x01PAGE:0123456789").lstrip().lower().startswith(paren_q.lower()):
            body = re.sub(
                r"^(\x01PAGE:\d+\x01)?\s*\([^)]*\)[,;\s]*",
                r"\1", body,
            )
    return body


def check_transform(volume: int | None, limit: int | None, diff_n: int,
                    only_ids: set[int] | None = None,
                    mismatch_log: Path | None = None
                    ) -> tuple[int, int, list[tuple[str, str, str]]]:
    """Returns (n_checked, n_mismatches, sample_diffs)."""
    session = SessionLocal()
    mismatch_fh = mismatch_log.open("w", encoding="utf-8") if mismatch_log else None
    try:
        q = select(Article.id).order_by(Article.volume, Article.page_start, Article.id)
        if volume is not None:
            q = q.where(Article.volume == volume)
        if only_ids is not None:
            q = q.where(Article.id.in_(only_ids))
        if limit is not None:
            q = q.limit(limit)
        ids = [row[0] for row in session.execute(q).all()]

        n_checked = 0
        n_mismatches = 0
        sample_diffs: list[tuple[str, str, str]] = []
        last_print = time.monotonic()

        for aid in ids:
            article = session.get(Article, aid)
            if article is None:
                continue
            expected = article.body or ""
            try:
                actual = _shadow_transform(session, article)
            except Exception as exc:
                actual = f"<EXCEPTION: {type(exc).__name__}: {exc}>"

            n_checked += 1
            if actual != expected:
                n_mismatches += 1
                if mismatch_fh:
                    mismatch_fh.write(f"{article.id}\t{article.volume:02d}-{article.page_start:04d}\t{article.title}\n")
                    mismatch_fh.flush()
                if len(sample_diffs) < diff_n:
                    sample_diffs.append((
                        f"{article.volume:02d}-{article.page_start:04d}-{article.title}",
                        expected,
                        actual,
                    ))
            session.expire(article)

            now = time.monotonic()
            if now - last_print > 5:
                log(f"  transform: {n_checked}/{len(ids)} "
                    f"({n_mismatches} mismatches)")
                last_print = now

        return n_checked, n_mismatches, sample_diffs
    finally:
        session.close()
        if mismatch_fh:
            mismatch_fh.close()


# ── export shadow ───────────────────────────────────────────────────────


def _list_volumes() -> list[int]:
    session = SessionLocal()
    try:
        return sorted(
            v for (v,) in session.execute(
                select(Article.volume).distinct()
            ).all()
        )
    finally:
        session.close()


def _diff_json_files(baseline: Path, candidate: Path) -> str | None:
    """Return a short diff summary or None if equal."""
    try:
        baseline_bytes = baseline.read_bytes()
        candidate_bytes = candidate.read_bytes()
    except FileNotFoundError as e:
        return f"missing: {e}"
    if baseline_bytes == candidate_bytes:
        return None
    # JSON semantic compare so trivial key-order or whitespace
    # differences don't dominate the report.
    try:
        bd = json.loads(baseline_bytes.decode("utf-8"))
        cd = json.loads(candidate_bytes.decode("utf-8"))
    except Exception:
        return f"bytes differ ({len(baseline_bytes)} vs {len(candidate_bytes)})"
    if bd == cd:
        return None
    # Find first differing top-level key.
    keys = set(bd) | set(cd)
    diffs = []
    for k in sorted(keys):
        if bd.get(k) != cd.get(k):
            b = bd.get(k)
            c = cd.get(k)
            if isinstance(b, str) and isinstance(c, str):
                # Inline char-level summary.
                for i, (cb, cc) in enumerate(zip(b, c)):
                    if cb != cc:
                        start = max(0, i - 20)
                        end = min(len(b), i + 40)
                        diffs.append(
                            f"key={k!r} @char {i}: "
                            f"{b[start:end]!r} vs {c[start:end]!r}"
                        )
                        break
                else:
                    diffs.append(
                        f"key={k!r} length differs ({len(b)} vs {len(c)})"
                    )
            else:
                diffs.append(f"key={k!r} differs")
            if len(diffs) >= 2:
                break
    return "; ".join(diffs) or "(structural diff)"


def check_export(volume: int | None, limit: int | None, diff_n: int) -> tuple[int, int, list[tuple[str, str]]]:
    """Returns (n_checked, n_mismatches, sample_diffs)."""
    volumes = [volume] if volume is not None else _list_volumes()
    n_checked = 0
    n_mismatches = 0
    sample_diffs: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="verify_refactor_") as tmp:
        tmp_dir = Path(tmp)
        for vol in volumes:
            log(f"  export: volume {vol} -> tmp")
            try:
                export_articles_to_json(vol, tmp_dir)
            except Exception as exc:
                log(f"    EXPORT EXCEPTION vol {vol}: {exc}")
                n_mismatches += 1
                if len(sample_diffs) < diff_n:
                    sample_diffs.append((f"<volume {vol}>", str(exc)))
                continue

            volume_files = sorted(
                p for p in tmp_dir.iterdir()
                if p.suffix == ".json" and p.name.startswith(f"{vol:02d}-")
            )
            if limit is not None:
                volume_files = volume_files[:limit]

            for tmp_file in volume_files:
                baseline_file = ARTICLES_DIR / tmp_file.name
                diff = _diff_json_files(baseline_file, tmp_file)
                n_checked += 1
                if diff is not None:
                    n_mismatches += 1
                    if len(sample_diffs) < diff_n:
                        sample_diffs.append((tmp_file.name, diff))

            # Drop volume's tmp files so the temp dir doesn't grow.
            for p in volume_files:
                try:
                    p.unlink()
                except OSError:
                    pass

    return n_checked, n_mismatches, sample_diffs


# ── full-pipeline shadow ────────────────────────────────────────────────


def check_full(volume: int | None, limit: int | None, diff_n: int,
               mismatch_log: Path | None = None
               ) -> tuple[int, int, int, list[tuple[str, str]]]:
    """Recompute every article's body via ``_shadow_transform``, re-export
    with those bodies as ``body_override``, diff against the on-disk
    baseline (``data/derived/articles/``).

    Returns ``(n_files_checked, n_bodies_changed, n_mismatches, sample_diffs)``.
    ``n_bodies_changed`` is informational — it's how many articles the
    current code would produce a different *pre-export* body for than what
    the DB holds (i.e. the scope of whatever transform-stage change is in
    flight); it is not itself a failure.
    """
    volumes = [volume] if volume is not None else _list_volumes()
    n_checked = 0
    n_bodies_changed = 0
    n_mismatches = 0
    sample_diffs: list[tuple[str, str]] = []
    mismatch_fh = mismatch_log.open("w", encoding="utf-8") if mismatch_log else None

    session = SessionLocal()
    try:
        with tempfile.TemporaryDirectory(prefix="verify_refactor_full_") as tmp:
            tmp_dir = Path(tmp)
            for vol in volumes:
                articles = (
                    session.query(Article)
                    .filter(Article.volume == vol)
                    .order_by(Article.page_start, Article.page_end, Article.title)
                    .all()
                )
                if limit is not None:
                    articles = articles[:limit]

                overrides: dict[int, str] = {}
                vol_changed = 0
                for article in articles:
                    try:
                        shadow = _shadow_transform(session, article)
                    except Exception as exc:
                        shadow = f"<EXCEPTION: {type(exc).__name__}: {exc}>"
                    overrides[article.id] = shadow
                    if shadow != (article.body or ""):
                        vol_changed += 1
                n_bodies_changed += vol_changed
                log(f"  full: volume {vol} -> tmp "
                    f"({len(articles)} articles, {vol_changed} bodies changed)")

                try:
                    export_articles_to_json(vol, tmp_dir, body_override=overrides)
                except Exception as exc:
                    log(f"    EXPORT EXCEPTION vol {vol}: {exc}")
                    n_mismatches += 1
                    if len(sample_diffs) < diff_n:
                        sample_diffs.append((f"<volume {vol}>", str(exc)))
                    session.expunge_all()
                    continue

                volume_files = sorted(
                    p for p in tmp_dir.iterdir()
                    if p.suffix == ".json" and p.name.startswith(f"{vol:02d}-")
                )
                for tmp_file in volume_files:
                    baseline_file = ARTICLES_DIR / tmp_file.name
                    diff = _diff_json_files(baseline_file, tmp_file)
                    n_checked += 1
                    if diff is not None:
                        n_mismatches += 1
                        if mismatch_fh:
                            mismatch_fh.write(f"{tmp_file.name}\t{diff}\n")
                            mismatch_fh.flush()
                        if len(sample_diffs) < diff_n:
                            sample_diffs.append((tmp_file.name, diff))
                for p in volume_files:
                    try:
                        p.unlink()
                    except OSError:
                        pass
                session.expunge_all()

        return n_checked, n_bodies_changed, n_mismatches, sample_diffs
    finally:
        session.close()
        if mismatch_fh:
            mismatch_fh.close()


# ── main ────────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--volume", type=int, help="restrict to one volume")
    p.add_argument("--limit", type=int, help="cap article count")
    p.add_argument("--diff", type=int, default=3,
                   help="number of sample diffs to print per phase (default 3)")
    p.add_argument("--transform-only", action="store_true")
    p.add_argument("--export-only", action="store_true")
    p.add_argument("--full", action="store_true",
                   help="full-pipeline shadow: recompute bodies AND re-export, "
                        "diff against the on-disk baseline (use this for "
                        "burndown changes that span transform + export)")
    p.add_argument("--save-mismatches", type=Path, default=Path("verify_mismatches.tsv"),
                   help="write mismatches to this file (default verify_mismatches.tsv)")
    p.add_argument("--only-from", type=Path,
                   help="check only articles whose IDs appear in the given mismatch file")
    p.add_argument("--log", type=Path, default=Path("verify_refactor.log"),
                   help="progress log file, flushed per line so the run is "
                        "inspectable mid-flight (default verify_refactor.log)")
    args = p.parse_args()

    global _LOG_FH
    _LOG_FH = args.log.open("w", encoding="utf-8", buffering=1)

    only_ids: set[int] | None = None
    if args.only_from:
        only_ids = set()
        for line in args.only_from.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                only_ids.add(int(line.split("\t", 1)[0]))
            except (ValueError, IndexError):
                continue
        log(f"Limiting to {len(only_ids)} article IDs from {args.only_from}")

    if args.full:
        do_transform = do_export = False
        do_full = True
    else:
        do_transform = not args.export_only
        do_export = not args.transform_only
        do_full = False

    if not ARTICLES_DIR.exists():
        log(f"FATAL: {ARTICLES_DIR} not found — no baseline to compare against.")
        return 2

    overall_mismatch = 0
    try:
        if do_full:
            log("=" * 60)
            log("Full-pipeline shadow run (transform → export → diff baseline)")
            log("=" * 60)
            t0 = time.monotonic()
            n, changed, m, diffs = check_full(
                args.volume, args.limit, args.diff,
                mismatch_log=args.save_mismatches,
            )
            dt = time.monotonic() - t0
            log(f"  Checked {n} JSON files in {dt:.1f}s")
            log(f"  Bodies changed by current code vs DB: {changed}")
            log(f"  JSON mismatches vs baseline: {m}")
            if diffs:
                log()
                log("  Sample diffs:")
                for label, diff in diffs:
                    log(f"    {label}")
                    log(f"      {diff}")
            overall_mismatch += m

        if do_transform:
            log("=" * 60)
            log("Transform shadow run")
            log("=" * 60)
            t0 = time.monotonic()
            n, m, diffs = check_transform(args.volume, args.limit, args.diff,
                                           only_ids=only_ids,
                                           mismatch_log=args.save_mismatches)
            dt = time.monotonic() - t0
            log(f"  Checked {n} articles in {dt:.1f}s")
            log(f"  Mismatches: {m}")
            if diffs:
                log()
                log("  Sample diffs:")
                for label, expected, actual in diffs:
                    log(f"    --- {label} ---")
                    # Show a unified-diff snippet (first 12 lines).
                    exp_lines = expected.splitlines(keepends=False)
                    act_lines = actual.splitlines(keepends=False)
                    lines = list(difflib.unified_diff(
                        exp_lines, act_lines,
                        fromfile="baseline", tofile="refactored",
                        n=2, lineterm="",
                    ))
                    for line in lines[:12]:
                        log(f"      {line}")
                    if len(lines) > 12:
                        log(f"      ... ({len(lines) - 12} more lines)")
            overall_mismatch += m

        if do_export:
            log()
            log("=" * 60)
            log("Export shadow run")
            log("=" * 60)
            t0 = time.monotonic()
            n, m, diffs = check_export(args.volume, args.limit, args.diff)
            dt = time.monotonic() - t0
            log(f"  Checked {n} JSON files in {dt:.1f}s")
            log(f"  Mismatches: {m}")
            if diffs:
                log()
                log("  Sample diffs:")
                for label, diff in diffs:
                    log(f"    {label}")
                    log(f"      {diff}")
            overall_mismatch += m

        log()
        log("=" * 60)
        if overall_mismatch == 0:
            log("VERIFY OK — no behavior change detected on the sampled corpus.")
            return 0
        log(f"VERIFY FAIL — {overall_mismatch} total mismatches.")
        return 1
    finally:
        _LOG_FH.close()


if __name__ == "__main__":
    sys.exit(main())
