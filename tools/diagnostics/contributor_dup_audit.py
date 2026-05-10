"""Audit duplicate Contributor records via combined name+initials signature.

Each contributor record is internally consistent — its name and
initials drift together to whatever transcription style was used in
its source volume.  When the same person appears in two volumes with
slightly different transcriptions, BOTH the name and the initials
drift in the same direction.  So pairwise dedup is best done on a
single combined signature, not as two independent fuzzy axes.

Signature shape:
    normalize(name) + "|" + normalize(sorted initials)

Where normalization:
- strips honorifics ("Rev.", "Prof.", "Sir", ...)
- strips punctuation (periods, commas, apostrophes — curly and
  straight collapse to nothing)
- lowercases
- collapses whitespace

Two records whose signatures are within ~0.92 SequenceMatcher
similarity (a few chars apart) are presumed dupes.  False positives
like ``Lyall`` vs ``Ball`` are rejected because their initials drift
in OPPOSITE directions, so the combined signature similarity falls
below threshold even when the name-only similarity is high.

Article-overlap (Jaccard) is shown alongside as a secondary
confidence signal.

Usage:
    uv run python tools/diagnostics/contributor_dup_audit.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import (  # noqa: E402
    ArticleContributor,
    Contributor,
    ContributorInitials,
)
from britannica.db.session import SessionLocal  # noqa: E402


_TITLE_RE = re.compile(
    r"\b(?:Prof|Professor|Dr|Sir|Lord|Lady|Miss|Mrs|Mr|Rev|Reverend|"
    r"Hon|Honourable|Gen|General|Col|Colonel|Capt|Captain|Maj|Major|"
    r"Lt|Lieutenant|Adml|Admiral)"
    r"\.?\s+",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    s = _TITLE_RE.sub("", name or "")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _normalize_initials_token(initials: str) -> str:
    """Aggressive: lowercase, drop punctuation including curly
    apostrophes, drop spaces.  ``W. Ay.`` and ``W. AY.`` and
    ``W.AY`` all collapse to ``way``."""
    s = re.sub(r"[^\w]", "", initials or "").lower()
    return s


def _signature(name: str, initials_set: set[str]) -> str:
    name_n = _normalize_name(name)
    inits = sorted({
        _normalize_initials_token(i) for i in initials_set
        if _normalize_initials_token(i)
    })
    inits_str = " ".join(inits)
    return f"{name_n}|{inits_str}"


def main() -> int:
    s = SessionLocal()
    try:
        contribs = s.query(Contributor).all()
        # Per-contributor: all initials variants + all article ids.
        cid_to_initials: dict[int, set[str]] = defaultdict(set)
        for ci, contrib in (
            s.query(ContributorInitials, Contributor)
            .join(Contributor,
                  ContributorInitials.contributor_id == Contributor.id)
            .all()
        ):
            cid_to_initials[contrib.id].add(ci.initials)

        cid_to_articles: dict[int, set[int]] = defaultdict(set)
        for cid, aid in s.query(
            ArticleContributor.contributor_id,
            ArticleContributor.article_id,
        ).all():
            cid_to_articles[cid].add(aid)

        # Compute signature per contributor.
        cid_to_sig: dict[int, str] = {}
        for c in contribs:
            cid_to_sig[c.id] = _signature(
                c.full_name, cid_to_initials.get(c.id, set())
            )

        # ----------------------------------------------------------
        # Pairwise compare.  Bucket by first letter of name to keep
        # the comparison set tractable (typo / variant pairs share
        # the first letter in nearly every realistic case).
        # ----------------------------------------------------------
        bucket: dict[str, list[Contributor]] = defaultdict(list)
        for c in contribs:
            sig = cid_to_sig[c.id]
            if sig:
                bucket[sig[0] if sig[0].isalpha() else "_"].append(c)

        threshold = 0.92
        ranked: list[tuple] = []
        for letter, members in bucket.items():
            for i, a in enumerate(members):
                sa = cid_to_sig[a.id]
                for b in members[i + 1:]:
                    sb = cid_to_sig[b.id]
                    sim = SequenceMatcher(None, sa, sb).ratio()
                    if sim < threshold:
                        continue
                    arts_a = cid_to_articles.get(a.id, set())
                    arts_b = cid_to_articles.get(b.id, set())
                    inter = len(arts_a & arts_b)
                    uni = len(arts_a | arts_b)
                    jacc = inter / uni if uni else 0.0
                    ranked.append((sim, jacc, inter, uni, a, b))

        ranked.sort(key=lambda t: (-t[0], -t[1]))

        print(f"Total Contributor records: {len(contribs)}")
        print(f"Candidate dupe pairs (signature sim ≥ {threshold}): "
              f"{len(ranked)}")
        print()

        # Markdown table.
        print(
            "| sim | jacc | shared/union | A — name (id, articles) | "
            "A initials | B — name (id, articles) | B initials |"
        )
        print(
            "|---|---|---|---|---|---|---|"
        )
        for sim, jacc, inter, uni, a, b in ranked:
            ac_a = len(cid_to_articles.get(a.id, set()))
            ac_b = len(cid_to_articles.get(b.id, set()))
            ia = "; ".join(sorted(cid_to_initials.get(a.id, [])))
            ib = "; ".join(sorted(cid_to_initials.get(b.id, [])))
            jacc_str = f"{jacc:.2f}" if uni else "—"
            print(
                f"| {sim:.3f} | {jacc_str} | {inter}/{uni} | "
                f"{a.full_name!r} (id={a.id}, {ac_a}) | "
                f"`{ia}` | "
                f"{b.full_name!r} (id={b.id}, {ac_b}) | "
                f"`{ib}` |"
            )
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
