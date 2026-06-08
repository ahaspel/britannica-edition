"""Audit what `_strip_templates` is silently deleting across articles.

Instruments the catch-all to capture every match BEFORE the strip
actually deletes it.  Iterates over ARTICLES (via the DB), NOT raw
pages — front matter, plates, and other non-article content go
through different pipelines and aren't relevant to article-body
catch-all behaviour.

Templates are bucketed by full name (e.g. ``EB1911 article link``,
not lazily collapsed to a first token), so producer-handler gap
analysis can pinpoint each variant.

Usage:
    uv run python tools/diagnostics/audit_strip_templates.py snapshots
    uv run python tools/diagnostics/audit_strip_templates.py articles
    uv run python tools/diagnostics/audit_strip_templates.py articles --volumes 1 2 3
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

from britannica.pipeline.stages.transform_articles import (  # noqa: E402
    _transform_text_v2,
)
from britannica.pipeline.stages.transform_articles import body_text as bt  # noqa: E402


# ── Instrumentation ──────────────────────────────────────────────────

# Full-name extractor: `{{NAME|...}}` or `{{NAME}}` — captures the
# complete template name including embedded spaces.  Stops at `|` or
# `}}`.  Different from the lazy first-token tokenizer; an
# ``{{EB1911 article link|...}}`` template's NAME is the full
# ``EB1911 article link``, not just ``eb1911``.
_TEMPLATE_NAME_RE = re.compile(r"\{\{\s*([^|{}\n]+?)\s*(?:\||\}\})")

_phase1_matches: Counter[str] = Counter()
_phase1_samples: dict[str, list[str]] = defaultdict(list)
_phase2_count = 0
_phase3_count = 0
_phase4_count = 0
_phase5_count = 0
_phase6_count = 0
_phase2_samples: list[str] = []
_phase3_samples: list[str] = []
_phase4_samples: list[str] = []
_phase5_samples: list[str] = []
_phase6_samples: list[str] = []
_SAMPLE_LIMIT = 10


def _name_of(template: str) -> str:
    m = _TEMPLATE_NAME_RE.match(template)
    return (m.group(1).strip().lower() if m else "<unparseable>")


def _context(text: str, pos: int, width: int = 120) -> str:
    lo = max(0, pos - width)
    hi = min(len(text), pos + width)
    return text[lo:hi].replace("\n", "\\n")


def _instrumented_strip_templates(text: str) -> str:
    global _phase2_count, _phase3_count
    global _phase4_count, _phase5_count, _phase6_count

    # Phase 1 — iterated template strip.
    prev = None
    while prev != text:
        prev = text
        for m in bt._STRIP_TEMPLATES_RE.finditer(text):
            blob = m.group(0)
            name = _name_of(blob)
            _phase1_matches[name] += 1
            if len(_phase1_samples[name]) < 5:
                _phase1_samples[name].append(blob[:200])
        text = bt._STRIP_TEMPLATES_RE.sub("", text)

    # Phase 2 — orphan `}}` lines.
    orphan_close_re = re.compile(r"^\s*\}\}+\s*$", re.MULTILINE)
    for m in orphan_close_re.finditer(text):
        _phase2_count += 1
        if len(_phase2_samples) < _SAMPLE_LIMIT:
            _phase2_samples.append(_context(text, m.start()))
    text = orphan_close_re.sub("", text)

    # Phase 3 — per-line excess `}}`.
    def _strip_excess_closers(m):
        global _phase3_count
        line = m.group(0)
        opens = len(re.findall(r"\{\{", line))
        closes = len(re.findall(r"\}\}", line))
        if closes > opens:
            excess = closes - opens
            _phase3_count += excess
            if len(_phase3_samples) < _SAMPLE_LIMIT:
                _phase3_samples.append(line[:240].replace("\n", "\\n"))
            return re.sub(r"(\}\})" * excess + r"\s*$", "", line)
        return line
    text = re.sub(r"^.*$", _strip_excess_closers, text, flags=re.MULTILINE)

    # Phase 4-6.
    table_close_re = re.compile(r"^\s*\|\}+\s*$", re.MULTILINE)
    table_open_re = re.compile(r"^\s*\{\|\s*$", re.MULTILINE)
    row_sep_re = re.compile(r"^\s*\|-\s*$", re.MULTILINE)
    for m in table_close_re.finditer(text):
        _phase4_count += 1
        if len(_phase4_samples) < _SAMPLE_LIMIT:
            _phase4_samples.append(_context(text, m.start()))
    for m in table_open_re.finditer(text):
        _phase5_count += 1
        if len(_phase5_samples) < _SAMPLE_LIMIT:
            _phase5_samples.append(_context(text, m.start()))
    for m in row_sep_re.finditer(text):
        _phase6_count += 1
        if len(_phase6_samples) < _SAMPLE_LIMIT:
            _phase6_samples.append(_context(text, m.start()))
    text = table_close_re.sub("", text)
    text = table_open_re.sub("", text)
    text = row_sep_re.sub("", text)
    return text


def _patch():
    bt._strip_templates = _instrumented_strip_templates


def _process_snapshots() -> int:
    n = 0
    snap = Path("tests/snapshots/transform")
    for meta_path in sorted(snap.glob("*.meta.json")):
        stem = meta_path.name.removesuffix(".meta.json")
        raw = (snap / f"{stem}.input.txt").read_text(encoding="utf-8")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        _transform_text_v2(raw, meta["volume"], meta["page_number"])
        n += 1
    return n


def _process_articles(volumes: list[int] | None = None) -> int:
    """Iterate ARTICLES via the DB (filtering out plates / front matter
    / etc.).  Mirrors what production transform_articles processes."""
    from britannica.db.models import Article, ArticleSegment, SourcePage
    from britannica.db.session import SessionLocal
    from sqlalchemy.orm import sessionmaker

    n = 0
    s = SessionLocal()
    try:
        q = (s.query(Article)
             .filter(Article.article_type != "plate"))
        if volumes:
            q = q.filter(Article.volume.in_(volumes))
        articles = q.order_by(Article.volume, Article.page_start).all()
        total = len(articles)
        for i, article in enumerate(articles):
            segments = (
                s.query(ArticleSegment)
                .join(SourcePage,
                      ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == article.id)
                .order_by(ArticleSegment.sequence_in_article)
                .add_columns(SourcePage.page_number)
                .all()
            )
            if not segments:
                continue
            joined_raw = "".join(
                seg.segment_text or "" for seg, page_number in segments)
            first_page = segments[0][1]
            try:
                _transform_text_v2(joined_raw, article.volume, first_page)
            except Exception as e:
                print(f"  ! article id={article.id}: "
                      f"{type(e).__name__}: {e}", file=sys.stderr)
            n += 1
            if n % 500 == 0:
                print(f"  {n}/{total} articles processed",
                      file=sys.stderr)
    finally:
        s.close()
    return n


def _report(scope_label: str, page_count: int) -> None:
    out: list[str] = []
    out.append(f"# _strip_templates audit -- {scope_label}")
    out.append(f"# articles processed: {page_count}")
    out.append("")
    out.append("## Phase 1 -- template strip (full template name -> count)")
    out.append("")
    total = sum(_phase1_matches.values())
    out.append(f"total deletions: {total}")
    out.append("")
    if _phase1_matches:
        out.append(f"{'count':>8s}  {'name':40s}  sample")
        out.append("-" * 130)
        for name, count in _phase1_matches.most_common():
            sample = _phase1_samples[name][0] if _phase1_samples[name] else ""
            sample = sample.replace("\n", " ")[:80]
            out.append(f"{count:>8d}  {name:40s}  {sample}")
        out.append("")
    out.append("## Phases 2-6 -- orphan markup (LIKELY EVIDENCE OF UPSTREAM LOSS)")
    out.append("")
    out.append(f"  phase 2 (orphan `}}}}` lines):       {_phase2_count}")
    out.append(f"  phase 3 (per-line excess `}}}}`):    {_phase3_count}")
    out.append(f"  phase 4 (orphan `|}}` lines):       {_phase4_count}")
    out.append(f"  phase 5 (orphan `{{|` lines):       {_phase5_count}")
    out.append(f"  phase 6 (orphan `|-` lines):       {_phase6_count}")
    out.append("")
    for label, samples in (
        ("phase 2", _phase2_samples),
        ("phase 3", _phase3_samples),
        ("phase 4", _phase4_samples),
        ("phase 5", _phase5_samples),
        ("phase 6", _phase6_samples),
    ):
        if not samples:
            continue
        out.append(f"### {label} samples")
        for s in samples:
            out.append(f"  {s[:200]}")
        out.append("")
    out_path = Path("tools/_scratch/strip_templates_audit.txt")
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {out_path}", file=sys.stderr)
    # Print head to stdout
    for line in out[:60]:
        print(line)


def main() -> int:
    _patch()
    if len(sys.argv) < 2 or sys.argv[1] == "snapshots":
        n = _process_snapshots()
        _report("snapshot articles", n)
    elif sys.argv[1] == "articles":
        vols = None
        if len(sys.argv) > 2 and sys.argv[2] == "--volumes":
            vols = [int(v) for v in sys.argv[3:]]
        n = _process_articles(vols)
        scope = f"articles in volumes {vols}" if vols else "all articles"
        _report(scope, n)
    else:
        print(f"unknown scope: {sys.argv[1]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
