"""Audit untapped cross-reference coverage.

Walks every article body looking for "see X" / "cf. X" / "vide X" /
"see article X" patterns that the extractor currently doesn't catch.
For each candidate, checks whether the target matches an existing
article title (via the same normalization the resolver uses).  The
match-rate per pattern tells us whether expanding the extractor to
cover that shape is worth the work or just produces noise.

Filters out candidates that fall inside an existing ``«LN:…»`` link
marker — those are already linked, just rendered with the surface
text.

Output: ``xref_coverage.md`` with per-pattern tally + sample matches.

Usage:
    uv run python tools/diagnostics/xref_coverage_audit.py \\
        --out xref_coverage.md
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict

from britannica.db.models import Article  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.xrefs.normalizer import normalize_xref_target  # noqa: E402


# Existing link markers in body text.  Candidates inside these spans
# are already linked and shouldn't count as missed coverage.
_LN_RE = re.compile(r"«LN:[^«]*«/LN»")

# A loose target shape: starts with an uppercase letter, can contain
# letters/digits/spaces/apostrophes/hyphens/commas, ends at a
# sentence-terminator or paren-close.  Bounded by reasonable length
# so we don't grab whole paragraphs.
_TARGET_TAIL = r"([A-Z][A-Za-z][A-Za-z0-9 ,'.\-]{2,80}?)(?=[,;.)”’\"\']|\s+(?:and|or|in|of|on|by|at|to|from|with|for)\b|$|\n)"

# Candidate patterns the current extractor doesn't handle (or handles
# only in a strict form).  Each (label, regex) pair is scanned over
# every article body.
_PATTERNS = [
    ("see X (lowercase 'see', mixed-case target)",
     re.compile(r"\bsee\s+" + _TARGET_TAIL)),
    ("See X (mixed-case target)",
     re.compile(r"\bSee\s+" + _TARGET_TAIL)),
    ("see article X",
     re.compile(r"\bsee\s+(?:the\s+)?article\s+(?:on\s+)?" + _TARGET_TAIL)),
    ("See also X (mixed-case)",
     re.compile(r"\bSee\s+also\s+" + _TARGET_TAIL)),
    ("cf. X",
     re.compile(r"\b[Cc]f\.\s+" + _TARGET_TAIL)),
    ("vide X",
     re.compile(r"\bvide\s+" + _TARGET_TAIL)),
    ("v. X (Latin abbreviation)",
     re.compile(r"\bv\.\s+" + _TARGET_TAIL)),
    ("compare X",
     re.compile(r"\b[Cc]ompare\s+" + _TARGET_TAIL)),
]


def _ln_spans(body: str) -> list[tuple[int, int]]:
    """Source positions of existing link markers — exclude from
    candidate scanning."""
    return [(m.start(), m.end()) for m in _LN_RE.finditer(body)]


def _in_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in spans)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="xref_coverage.md",
                   help="markdown report path")
    p.add_argument("--examples-per-pattern", type=int, default=15,
                   help="how many sample matches per pattern")
    args = p.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    s = SessionLocal()
    try:
        articles = s.query(Article).all()
        # Build the set of normalized article titles.  Exclude plate /
        # subarticle / front-matter shapes — those aren't typical
        # cross-reference targets.
        titles_norm: set[str] = set()
        title_to_article: dict[str, str] = {}
        for a in articles:
            if a.article_type in ("plate",):
                continue
            n = normalize_xref_target(a.title)
            if n:
                titles_norm.add(n)
                title_to_article.setdefault(n, a.title)
        print(f"Loaded {len(articles)} articles, "
              f"{len(titles_norm)} normalized titles for matching")

        per_pattern_total: Counter = Counter()
        per_pattern_matched: Counter = Counter()
        per_pattern_examples: dict[str, list[str]] = defaultdict(list)

        for art in articles:
            body = art.body or ""
            if not body:
                continue
            ln_spans = _ln_spans(body)

            for label, pat in _PATTERNS:
                for m in pat.finditer(body):
                    if _in_span(m.start(), ln_spans):
                        continue
                    target = m.group(1).strip().rstrip(",.;:")
                    norm = normalize_xref_target(target)
                    if not norm:
                        continue
                    per_pattern_total[label] += 1
                    matched = norm in titles_norm
                    if matched:
                        per_pattern_matched[label] += 1
                        if len(per_pattern_examples[label]) < args.examples_per_pattern:
                            per_pattern_examples[label].append(
                                f"vol {art.volume:2d} {art.title!r} → "
                                f"{m.group(0)!r} → matches {title_to_article[norm]!r}"
                            )
    finally:
        s.close()

    # Render report.
    lines: list[str] = []
    lines.append("# Cross-reference coverage audit")
    lines.append("")
    lines.append(f"- Articles scanned: **{len(articles)}**")
    lines.append(f"- Normalized titles: **{len(titles_norm)}**")
    lines.append("")
    lines.append("## Pattern hit-rates")
    lines.append("")
    lines.append("| pattern | candidates | resolvable | match rate |")
    lines.append("|---|---|---|---|")
    for label, _ in _PATTERNS:
        total = per_pattern_total.get(label, 0)
        matched = per_pattern_matched.get(label, 0)
        rate = f"{matched / total * 100:.1f}%" if total else "—"
        lines.append(f"| {label} | {total} | {matched} | {rate} |")
    lines.append("")
    lines.append(
        "*Resolvable* = candidate's target normalizes to an existing "
        "article title.  Higher match rate → expanding the extractor "
        "to cover this shape produces real links rather than noise."
    )
    lines.append("")

    for label, _ in _PATTERNS:
        examples = per_pattern_examples.get(label, [])
        if not examples:
            continue
        lines.append(f"## Examples — {label}")
        lines.append("")
        for ex in examples:
            lines.append(f"- {ex}")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
