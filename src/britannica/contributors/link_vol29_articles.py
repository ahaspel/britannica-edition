"""Bind vol 29 master-Index article attributions to contributors.

The vol 29 contributor linker (`link_vol29_contributors.py`) inserts
contributor rows + initials but doesn't create `ArticleContributor`
links — that's normally extract-contributors' job (footer matching)
and link_contributors_from_frontmatter.py's fallback (per-volume
contributor-table subject lists).

Both fall short for vol-29-only contributors: their attributed
articles often have no `(initials)` footer signature, and they don't
appear in any per-volume front matter table.  Without an explicit
binding step, those contributors ship as orphans (no
ArticleContributor rows) and get filtered out of contributors.json
by the export's "contributors with at least one article" rule.

This script consumes `parse_vol29_index()` directly: for each entry
that resolves to a contributor, look up each article in entry.articles
by title and create the binding.

Vol 29 is EB1911's own authoritative record of who wrote what, so we
credit a contributor with EVERY article it lists for them — not just
the ones otherwise orphaned.  A footer signature on two of a
contributor's three articles is no reason to discard the third: the
per-link dedup below (the `existing` check) prevents any double-bind,
so a partial-coverage contributor is *supplemented*, never duplicated.

Run AFTER `extract-contributors` (footer matching) and AFTER
`link_contributors_from_frontmatter.py` (front-matter fallback), so the
footer- and front-matter-derived links already exist and this step adds
only what vol 29 asserts beyond them.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict

from britannica.contributors.resolver import ContributorIndex
from britannica.contributors.vol29_index import Vol29Entry, parse_vol29_index
from britannica.db.models import (
    Article, ArticleContributor, Contributor,
)
from britannica.db.models.contributor import ContributorInitials
from britannica.db.session import SessionLocal


def _normalize_vol29_title(t: str) -> str:
    """Strip vol-29-style parentheticals and uppercase for matching.

    Vol 29 article cells carry editorial qualifiers like
    'Lotze (in part)', '(in collaboration with X)' which aren't part
    of the article title.  The rest of the cell is the title in
    canonical SURNAME-comma-FIRSTNAME form."""
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"\s+", " ", t).strip().rstrip(",.;")
    return t.upper()


def _build_title_map(session) -> dict[str, list[Article]]:
    """Map normalised uppercase title → list of matching articles.

    Multiple articles can share a title across volumes (MAN, BANK,
    etc.); the caller picks the best one (or all of them) per
    attribution."""
    out: dict[str, list[Article]] = {}
    for a in session.query(Article).filter(
            Article.article_type != "plate"):
        key = _normalize_vol29_title(a.title)
        out.setdefault(key, []).append(a)
    return out


def link_vol29_articles(apply_mode: bool = False) -> None:
    session = SessionLocal()
    try:
        entries = parse_vol29_index()
        title_map = _build_title_map(session)
        # Pre-comma-head index over the same titles, for the unique-surname
        # fallback in the loop below: head ("CALVIN") → the articles whose
        # title-head is exactly that ("CALVIN, JOHN").  "CALVINISTIC METHODISTS"
        # indexes under its own head, never under "CALVIN".
        head_index: dict[str, list[Article]] = {}
        for norm_title, arts in title_map.items():
            head_index.setdefault(
                norm_title.split(",", 1)[0].strip(), []).extend(arts)
        # The single contributor resolver
        # ([[project_contributor_resolver_consolidation]]): (name, initials) → id
        # over the whole DB, surname-aware, never guessing.
        inits: dict[int, list[str]] = defaultdict(list)
        for ci in session.query(ContributorInitials).all():
            inits[ci.contributor_id].append(ci.initials)
        idx = ContributorIndex((c.id, c.full_name, inits.get(c.id, []))
                               for c in session.query(Contributor).all())

        created = 0
        bound_contribs: set[int] = set()
        unmatched_titles: list[tuple[str, str]] = []
        no_contributor: list[Vol29Entry] = []

        for entry in entries:
            if not entry.articles:
                continue
            cid = idx.resolve(name=entry.full_name, initials=entry.initials)
            if cid is None:
                no_contributor.append(entry)
                continue
            for article_title in entry.articles:
                key = _normalize_vol29_title(article_title)
                articles = title_map.get(key, [])
                if not articles and "," in key:
                    # A vol-29 cell can qualify a title with a section after a
                    # comma ("BOLIVIA, HISTORY") where the DB carries only the
                    # leading article ("BOLIVIA") as a full title.
                    head_key = key.split(",", 1)[0].strip()
                    articles = title_map.get(head_key, [])
                if not articles:
                    # Final fallback: the head — a bare surname ("CALVIN") or
                    # the pre-comma head ("UNITED STATES" of "United States,
                    # Geology") — matches the title-head of EXACTLY ONE article
                    # ("CALVIN, JOHN", "UNITED STATES, THE").  Exact head, not a
                    # prefix (so "Calvin" never reaches "Calvinistic Methodists");
                    # the uniqueness gate is the safety — a surname shared by 2+
                    # articles stays unmatched, so this adds zero false positives
                    # (simulated: 6 recovered, 0 wrong; ambiguous / garbage heads
                    # skip).
                    head_hits = head_index.get(key.split(",", 1)[0].strip(), [])
                    if len(head_hits) == 1:
                        articles = head_hits
                if not articles:
                    unmatched_titles.append((entry.full_name, article_title))
                    continue
                # Pick the longest-bodied article (the "main" one) when
                # multiple share a title.
                target = max(articles, key=lambda a: len(a.body or ""))
                existing = (session.query(ArticleContributor)
                            .filter(ArticleContributor.article_id == target.id,
                                    ArticleContributor.contributor_id == cid)
                            .first())
                if existing:
                    continue
                if apply_mode:
                    session.add(ArticleContributor(
                        article_id=target.id,
                        contributor_id=cid,
                        sequence=99,
                    ))
                created += 1
                bound_contribs.add(cid)

        if apply_mode:
            session.commit()
        else:
            session.rollback()

        verb = "Created" if apply_mode else "Would create"
        print(f"vol 29 entries: {len(entries)}")
        print(f"  contributors found: {len(entries) - len(no_contributor)}")
        print(f"  contributors not in DB: {len(no_contributor)}")
        print(f"{verb} {created} ArticleContributor rows "
              f"for {len(bound_contribs)} contributors.")
        if not apply_mode:
            print("(dry-run; pass --apply to commit)")
        if unmatched_titles:
            print(f"\nUnmatched article titles ({len(unmatched_titles)}):")
            for name, title in unmatched_titles[:20]:
                print(f"  {name!r}: {title!r}")
            if len(unmatched_titles) > 20:
                print(f"  ... and {len(unmatched_titles) - 20} more")
        if no_contributor:
            print(f"\nVol 29 entries with no DB match ({len(no_contributor)}):")
            for e in no_contributor[:10]:
                print(f"  {e.full_name!r} @ {e.initials!r}")
            if len(no_contributor) > 10:
                print(f"  ... and {len(no_contributor) - 10} more")
    finally:
        session.close()


if __name__ == "__main__":
    link_vol29_articles(apply_mode="--apply" in sys.argv)
