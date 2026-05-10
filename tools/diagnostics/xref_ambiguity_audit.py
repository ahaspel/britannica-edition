"""Audit how many existing cross-references would be reclassified as
ambiguous, and how many of those can be auto-disambiguated by simple
article-level context (Phase 1 of the cascade).

Ambiguous title := exists as a standalone article AND has ≥3
``TITLE, FIRSTNAME`` person-variant articles (Adam Smith, George
Smith, etc.).

For each currently-resolved xref whose normalized target is in the
ambiguous set, look at the source article's body: if exactly one of
the variants is mentioned by full name (``Adam Smith``, etc.), Phase 1
can route the bare-surname xref to that variant.  If multiple variants
mentioned → truly ambiguous within the article.  If none mentioned →
needs Phase 2 (xref-graph) or Phase 3 (LLM).

Usage:
    uv run python tools/diagnostics/xref_ambiguity_audit.py \\
        --out xref_ambiguity.md \\
        --threshold 3
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict

from britannica.db.models import Article, CrossReference  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.xrefs.normalizer import normalize_xref_target  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="xref_ambiguity.md",
                   help="markdown report path")
    p.add_argument("--threshold", type=int, default=3,
                   help="min #person-variants to call a title ambiguous")
    args = p.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    s = SessionLocal()
    try:
        # ----------------------------------------------------------
        # Step 1: build the ambiguous-title set + variant lookup.
        # ----------------------------------------------------------
        articles = s.query(Article).filter(
            Article.article_type == "article"
        ).all()

        norm_titles: set[str] = set()
        # variants[surname] = [list of (full title, article id, first-name string)]
        variants: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        # Map from normalized title to (article id, raw title) for
        # resolution-target lookup.
        title_to_art: dict[str, tuple[int, str]] = {}

        for a in articles:
            n = normalize_xref_target(a.title)
            if not n:
                continue
            norm_titles.add(n)
            title_to_art.setdefault(n, (a.id, a.title))
            if "," in n:
                surname, _, first = n.partition(",")
                surname = surname.strip()
                first = first.strip()
                if surname and first:
                    variants[surname].append((a.title, a.id, first))

        ambiguous: dict[str, list[tuple[str, int, str]]] = {
            surname: vs
            for surname, vs in variants.items()
            if surname in norm_titles and len(vs) >= args.threshold
        }

        print(f"Articles scanned: {len(articles)}")
        print(f"Ambiguous titles (≥{args.threshold} person-variants): {len(ambiguous)}")

        # ----------------------------------------------------------
        # Step 2: count currently-resolved xrefs targeting ambiguous
        # titles.
        # ----------------------------------------------------------
        all_resolved = (
            s.query(CrossReference)
            .filter(CrossReference.status == "resolved")
            .all()
        )
        ambiguous_xrefs = [
            cr for cr in all_resolved
            if cr.normalized_target in ambiguous
        ]
        print(f"Total resolved xrefs: {len(all_resolved)}")
        print(f"  ...targeting an ambiguous title: {len(ambiguous_xrefs)}")

        # ----------------------------------------------------------
        # Step 3: per-target tally + Phase-1 disambiguation check.
        # ----------------------------------------------------------
        per_target: Counter = Counter()
        phase1_one_match: Counter = Counter()
        phase1_multi_match: Counter = Counter()
        phase1_no_match: Counter = Counter()

        # For each ambiguous xref, fetch source article body and check
        # which variants appear.
        article_body_cache: dict[int, str] = {}
        for cr in ambiguous_xrefs:
            target = cr.normalized_target
            per_target[target] += 1

            # Fetch source article body once.
            body = article_body_cache.get(cr.article_id)
            if body is None:
                src = s.query(Article).filter(
                    Article.id == cr.article_id
                ).first()
                body = (src.body or "") if src else ""
                article_body_cache[cr.article_id] = body

            # Look for each variant's first-name in the body.  Match
            # ``FirstName Surname`` (e.g., ``Adam Smith``) — first name
            # may have multiple words ("GEORGE ADAM").  Use case-
            # insensitive boundary match.
            present_variants: list[str] = []
            for full_title, _aid, first in ambiguous[target]:
                # Pattern: FirstName + space + Target (case-insensitive)
                pat = re.compile(
                    r"\b" + re.escape(first) + r"\s+" + re.escape(target) + r"\b",
                    re.IGNORECASE,
                )
                if pat.search(body):
                    present_variants.append(full_title)
            if len(present_variants) == 1:
                phase1_one_match[target] += 1
            elif len(present_variants) >= 2:
                phase1_multi_match[target] += 1
            else:
                phase1_no_match[target] += 1

        # ----------------------------------------------------------
        # Render report.
        # ----------------------------------------------------------
        lines: list[str] = []
        lines.append("# Cross-reference ambiguity audit")
        lines.append("")
        lines.append(f"- Articles scanned: **{len(articles)}**")
        lines.append(f"- Ambiguity threshold: ≥{args.threshold} person-variants")
        lines.append(f"- Ambiguous titles: **{len(ambiguous)}**")
        lines.append(f"- Total resolved xrefs: **{len(all_resolved)}**")
        lines.append(f"- Resolved xrefs targeting an ambiguous title: "
                     f"**{len(ambiguous_xrefs)}** "
                     f"({len(ambiguous_xrefs) / len(all_resolved) * 100:.1f}% of resolved)")
        lines.append("")

        lines.append("## Phase-1 disambiguation outcome")
        lines.append("")
        lines.append("Phase 1 = scan the source article's body for "
                     "``FirstName Surname`` of each variant.")
        lines.append("")
        lines.append("| outcome | xrefs | %% of ambiguous |")
        lines.append("|---|---|---|")
        ones = sum(phase1_one_match.values())
        multis = sum(phase1_multi_match.values())
        zeros = sum(phase1_no_match.values())
        total = ones + multis + zeros
        if total:
            lines.append(f"| **exactly one variant in body → auto-link** | {ones} | {ones/total*100:.1f}% |")
            lines.append(f"| multiple variants in body → still ambiguous | {multis} | {multis/total*100:.1f}% |")
            lines.append(f"| no variant in body → needs Phase 2 / 3 | {zeros} | {zeros/total*100:.1f}% |")
        lines.append("")

        # Top ambiguous targets by xref count
        lines.append("## Top ambiguous targets by xref count")
        lines.append("")
        lines.append("| target | resolved xrefs | variants |")
        lines.append("|---|---|---|")
        for target, n in per_target.most_common(25):
            v = len(ambiguous[target])
            lines.append(f"| {target} | {n} | {v} |")
        lines.append("")

        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Wrote {args.out}")
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
