"""Merge duplicate Contributor records identified by combined-signature audit.

Pairs of Contributor records that should be the same person — identified
via the combined name+initials signature audit — are consolidated:

* The "canonical" record (more articles, then longer description, then
  longer name) is kept.
* The "redundant" record's ArticleContributor and ContributorInitials
  rows are reassigned to the canonical, deduping where the canonical
  already has the corresponding link or initials variant.
* The redundant record's description / credentials are merged into the
  canonical record if the canonical has none.
* The redundant Contributor row is deleted.

Conservative-by-default: lists candidates and the proposed merge plan
without writing.  Pass ``--apply`` to actually mutate the database.
Each merge is committed individually so an error in one doesn't roll
back successful merges before it.

Mirrors the ``tools/vol29/disambiguate_toc.py`` pattern: dry-run by
default, ``--apply`` to commit, idempotent (re-running after applies
is a no-op once dupes are gone).

Usage:
    uv run python tools/db/dedup_contributors.py
    uv run python tools/db/dedup_contributors.py --apply
"""
from __future__ import annotations

import argparse
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
    return re.sub(r"[^\w]", "", initials or "").lower()


def _signature(name: str, initials_set: set[str]) -> str:
    name_n = _normalize_name(name)
    inits = sorted({
        _normalize_initials_token(i) for i in initials_set
        if _normalize_initials_token(i)
    })
    return f"{name_n}|{' '.join(inits)}"


def _pick_canonical(
    a_id: int, b_id: int,
    contribs: dict[int, Contributor],
    articles_count: dict[int, int],
) -> tuple[int, int]:
    """Return (canonical_id, redundant_id).

    Priority: more articles → longer description → longer name → lower id.
    """
    a_arts = articles_count.get(a_id, 0)
    b_arts = articles_count.get(b_id, 0)
    if a_arts != b_arts:
        return (a_id, b_id) if a_arts > b_arts else (b_id, a_id)

    a_desc = (contribs[a_id].description or "").strip()
    b_desc = (contribs[b_id].description or "").strip()
    if len(a_desc) != len(b_desc):
        return (a_id, b_id) if len(a_desc) > len(b_desc) else (b_id, a_id)

    a_name_len = len(contribs[a_id].full_name or "")
    b_name_len = len(contribs[b_id].full_name or "")
    if a_name_len != b_name_len:
        return (a_id, b_id) if a_name_len > b_name_len else (b_id, a_id)

    return (a_id, b_id) if a_id < b_id else (b_id, a_id)


def _merge_one(session, canonical_id: int, redundant_id: int) -> dict:
    """Perform a single merge.  Returns a summary dict for logging.

    Caller commits.  Strategy:
    1. Reassign or dedupe ArticleContributor rows (B → A).  When B and
       A both have a row for the same article, B's row is deleted —
       no duplicate (article_id, contributor_id) pairs.
    2. Migrate ContributorInitials rows (B → A).  ContributorInitials
       has a UNIQUE constraint on ``initials``, so for any value B
       holds that A doesn't, reassign; for values both hold, delete B's.
    3. Promote B's description / credentials onto A only if A's slot is
       empty.
    4. Delete B's Contributor row.
    """
    summary = {
        "canonical_id": canonical_id,
        "redundant_id": redundant_id,
        "articles_reassigned": 0,
        "articles_deduped": 0,
        "initials_reassigned": 0,
        "initials_deduped": 0,
        "description_promoted": False,
        "credentials_promoted": False,
    }

    # 1. ArticleContributor: which articles does canonical already cover?
    canon_articles = {
        ac.article_id
        for ac in session.query(ArticleContributor)
        .filter(ArticleContributor.contributor_id == canonical_id)
        .all()
    }
    for ac in (
        session.query(ArticleContributor)
        .filter(ArticleContributor.contributor_id == redundant_id)
        .all()
    ):
        if ac.article_id in canon_articles:
            session.delete(ac)
            summary["articles_deduped"] += 1
        else:
            ac.contributor_id = canonical_id
            summary["articles_reassigned"] += 1

    # 2. ContributorInitials: unique-constraint on initials.
    canon_inits = {
        ci.initials
        for ci in session.query(ContributorInitials)
        .filter(ContributorInitials.contributor_id == canonical_id)
        .all()
    }
    for ci in (
        session.query(ContributorInitials)
        .filter(ContributorInitials.contributor_id == redundant_id)
        .all()
    ):
        if ci.initials in canon_inits:
            session.delete(ci)
            summary["initials_deduped"] += 1
        else:
            ci.contributor_id = canonical_id
            summary["initials_reassigned"] += 1

    # 3. Promote description / credentials if canonical's slot is empty.
    canon = session.get(Contributor, canonical_id)
    redundant = session.get(Contributor, redundant_id)
    if not (canon.description or "").strip() and (redundant.description or "").strip():
        canon.description = redundant.description
        summary["description_promoted"] = True
    if not (canon.credentials or "").strip() and (redundant.credentials or "").strip():
        canon.credentials = redundant.credentials
        summary["credentials_promoted"] = True

    # 4. Delete redundant Contributor row.
    session.delete(redundant)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually perform the merges (default: dry-run)")
    ap.add_argument("--threshold", type=float, default=0.92,
                    help="signature-similarity threshold for dupe "
                         "candidates (default 0.92)")
    args = ap.parse_args()

    s = SessionLocal()
    try:
        contribs_list = s.query(Contributor).all()
        contribs: dict[int, Contributor] = {c.id: c for c in contribs_list}

        # Per-contributor: initials variants and article counts.
        cid_to_initials: dict[int, set[str]] = defaultdict(set)
        for ci in s.query(ContributorInitials).all():
            cid_to_initials[ci.contributor_id].add(ci.initials)

        articles_count: dict[int, int] = defaultdict(int)
        for cid, _ in s.query(
            ArticleContributor.contributor_id,
            ArticleContributor.article_id,
        ).all():
            articles_count[cid] += 1

        # Compute signature per contributor; bucket by first letter.
        cid_to_sig: dict[int, str] = {
            c.id: _signature(c.full_name, cid_to_initials.get(c.id, set()))
            for c in contribs_list
        }
        bucket: dict[str, list[Contributor]] = defaultdict(list)
        for c in contribs_list:
            sig = cid_to_sig[c.id]
            if sig:
                bucket[sig[0] if sig[0].isalpha() else "_"].append(c)

        # Pairwise compare within each bucket.
        pairs: list[tuple[float, int, int]] = []
        for letter, members in bucket.items():
            for i, a in enumerate(members):
                sa = cid_to_sig[a.id]
                for b in members[i + 1:]:
                    sb = cid_to_sig[b.id]
                    sim = SequenceMatcher(None, sa, sb).ratio()
                    if sim >= args.threshold:
                        pairs.append((sim, a.id, b.id))
        pairs.sort(key=lambda t: -t[0])

        print(f"Total contributors: {len(contribs_list)}")
        print(f"Candidate dupe pairs (sim ≥ {args.threshold}): {len(pairs)}")
        print()

        if not pairs:
            print("Nothing to dedup.")
            return 0

        # Plan and execute (dry-run unless --apply).
        for sim, a_id, b_id in pairs:
            if a_id not in contribs or b_id not in contribs:
                # Already merged this run — skip (chained dupes).
                continue
            canon_id, redundant_id = _pick_canonical(
                a_id, b_id, contribs, articles_count
            )
            canon = contribs[canon_id]
            redundant = contribs[redundant_id]
            print(
                f"sim={sim:.3f}  canonical: {canon.full_name!r} "
                f"(id={canon_id}, {articles_count[canon_id]} articles)"
            )
            print(
                f"             redundant: {redundant.full_name!r} "
                f"(id={redundant_id}, {articles_count[redundant_id]} articles)"
            )
            if args.apply:
                summary = _merge_one(s, canon_id, redundant_id)
                s.commit()
                # Update local state so a later pair referencing
                # ``redundant_id`` skips cleanly (chained dupes).
                del contribs[redundant_id]
                articles_count[canon_id] += articles_count.pop(redundant_id, 0)
                print(
                    f"             merged: "
                    f"+{summary['articles_reassigned']} articles, "
                    f"+{summary['initials_reassigned']} initials, "
                    f"-{summary['articles_deduped']} dup-articles, "
                    f"-{summary['initials_deduped']} dup-initials"
                    + (", desc promoted" if summary["description_promoted"] else "")
                    + (", cred promoted" if summary["credentials_promoted"] else "")
                )
            print()

        if not args.apply:
            print("[dry-run]  Pass --apply to commit these merges.")
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
