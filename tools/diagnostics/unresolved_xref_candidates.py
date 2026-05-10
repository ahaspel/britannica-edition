"""Audit candidate-generation for unresolved cross-references.

For each xref with ``status='unresolved'``, generate a ranked list of
plausible candidate articles by combining word-overlap match with
fuzzy string distance.  This is the candidate set that would be fed
to the LLM for final selection.

Two outputs:

1. ``unresolved_candidates.md`` — header stats + top-N examples per
   bucket (no candidates / 1 candidate / 2-5 / 6+).
2. ``unresolved_candidates.json`` — full per-xref candidate list,
   ready to be consumed by the LLM-resolver script.

Tells us:
- How many unresolveds have *any* plausible candidate (LLM-resolvable
  ceiling).
- Per-bucket distribution → cost estimate for LLM stage.
- Whether candidate sets are sharp enough that even a cheap model
  will work, or noisy enough that we need more reasoning.

Usage:
  uv run python tools/diagnostics/unresolved_xref_candidates.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher

from britannica.db.models import Article, CrossReference  # noqa: E402
from britannica.db.session import SessionLocal  # noqa: E402
from britannica.export.article_json import stable_id  # noqa: E402
from britannica.xrefs.normalizer import normalize_xref_target  # noqa: E402


_STOPWORDS = frozenset({
    "the", "of", "a", "an", "and", "or", "in", "on", "by", "to",
    "for", "from", "with", "as", "at", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "see",
    "also", "cf", "vide", "v", "compare", "article", "articles",
})

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
_TOP_CANDIDATES = 15


def _tokens(text: str) -> list[str]:
    """Lowercase word tokens, stopwords removed, length>=2."""
    return [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if t.lower() not in _STOPWORDS and len(t) >= 2
    ]


def _build_title_index(articles: list[Article]) -> tuple[
    dict[str, set[int]], list[Article], dict[str, float]
]:
    """Return (token → article-id-set inverted index, valid articles,
    token → IDF map).

    IDF (inverse document frequency) measures token rarity: tokens
    that appear in many titles carry less signal than tokens unique
    to a few articles.  Without IDF weighting, ``BIBLE (KING JAMES)/
    EXODUS: 4:27`` lights up every James-name article (via the
    common ``James`` token) and out-scores the actual answer (the
    EXODUS article, which only shares the rare ``exodus`` token).
    """
    import math
    word_to_articles: dict[str, set[int]] = defaultdict(set)
    valid: list[Article] = []
    for a in articles:
        if a.article_type == "plate":
            continue
        title = a.title or ""
        if not title:
            continue
        valid.append(a)
        for tok in _tokens(title):
            word_to_articles[tok].add(a.id)
    n = max(1, len(valid))
    idf = {
        tok: math.log(n / max(1, len(article_ids)))
        for tok, article_ids in word_to_articles.items()
    }
    return word_to_articles, valid, idf


def _score_candidate(
    target: str, surface: str, title: str, idf: dict[str, float]
) -> float:
    """IDF-weighted token overlap, plus substring-of-target bonus,
    plus character fuzzy.

    Returns a normalized 0..1 score where 1 is a perfect match.
    """
    target_text = f"{target} {surface}"
    t_words = set(_tokens(target_text))
    c_words = set(_tokens(title))

    # IDF-weighted Jaccard: shared tokens weighted by their rarity.
    if t_words and c_words:
        shared = t_words & c_words
        union = t_words | c_words
        shared_mass = sum(idf.get(w, 0.0) for w in shared)
        union_mass = sum(idf.get(w, 0.0) for w in union)
        weighted_jaccard = (
            shared_mass / union_mass if union_mass else 0.0
        )
    else:
        weighted_jaccard = 0.0

    # Substring bonus: title (or its main token) appearing in the
    # target text as a literal substring is a strong signal.
    # ``EXODUS`` is in ``"BIBLE (KING JAMES)/EXODUS: 4:27"``;
    # ``STIRLING`` is not.
    target_upper = target_text.upper()
    title_upper = title.upper()
    substring_bonus = 0.0
    if title_upper and title_upper in target_upper:
        substring_bonus = 0.5  # whole title appears in target
    else:
        # Most-significant title token (highest IDF) — does *it*
        # appear in target?  Catches "EXODUS, BOOK OF" → "EXODUS"
        # signal in target text.
        title_toks = _tokens(title)
        if title_toks:
            best_tok = max(title_toks, key=lambda t: idf.get(t, 0.0))
            if best_tok.upper() in target_upper:
                # Bonus proportional to that token's IDF — rare-token
                # substring is a stronger signal than common-token.
                # Normalize by max IDF in the corpus to land in 0..1.
                max_idf = max(idf.values()) if idf else 1.0
                substring_bonus = (
                    0.5 * idf.get(best_tok, 0.0) / max_idf
                )

    # Character fuzzy as a fallback signal — handles typos that
    # break token matching.
    fuzzy = SequenceMatcher(None, target.upper(), title_upper).ratio()

    return min(1.0, weighted_jaccard + substring_bonus + 0.2 * fuzzy)


def _candidates_for(
    target: str,
    surface: str,
    source_article_id: int | None,
    word_to_articles: dict[str, set[int]],
    article_by_id: dict[int, Article],
    idf: dict[str, float],
    top_n: int = _TOP_CANDIDATES,
) -> list[tuple[Article, float]]:
    """Top-N candidate articles for an unresolved target.

    Excludes the source article itself — a reference inside an
    article should never link back to that same article (would
    produce a self-loop link).  Account of Egypt (Abdallatif) in the
    ABDALLATIF article resolved to ABDALLATIF before this filter.
    """
    seed_ids: set[int] = set()
    for tok in _tokens(f"{target} {surface}"):
        seed_ids |= word_to_articles.get(tok, set())
    if source_article_id is not None:
        seed_ids.discard(source_article_id)

    scored: list[tuple[Article, float]] = []
    for aid in seed_ids:
        a = article_by_id.get(aid)
        if a is None:
            continue
        score = _score_candidate(target, surface, a.title or "", idf)
        if score > 0.15:  # noise floor — slightly relaxed for the
            scored.append((a, score))    # IDF-weighted regime
    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-md", default="unresolved_candidates.md")
    p.add_argument("--out-json", default="unresolved_candidates.json")
    p.add_argument("--limit", type=int, default=0,
                   help="cap at first N unresolved (default unlimited)")
    p.add_argument("--examples-per-bucket", type=int, default=15)
    args = p.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    s = SessionLocal()
    try:
        all_articles = s.query(Article).all()
        word_to_articles, valid, idf = _build_title_index(all_articles)
        article_by_id = {a.id: a for a in valid}
        print(f"Article corpus: {len(valid)}")
        print(f"Token index: {len(word_to_articles)} unique words")

        unresolved = (
            s.query(CrossReference)
            .filter(CrossReference.status == "unresolved")
            .all()
        )
        if args.limit:
            unresolved = unresolved[:args.limit]
        print(f"Unresolved xrefs: {len(unresolved)}")

        # Walk each unresolved xref and build candidate sets.
        records: list[dict] = []
        bucket_counts: Counter = Counter()
        for cr in unresolved:
            cands = _candidates_for(
                cr.normalized_target, cr.surface_text,
                cr.article_id,
                word_to_articles, article_by_id, idf,
            )
            n_cand = len(cands)
            if n_cand == 0:
                bucket = "0_none"
            elif n_cand == 1:
                bucket = "1_single"
            elif n_cand <= 5:
                bucket = "2-5_few"
            else:
                bucket = "6+_many"
            bucket_counts[bucket] += 1

            src = article_by_id.get(cr.article_id)
            records.append({
                "xref_id": cr.id,
                "source_stable_id": stable_id(src) if src else None,
                "source_title": src.title if src else None,
                "surface_text": cr.surface_text,
                "normalized_target": cr.normalized_target,
                "xref_type": cr.xref_type,
                "candidates": [
                    {
                        "stable_id": stable_id(a),
                        "title": a.title,
                        "score": round(score, 3),
                    }
                    for a, score in cands
                ],
                "bucket": bucket,
            })
    finally:
        s.close()

    # JSON output (full per-xref data).
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Markdown summary.
    lines: list[str] = []
    lines.append("# Unresolved xref candidate-generation audit")
    lines.append("")
    lines.append(f"- Unresolved xrefs scanned: **{len(records)}**")
    lines.append("")
    lines.append("## Candidate-set distribution")
    lines.append("")
    lines.append("| bucket | count | %% |")
    lines.append("|---|---|---|")
    for bucket in ("0_none", "1_single", "2-5_few", "6+_many"):
        n = bucket_counts.get(bucket, 0)
        pct = n / len(records) * 100 if records else 0
        lines.append(f"| {bucket} | {n} | {pct:.1f}% |")
    lines.append("")
    lines.append(
        "*0_none* = no candidate scored above noise floor → likely a "
        "genuine miss (article doesn't exist in EB1911) or pure "
        "typographical garbage.  *1_single* = single high-confidence "
        "match → could be auto-linked without LLM.  *2-5_few* and "
        "*6+_many* = LLM disambiguates.")
    lines.append("")

    # Examples per bucket.
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_bucket[r["bucket"]].append(r)
    for bucket in ("1_single", "2-5_few", "6+_many", "0_none"):
        examples = by_bucket.get(bucket, [])[:args.examples_per_bucket]
        if not examples:
            continue
        lines.append(f"## Examples — {bucket}")
        lines.append("")
        for r in examples:
            lines.append(f"- **target:** `{r['normalized_target']}` "
                         f"(surface: `{r['surface_text'][:60]}`)  ")
            lines.append(f"  source: {r['source_title']!r} "
                         f"({r['source_stable_id']})")
            if r["candidates"]:
                lines.append("  candidates:")
                for c in r["candidates"][:5]:
                    lines.append(f"    - {c['score']:.2f}  {c['title']!r} "
                                 f"({c['stable_id']})")
            lines.append("")
        lines.append("")

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {args.out_md} and {args.out_json}")
    print(f"Bucket distribution: {dict(bucket_counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
