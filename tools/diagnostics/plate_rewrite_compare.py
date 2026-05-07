"""Regression harness for the plate parser.

For every ``article_type='plate'`` article, runs the current
``britannica.parsers.plate.parse_plate`` and compares its output
against a stored *baseline* — a snapshot of `parse_plate`'s output
captured at a known-good moment.  The baseline is the prior accepted
state of the parser; the goal of each iteration is "don't regress
any plate against this baseline."

The original ``OLD`` reference (``transform_articles._transform_plate``)
was retired once NEW unambiguously beat OLD on every quality axis;
continuing to compare against the legacy parser stopped producing
useful signal.

Snapshot/compare modes:

* ``--snapshot``  — run the current parser on every plate and write
  ``tools/diagnostics/plate_baseline.json`` (article_id → body).
  Use this when you've reached a state worth preserving as the new
  reference.
* default mode  — load that baseline, run the current parser, and
  emit a Markdown diff report.  Fails fast if the baseline file is
  missing.

Usage:
    uv run python tools/diagnostics/plate_rewrite_compare.py \\
        --snapshot
    uv run python tools/diagnostics/plate_rewrite_compare.py \\
        --out plate_compare.md
    uv run python tools/diagnostics/plate_rewrite_compare.py \\
        --signature "wikitable depth=3 wt=multi ht=0 has_colspan" \\
        --out regalia.md
    uv run python tools/diagnostics/plate_rewrite_compare.py \\
        --vol 23 --out vol23_plates.md
    uv run python tools/diagnostics/plate_rewrite_compare.py \\
        --title "REGALIA" --out regalia.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Reuse the audit's fingerprint/signature helpers so harness clusters
# match the audit clusters exactly.
sys.path.insert(0, "tools/diagnostics")
from plate_structure_audit import fingerprint, signature  # noqa: E402

from britannica.db.models import Article, ArticleSegment  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.parsers.plate import parse_plate  # noqa: E402


_BASELINE_PATH = Path("tools/diagnostics/plate_baseline.json")


def _baseline_key(art: Article) -> str:
    """Stable per-plate identifier for the baseline JSON.

    Auto-increment article IDs change every time a volume is
    reprocessed (the wipe-and-redetect cycle assigns new IDs), so
    keying the baseline by ``art.id`` invalidates the baseline for
    every reprocessed volume.  ``(volume, page_start, title)`` is
    stable across reprocesses — same plate from same scan page with
    same title hash always produces the same key.
    """
    return f"{art.volume:02d}-{art.page_start:04d}-{art.title}"


# ---------------------------------------------------------------------------
# Body inspection
# ---------------------------------------------------------------------------

_IMG_MARKER_RE = re.compile(
    r"\{\{IMG:([^|}]+)(?:\|([^{}]*))?\}\}",
)
_LEGEND_MARKER_RE = re.compile(r"\{\{LEGEND:([\s\S]*?)\}LEGEND\}")

# Caption-leak: a caption text that contains raw wiki markup the cleaner
# missed.  Pipe inside a caption is the strongest signal because the IMG
# marker uses ``|`` as filename/caption separator — a literal ``|`` in
# the caption splits the marker.  Braces and brackets are template /
# image-link leftovers.
_CAPTION_LEAK_RE = re.compile(r"[{}|\[\]]")

# Bookend markup-leak: header/footer text that retains wiki-table cell
# attributes, template markers, or link/template brackets.  Single bare
# ``|`` is allowed in header/footer (unlikely but harmless); the markers
# below appear *only* in unstripped wikitext.
_BOOKEND_LEAK_RE = re.compile(
    r"\{\||\|\}|\[\[|\]\]|\{\{|\}\}|"
    r"colspan=|rowspan=|width=|height=|align=|valign=|"
    r"width:|height:|padding:|border:|margin:|"
    # Leaked `|-` row separator: line begins with bare hyphen.  The
    # `^` is start-of-string (the bookend was already stripped) or
    # right after a newline.
    r"(?:^|\n)\s*-(?:\s|$)"
)

# Caption-shape leak in bookend: a numbered figure caption (1., (a),
# Fig. 3) that fell through into the header or footer.  ``Plate I.`` is
# common and *legitimate* header text, so it's NOT in this regex.
_BOOKEND_CAP_SHAPE_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+\.|\([a-z]\)|Fig\.\s*\d+)",
)


def stats(body: str) -> dict:
    if not body or body == "(not yet implemented)":
        return {
            "images": 0, "captioned": 0, "legends": 0,
            "broken_caps": 0,
            "header_present": 0, "footer_present": 0,
            "header_leak": 0, "footer_leak": 0,
            "header_cap_shape": 0, "footer_cap_shape": 0,
            "header": "", "footer": "",
        }
    images = _IMG_MARKER_RE.findall(body)
    captioned = sum(1 for _fn, cap in images if cap.strip())
    broken_caps = sum(
        1 for _fn, cap in images if cap and _CAPTION_LEAK_RE.search(cap)
    )
    legends = len(_LEGEND_MARKER_RE.findall(body))
    # Header = text before the first {{IMG: or {{LEGEND: marker.
    # Footer = text after the last marker.  The two marker shapes have
    # different terminators — IMG ends in ``}}``, LEGEND ends in
    # ``}LEGEND}`` — so the regex matches both forms.  Without the
    # LEGEND alternative, every body that emitted a LEGEND would
    # spuriously place the LEGEND content in "footer text" and trip
    # the leak predicate on the marker's own ``{{``.
    _MATTER_MARKER_RE = re.compile(
        r"\{\{IMG:[^{}]*\}\}|\{\{LEGEND:[\s\S]*?\}LEGEND\}"
    )
    first_marker = _MATTER_MARKER_RE.search(body)
    last_marker = None
    for m in _MATTER_MARKER_RE.finditer(body):
        last_marker = m
    header = body[:first_marker.start()].strip() if first_marker else body.strip()
    footer = body[last_marker.end():].strip() if last_marker else ""

    header_present = 1 if header else 0
    footer_present = 1 if footer else 0
    header_leak = 1 if header and _BOOKEND_LEAK_RE.search(header) else 0
    footer_leak = 1 if footer and _BOOKEND_LEAK_RE.search(footer) else 0
    header_cap_shape = 1 if header and _BOOKEND_CAP_SHAPE_RE.search(header) else 0
    footer_cap_shape = 1 if footer and _BOOKEND_CAP_SHAPE_RE.search(footer) else 0

    return {
        "images": len(images),
        "captioned": captioned,
        "legends": legends,
        "broken_caps": broken_caps,
        "header_present": header_present,
        "footer_present": footer_present,
        "header_leak": header_leak,
        "footer_leak": footer_leak,
        "header_cap_shape": header_cap_shape,
        "footer_cap_shape": footer_cap_shape,
        "header": header[:120],
        "footer": footer[:120],
    }


def score(s: dict) -> dict:
    """Reduce per-plate stats to three comparable scalars.

    * ``matter`` — content recovered, weighted by semantic role.  An
      image is 1, a captioned image is 1, a legend is 1, a clean
      header or footer is 2 (a bookend typically holds title plus
      attribution, the equivalent of two legends; weighting to that
      level prevents legends-to-footer routing from showing up as a
      regression when it's actually a structural improvement).
    * ``penalty`` — broken IMG markers + bookend markup leaks +
      caption-shape leaks into bookends.
    * ``bookend_clean`` — header/footer present AND not leaking.  Used
      as a tiebreaker when matter and penalty are equal.
    """
    bookend_clean = (
        (s["header_present"] and not s["header_leak"])
        + (s["footer_present"] and not s["footer_leak"])
    )
    matter = (
        s["images"] + s["captioned"] + s["legends"]
        + bookend_clean * 2
    )
    penalty = (
        s["broken_caps"]
        + s["header_leak"] + s["footer_leak"]
        + s["header_cap_shape"] + s["footer_cap_shape"]
    )
    return {"matter": matter, "penalty": penalty,
            "bookend_clean": bookend_clean}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
# Five categories, ordered worst-first for sorting:
#   regression — NEW lost matter, OR added penalty for same/less matter
#   mixed      — NEW gained matter but added penalty (or lost matter
#                but reduced penalty); judgement call required
#   equal      — same matter, same penalty, same bookend, but bodies
#                differ verbatim (visual diff)
#   better     — NEW recovered more matter and/or fewer leaks
#   identical  — bodies are byte-identical

VERDICT_ORDER = ["regression", "mixed", "equal", "better", "identical"]
VERDICT_LABEL = {
    "regression": "🔽 regression",
    "mixed":      "🟡 mixed",
    "equal":      "↔ equal scores, different output",
    "better":     "🟢 better",
    "identical":  "✅ identical",
}


def classify(old_s: dict, new_s: dict, bodies_equal: bool) -> tuple[str, int]:
    """Return (category, severity).

    ``severity`` is a sortable integer where larger = worse regression.
    For non-regressions it's 0 or negative (better outcomes more
    negative).  Used to order the report worst-first.
    """
    if bodies_equal:
        return "identical", 0
    o, n = score(old_s), score(new_s)
    matter_delta = n["matter"] - o["matter"]      # +ve = NEW gained
    penalty_delta = n["penalty"] - o["penalty"]   # +ve = NEW added leaks
    bookend_delta = n["bookend_clean"] - o["bookend_clean"]

    if matter_delta == 0 and penalty_delta == 0 and bookend_delta == 0:
        return "equal", 0
    # Pure better: matter up (or same) and penalty down (or same), with
    # at least one strict improvement.
    if matter_delta >= 0 and penalty_delta <= 0:
        improvement = matter_delta - penalty_delta + bookend_delta
        return "better", -improvement
    # Pure regression: matter down (or same) and penalty up (or same),
    # at least one strict regression.
    if matter_delta <= 0 and penalty_delta >= 0:
        severity = (-matter_delta) * 10 + penalty_delta - bookend_delta
        return "regression", severity
    # Otherwise mixed: one axis up, the other up too (or down)
    severity = max(0, -matter_delta) * 5 + max(0, penalty_delta)
    return "mixed", severity


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_one(art: Article, raw: str, sig: tuple,
               source_excerpt_chars: int,
               base_body: str, cur_body: str,
               base_stats: dict, cur_stats: dict,
               category: str, severity: int) -> str:
    """Markdown section for a single plate.

    Bodies and stats are passed in (already computed by the driver so
    classification and sorting can happen before rendering).
    """
    out: list[str] = []
    sig_str = " ".join(s for s in sig if s)
    out.append(f"## {art.title} — vol {art.volume:02d}")
    out.append("")
    out.append(f"**Article ID:** {art.id}  ")
    out.append(f"**Signature:** `{sig_str}`")
    out.append("")

    out.append("### Source excerpt")
    out.append("```")
    out.append(raw[:source_excerpt_chars] +
               ("\n…" if len(raw) > source_excerpt_chars else ""))
    out.append("```")
    out.append("")

    base_score = score(base_stats)
    cur_score = score(cur_stats)

    out.append("### Stats")
    out.append("")
    out.append("| | baseline | current |")
    out.append("|---|---|---|")
    out.append(f"| images          | {base_stats['images']} | {cur_stats['images']} |")
    out.append(f"| captioned       | {base_stats['captioned']} | {cur_stats['captioned']} |")
    out.append(f"| legends         | {base_stats['legends']} | {cur_stats['legends']} |")
    out.append(f"| broken caps     | {base_stats['broken_caps']} | {cur_stats['broken_caps']} |")
    out.append(f"| header leak     | {base_stats['header_leak']} | {cur_stats['header_leak']} |")
    out.append(f"| footer leak     | {base_stats['footer_leak']} | {cur_stats['footer_leak']} |")
    out.append(f"| header cap-shape| {base_stats['header_cap_shape']} | {cur_stats['header_cap_shape']} |")
    out.append(f"| footer cap-shape| {base_stats['footer_cap_shape']} | {cur_stats['footer_cap_shape']} |")
    out.append(f"| **matter**      | **{base_score['matter']}** | **{cur_score['matter']}** |")
    out.append(f"| **penalty**     | **{base_score['penalty']}** | **{cur_score['penalty']}** |")
    out.append(f"| **bookend_clean** | **{base_score['bookend_clean']}** | **{cur_score['bookend_clean']}** |")
    out.append(f"| header text     | {base_stats['header']!r} | {cur_stats['header']!r} |")
    out.append(f"| footer text     | {base_stats['footer']!r} | {cur_stats['footer']!r} |")
    out.append("")

    verdict = VERDICT_LABEL[category]
    if category in ("regression", "mixed"):
        verdict += f" (severity {severity})"
    out.append(f"**Verdict:** {verdict}")
    out.append("")

    out.append("### Baseline body")
    out.append("```")
    out.append(base_body or "(empty)")
    out.append("```")
    out.append("")

    out.append("### Current body")
    out.append("```")
    out.append(cur_body or "(empty)")
    out.append("```")
    out.append("")
    out.append("---")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _snapshot() -> int:
    """Run parse_plate on every plate and write a baseline JSON
    (article_id → body).  Overwrites the existing file."""
    sys.stdout.reconfigure(encoding="utf-8")
    s = SessionLocal()
    plates = (
        s.query(Article)
        .filter(Article.article_type == "plate")
        .order_by(Article.volume, Article.id)
        .all()
    )
    snapshot: dict[str, str] = {}
    skipped = 0
    for art in plates:
        seg = (
            s.query(ArticleSegment)
            .filter(ArticleSegment.article_id == art.id)
            .order_by(ArticleSegment.sequence_in_article)
            .first()
        )
        if not seg or not seg.segment_text:
            skipped += 1
            continue
        snapshot[_baseline_key(art)] = parse_plate(seg.segment_text)
    s.close()
    _BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )
    print(f"Wrote {len(snapshot)} plates to {_BASELINE_PATH}"
          + (f" (skipped {skipped} segment-less)" if skipped else ""))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", action="store_true",
                   help="write current parse_plate output to "
                        f"{_BASELINE_PATH} as the new baseline; do not "
                        "produce a comparison report")
    p.add_argument("--out", default="plate_compare.md",
                   help="markdown report path (default plate_compare.md)")
    p.add_argument("--signature",
                   help="only plates matching this exact signature string "
                        "(quote it; obtained from plate_structure_audit.py)")
    p.add_argument("--vol", type=int,
                   help="only plates from this volume number")
    p.add_argument("--title",
                   help="only plates whose title matches this regex")
    p.add_argument("--limit", type=int, default=0,
                   help="cap at first N matching plates (default unlimited)")
    p.add_argument("--source-chars", type=int, default=1500,
                   help="characters of raw source to include per plate "
                        "(default 1500)")
    p.add_argument("--regressions-only", action="store_true",
                   help="only render plates classified regression or mixed")
    p.add_argument("--no-sort", action="store_true",
                   help="keep original (volume, id) order; default sorts "
                        "regressions/mixed first")
    args = p.parse_args()

    if args.snapshot:
        return _snapshot()

    sys.stdout.reconfigure(encoding="utf-8")

    if not _BASELINE_PATH.exists():
        print(
            f"Baseline file not found at {_BASELINE_PATH}.\n"
            "Run with --snapshot first to capture the current parser "
            "output as the reference baseline.",
            file=sys.stderr,
        )
        return 2

    baseline: dict[str, str] = json.loads(
        _BASELINE_PATH.read_text(encoding="utf-8")
    )

    s = SessionLocal()
    q = s.query(Article).filter(Article.article_type == "plate")
    if args.vol:
        q = q.filter(Article.volume == args.vol)
    if args.title:
        title_re = re.compile(args.title)
    else:
        title_re = None
    plates = q.order_by(Article.volume, Article.id).all()

    sig_filter = args.signature.strip() if args.signature else None

    sig_counter: Counter = Counter()
    cat_counter: Counter = Counter()
    skipped = 0
    no_baseline = 0

    # Per-plate records so we can sort, aggregate, then render.
    records: list[dict] = []
    # Per-quality-signal totals (matter/penalty/bookend_clean breakdown).
    totals_base: Counter = Counter()
    totals_cur: Counter = Counter()

    for art in plates:
        if title_re and not title_re.search(art.title):
            continue
        seg = (
            s.query(ArticleSegment)
            .filter(ArticleSegment.article_id == art.id)
            .order_by(ArticleSegment.sequence_in_article)
            .first()
        )
        if not seg or not seg.segment_text:
            skipped += 1
            continue
        raw = seg.segment_text
        fp = fingerprint(raw)
        sig = signature(fp, multipage=False)
        sig_str = " ".join(x for x in sig if x)
        if sig_filter and sig_str != sig_filter:
            continue

        base_body = baseline.get(_baseline_key(art))
        if base_body is None:
            # New plate added since baseline; treat as no regression
            # possible (skip from comparison rather than crash).
            no_baseline += 1
            continue
        cur_body = parse_plate(raw)
        base_stats = stats(base_body)
        cur_stats = stats(cur_body)
        bodies_equal = base_body == cur_body
        category, severity = classify(base_stats, cur_stats, bodies_equal)

        sig_counter[sig_str] += 1
        cat_counter[category] += 1
        for k in ("images", "captioned", "legends", "broken_caps",
                  "header_present", "footer_present",
                  "header_leak", "footer_leak",
                  "header_cap_shape", "footer_cap_shape"):
            totals_base[k] += base_stats[k]
            totals_cur[k] += cur_stats[k]

        records.append({
            "art": art, "raw": raw, "sig": sig,
            "base_body": base_body, "cur_body": cur_body,
            "base_stats": base_stats, "cur_stats": cur_stats,
            "category": category, "severity": severity,
        })

    s.close()

    # Filter and sort.
    if args.regressions_only:
        records = [r for r in records
                   if r["category"] in ("regression", "mixed")]
    if not args.no_sort:
        # Worst first: by VERDICT_ORDER index, then by descending severity.
        records.sort(key=lambda r: (VERDICT_ORDER.index(r["category"]),
                                     -r["severity"]))
        # Apply --limit AFTER sorting so the cap is "top N worst", not
        # "first N by db order".
    if args.limit:
        records = records[:args.limit]

    sections = [
        render_one(r["art"], r["raw"], r["sig"], args.source_chars,
                   r["base_body"], r["cur_body"],
                   r["base_stats"], r["cur_stats"],
                   r["category"], r["severity"])
        for r in records
    ]

    # ---------------------------------------------------------------
    # Header / aggregate report
    # ---------------------------------------------------------------
    header: list[str] = []
    header.append("# Plate parser regression report")
    header.append("")
    header.append(f"- Baseline: `{_BASELINE_PATH}`")
    header.append(f"- Plates rendered: **{len(records)}**")
    if skipped:
        header.append(f"- Plates skipped (no segment): {skipped}")
    if no_baseline:
        header.append(f"- Plates without baseline entry (skipped): {no_baseline}")
    if sig_filter:
        header.append(f"- Signature filter: `{sig_filter}`")
    if args.vol:
        header.append(f"- Volume filter: {args.vol}")
    if args.title:
        header.append(f"- Title regex: `{args.title}`")
    if args.regressions_only:
        header.append("- Filtered to regressions + mixed only")
    header.append("")

    # Verdict breakdown.
    header.append("## Verdict breakdown")
    header.append("")
    header.append("| category | count |")
    header.append("|---|---|")
    for cat in VERDICT_ORDER:
        header.append(f"| {VERDICT_LABEL[cat]} | {cat_counter.get(cat, 0)} |")
    header.append("")

    # Quality signal totals.
    header.append("## Quality signals (totals across all plates)")
    header.append("")
    header.append("| signal | baseline | current | delta |")
    header.append("|---|---|---|---|")
    for k in ("images", "captioned", "legends",
              "broken_caps",
              "header_present", "footer_present",
              "header_leak", "footer_leak",
              "header_cap_shape", "footer_cap_shape"):
        b, c = totals_base[k], totals_cur[k]
        delta = c - b
        sign = "+" if delta > 0 else ""
        header.append(f"| {k} | {b} | {c} | {sign}{delta} |")
    header.append("")

    # Top regressions list (linkable anchors not generated, but titles
    # in this list are easy to grep for in the body).
    regressions = [r for r in records if r["category"] == "regression"]
    if regressions:
        header.append("## Top regressions")
        header.append("")
        header.append("| severity | title | vol |")
        header.append("|---|---|---|")
        for r in sorted(regressions, key=lambda r: -r["severity"])[:20]:
            header.append(
                f"| {r['severity']} | {r['art'].title} | {r['art'].volume} |"
            )
        header.append("")

    header.append("## Signatures in this report")
    header.append("")
    header.append("| count | signature |")
    header.append("|---|---|")
    for sig_str, n in sig_counter.most_common():
        header.append(f"| {n} | `{sig_str}` |")
    header.append("")
    header.append("---")
    header.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(header))
        f.write("\n".join(sections))

    print(f"Wrote {len(records)} plates to {args.out}  "
          f"({dict(cat_counter)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
