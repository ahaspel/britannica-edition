"""Targeted verify: shadow-transform a list of articles and diff
against the DB baseline.  Fast iteration for in-progress refactors —
verify_refactor.py walks 37k articles in ~25 min; this walks the
subset you care about (a TSV of prior mismatches, a comma-list of
titles, or a vol-page list) in seconds.

Usage:
    # From a verify_refactor TSV (`id\\tvol-page\\ttitle` per line):
    uv run python tools/diagnostics/verify_targeted.py tools/_scratch/_vm_consolidation.tsv

    # From explicit titles:
    uv run python tools/diagnostics/verify_targeted.py --titles ABERRATION,CEMENT,CLOCK

    # Show diff context for each mismatching article:
    uv run python tools/diagnostics/verify_targeted.py tools/_scratch/_vm.tsv --diff

Categories printed:
    PASS  — shadow == DB body (article is clean against baseline)
    DIFF  — shadow != DB body (mismatch present, with shape annotated)
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.elements._figure_faithful import (
    produce_faithful_figure,
)
from britannica.pipeline.stages.transform_articles import _transform_text_v2


def _shadow(session, a: Article) -> str:
    segs = (session.query(ArticleSegment)
            .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == a.id)
            .order_by(ArticleSegment.sequence_in_article)
            .add_columns(SourcePage.page_number).all())
    if not segs:
        return ""
    if a.article_type == "plate":
        raw = segs[0][0].segment_text or ""
        return produce_faithful_figure(raw) if raw else ""
    raw_parts = [f"\x01PAGE:{pg}\x01{seg.segment_text or ''}" for seg, pg in segs]
    joined = "\n".join(raw_parts)
    joined = re.sub(r"(\w)-\n(\x01PAGE:\d+\x01)(\w)", r"\1\2\3", joined)
    return _transform_text_v2(joined, a.volume, segs[0][1])


def _diff_shape(old: str, new: str) -> tuple[str, str]:
    """Return (shape, sample_window). `shape` is a short tag describing
    what kind of diff this is.  `sample_window` is ~80 chars of context
    around the first diff (or "" if length-only)."""
    if old == new:
        return "match", ""
    for i, (a, b) in enumerate(zip(old, new)):
        if a != b:
            ctx_old = old[max(0, i-40):i+80]
            ctx_new = new[max(0, i-40):i+80]
            # Categorise by what's in the immediate vicinity
            scope = old[max(0, i-60):i+100] + new[max(0, i-60):i+100]
            if re.search(r"\{\{IMG:[^}]*\}\}\s*«SC»Fig", scope):
                shape = "dup-fig-caption"
            elif "{{IMG:" in scope and ctx_old.count("{{IMG:") != ctx_new.count("{{IMG:"):
                shape = "img-count-diff"
            elif "«HTMLTABLE:" in scope:
                shape = "htmltable"
            elif "{{TABLE:" in scope or "}TABLE}" in scope:
                if ctx_old.count("|") > ctx_new.count("|") + 1:
                    shape = "table-cells-lost"
                elif ctx_new.count("|") > ctx_old.count("|") + 1:
                    shape = "table-cells-gained"
                else:
                    shape = "table-content"
            elif "{{LEGEND:" in scope or "}LEGEND}" in scope:
                shape = "legend"
            else:
                shape = "body"
            return shape, f"OLD {ctx_old!r}\n         NEW {ctx_new!r}"
    # Length-only diff
    if len(old) < len(new):
        return "tail-added", f"+{len(new) - len(old)} chars: ...{new[len(old):][:80]!r}"
    return "tail-lost", f"-{len(old) - len(new)} chars: ...{old[len(new):][:80]!r}"


def _read_targets_from_tsv(path: Path) -> list[tuple[int | None, str]]:
    """Read (id, title) pairs from a verify_refactor TSV.  Uses id
    when present (column 1) for O(1) lookups; falls back to title
    when id is missing or invalid."""
    targets: list[tuple[int | None, str]] = []
    seen_titles = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            aid: int | None = int(parts[0])
        except ValueError:
            aid = None
        t = parts[2].strip()
        if t and t not in seen_titles:
            seen_titles.add(t)
            targets.append((aid, t))
    return targets


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("tsv", nargs="?", type=Path,
                   help="TSV from verify_refactor (id\\tvol-page\\ttitle)")
    p.add_argument("--titles", help="comma-separated article titles")
    p.add_argument("--diff", action="store_true",
                   help="print first-diff window for each DIFF article")
    p.add_argument("--limit", type=int, help="cap article count")
    args = p.parse_args()

    targets: list[tuple[int | None, str]] = []
    if args.tsv:
        targets = _read_targets_from_tsv(args.tsv)
    if args.titles:
        for t in args.titles.split(","):
            t = t.strip()
            if t:
                targets.append((None, t))
    if not targets:
        print("no targets given", file=sys.stderr)
        return 1
    if args.limit:
        targets = targets[: args.limit]

    shapes: Counter[str] = Counter()
    diff_samples: dict[str, list[tuple[str, str]]] = {}
    pass_count = 0
    not_found: list[str] = []

    t0 = time.monotonic()
    session = SessionLocal()
    try:
        # Resolve any titles-only entries to IDs in one batch (single
        # query covers all the title-only targets at once instead of
        # one full table scan per title).
        title_only = [t for aid, t in targets if aid is None]
        title_to_id: dict[str, int] = {}
        if title_only:
            rows = session.execute(
                select(Article.id, Article.title).where(
                    Article.title.in_(title_only))
            ).all()
            title_to_id = {t: i for i, t in rows}

        last_print = time.monotonic()
        for idx, (aid, title) in enumerate(targets):
            if aid is None:
                aid = title_to_id.get(title)
            a = session.get(Article, aid) if aid else None
            if a is None:
                not_found.append(title)
                continue
            old = a.body or ""
            try:
                new = _shadow(session, a)
            except Exception as exc:
                shapes["EXCEPTION"] += 1
                if args.diff:
                    diff_samples.setdefault("EXCEPTION", []).append(
                        (title, f"{type(exc).__name__}: {exc}"))
                session.expire(a)
                continue
            shape, sample = _diff_shape(old, new)
            if shape == "match":
                pass_count += 1
            else:
                shapes[shape] += 1
                diff_samples.setdefault(shape, []).append((title, sample))
            session.expire(a)
            now = time.monotonic()
            if now - last_print > 3:
                print(f"  {idx + 1}/{len(targets)} "
                      f"({pass_count} pass, {sum(shapes.values())} diff)",
                      file=sys.stderr, flush=True)
                last_print = now
    finally:
        session.close()

    elapsed = time.monotonic() - t0
    total = len(targets) - len(not_found)
    diff_count = sum(shapes.values())
    print(f"\nChecked {total} articles in {elapsed:.1f}s")
    print(f"  PASS: {pass_count}")
    print(f"  DIFF: {diff_count}")
    if not_found:
        print(f"  NOT FOUND: {len(not_found)} ({', '.join(not_found[:3])}…)")
    print()
    for shape, n in shapes.most_common():
        print(f"  [{shape}]  {n}")
        if args.diff:
            for t, s in diff_samples.get(shape, [])[:5]:
                print(f"    {t}")
                print(f"      {s}")
            if len(diff_samples.get(shape, [])) > 5:
                print(f"    ... + {len(diff_samples[shape]) - 5} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
