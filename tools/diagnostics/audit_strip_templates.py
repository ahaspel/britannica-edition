"""Audit what `_strip_templates` is silently deleting across the corpus.

Instruments the catch-all to capture every template match BEFORE the strip
actually deletes it, then runs the transform pipeline on a chosen scope
and reports per-template-name counts (with sample contents).

Usage:
    uv run python tools/diagnostics/audit_strip_templates.py snapshots
    uv run python tools/diagnostics/audit_strip_templates.py corpus
    uv run python tools/diagnostics/audit_strip_templates.py volumes 1 5 10
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from britannica.pipeline.stages.transform_articles import (
    _transform_text_v2,
)
from britannica.pipeline.stages.transform_articles import body_text as bt


# ── Instrumentation ──────────────────────────────────────────────────
# Each call to `_strip_templates` runs:
#   * an iterated _STRIP_TEMPLATES_RE.sub loop (phase 1 — the template strip)
#   * orphan `}}` / `{|` / `|}` / `|-` strips (phases 2-6)
# We capture matches BEFORE the substitution runs, so we see what content
# the catch-all is silently eating.

_TEMPLATE_NAME_RE = re.compile(r"\{\{\s*([^|{}<>\n\s]+)")

_phase1_matches: Counter[str] = Counter()   # template name → count
_phase1_samples: dict[str, list[str]] = defaultdict(list)
_phase2_count = 0      # orphan `}}` lines
_phase3_count = 0      # per-line excess `}}` strips
_phase4_count = 0      # orphan `|}` lines
_phase5_count = 0      # orphan `{|` lines
_phase6_count = 0      # orphan `|-` lines

# Samples of context surrounding phase 2-6 strips.  Per the user's
# guidance: orphan-marker strips are themselves lossy in disguise — if
# `}}` lands orphaned, the matching `{{` was probably eaten with its
# content.  We capture the surrounding lines so we can trace each
# orphan back to its likely loss site.
_phase2_samples: list[str] = []
_phase3_samples: list[str] = []
_phase4_samples: list[str] = []
_phase5_samples: list[str] = []
_phase6_samples: list[str] = []
_SAMPLE_LIMIT = 20


def _context(text: str, pos: int, width: int = 120) -> str:
    """Snippet around `pos` for sample logging."""
    lo = max(0, pos - width)
    hi = min(len(text), pos + width)
    return text[lo:hi].replace("\n", "\\n")


def _name_of(template: str) -> str:
    m = _TEMPLATE_NAME_RE.match(template)
    return (m.group(1).lower() if m else "<unparseable>")


def _instrumented_strip_templates(text: str) -> str:
    """Drop-in replacement that logs every match before stripping."""
    global _phase2_count, _phase3_count
    global _phase4_count, _phase5_count, _phase6_count

    # Phase 1 — iterated template strip (capture each round's matches).
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
    """Install the instrumented strip everywhere `_strip_templates` is reached.

    `_apply_markup` calls the function via its module-level name within
    `body_text`, so monkey-patching the attribute there covers the article-
    body call AND every element-producer call that goes through
    `_apply_markup` (cells, captions, refs, …)."""
    bt._strip_templates = _instrumented_strip_templates


def _process_snapshots() -> int:
    """Process every snapshot input through the transform pipeline.

    Returns article count processed."""
    n = 0
    snap = Path("tests/snapshots/transform")
    for meta_path in sorted(snap.glob("*.meta.json")):
        stem = meta_path.name.removesuffix(".meta.json")
        raw = (snap / f"{stem}.input.txt").read_text(encoding="utf-8")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        _transform_text_v2(raw, meta["volume"], meta["page_number"])
        n += 1
    return n


def _process_corpus(volumes: list[int] | None = None) -> int:
    """Process every page in the named volumes (or all volumes) through the
    transform pipeline.  Articles aren't pre-segmented here — we feed each
    page's raw wikitext directly, which is a superset of what a single
    article would receive.  This is acceptable for an audit (we want to see
    what `_strip_templates` deletes, regardless of article boundaries)."""
    n = 0
    pages_root = Path("data/raw/wikisource")
    vol_dirs = sorted(pages_root.glob("vol_*"))
    if volumes:
        wanted = {f"vol_{v}" for v in volumes}
        vol_dirs = [d for d in vol_dirs if d.name in wanted]
    for vol_dir in vol_dirs:
        vol_num = int(vol_dir.name.removeprefix("vol_"))
        for page_path in sorted(vol_dir.glob("*.json")):
            page_data = json.loads(page_path.read_text(encoding="utf-8"))
            raw = page_data.get("wikitext") or ""
            if not raw:
                continue
            page_num_m = re.search(r"page(\d+)\.json$", page_path.name)
            page_num = int(page_num_m.group(1)) if page_num_m else 0
            try:
                _transform_text_v2(raw, vol_num, page_num)
            except Exception as e:
                print(f"  ! {page_path.name}: {type(e).__name__}: {e}",
                      file=sys.stderr)
            n += 1
        print(f"  vol {vol_num}: {n} pages so far", file=sys.stderr)
    return n


def _report(scope_label: str, page_count: int) -> None:
    out: list[str] = []
    out.append(f"# _strip_templates audit — {scope_label}")
    out.append(f"# pages processed: {page_count}")
    out.append("")
    out.append("## Phase 1 — template strip (template name → count)")
    out.append("")
    total = sum(_phase1_matches.values())
    out.append(f"total deletions: {total}")
    out.append("")
    if _phase1_matches:
        out.append(f"{'name':30s}  {'count':>8s}  sample")
        out.append("-" * 100)
        for name, count in _phase1_matches.most_common():
            sample = _phase1_samples[name][0] if _phase1_samples[name] else ""
            sample = sample.replace("\n", " ")
            if len(sample) > 80:
                sample = sample[:77] + "..."
            out.append(f"{name:30s}  {count:>8d}  {sample}")
        out.append("")
    out.append("## Phases 2-6 — orphan markup (LIKELY EVIDENCE OF UPSTREAM LOSS)")
    out.append("")
    out.append("Per [[no-catchall-cleanup]]: an orphan `}}` is the half-stranded")
    out.append("closer of a `{{...}}` whose opener (and contents) got eaten")
    out.append("elsewhere.  Count is a LOWER BOUND on lossy strips.")
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
    print("\n".join(out[:50]))


def main() -> int:
    _patch()
    if len(sys.argv) < 2 or sys.argv[1] == "snapshots":
        n = _process_snapshots()
        _report("snapshots", n)
    elif sys.argv[1] == "corpus":
        n = _process_corpus()
        _report("full corpus", n)
    elif sys.argv[1] == "volumes":
        vols = [int(v) for v in sys.argv[2:]]
        n = _process_corpus(vols)
        _report(f"volumes {vols}", n)
    else:
        print(f"unknown scope: {sys.argv[1]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
