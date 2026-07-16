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
import unicodedata

from britannica.contributors.vol29_index import Vol29Entry, parse_vol29_index
from britannica.db.models import (
    Article, ArticleContributor, Contributor,
)
from britannica.db.models.contributor import ContributorInitials
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.extract_contributors import _normalize_initials


def _name_tokens(name: str) -> frozenset[str]:
    """Lowercased ASCII tokens from a name, dropping honorifics that
    vol 29 keeps but per-volume tables drop (or vice versa).  Unicode
    is folded to ASCII so 'François' matches 'Francois' (vol 29's OCR
    drops the cedilla)."""
    drop = {"prof", "rev", "sir", "lord", "mrs", "dr", "hon",
            "rt", "very", "right", "ven", "bart", "jr", "sr",
            "captain", "col", "colonel", "major", "lt", "lieut",
            "general", "admiral", "baron", "viscount"}
    folded = unicodedata.normalize("NFKD", name)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    toks = re.findall(r"[A-Za-z]+", folded.lower())
    return frozenset(t for t in toks if t not in drop and len(t) > 1)


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


def _find_contributor(
    session, entry: Vol29Entry,
    by_initials: dict[str, list[Contributor]],
    all_contribs: list[Contributor],
) -> Contributor | None:
    """Resolve a vol 29 entry to a Contributor row.

    Order of preference:
      1. Exact initials match — the strongest signal. Babelon lives at
         `E. B.*` in DB and vol 29; that match holds even when name
         spellings disagree (`Edmond` vs `Edward`, abbreviated middle
         names, etc.) — SO LONG AS the names still share a token.  When
         the sole initials-owner's name shares ZERO tokens with the
         entry, the initials are corrupt: vol 29's OCR dropped a
         distinguishing mark (Bell's `L. Bl.` read as `L. Be.`; a lost
         `*` on `V. C.*` / `J. T. M.*`), colliding the entry onto the
         wrong neighbour (Bénédite, Chirol, Milton).  We don't trust
         that — we fall through to name resolution, which finds the true
         owner under their own correct key.
      2. Name-token equality (Unicode-folded so `François` matches
         `Francois`) — catches contributors who share initials with
         someone else (rare) or whose initials drifted between vol 29
         and per-volume tables.
      3. Name-token subset match (either direction) — catches `Prof.
         James George Frazer` ↔ `James George Frazer`.

    Returns None if no resolution is unambiguous.
    """
    init_key = _normalize_initials(entry.initials)
    candidates_by_init = by_initials.get(init_key, [])
    target = _name_tokens(entry.full_name)

    def _by_name():
        """The unique corpus contributor whose name-tokens match the entry
        (exact, else subset either direction), or None if not unambiguous."""
        if not target:
            return None
        exact = [c for c in all_contribs if _name_tokens(c.full_name) == target]
        if len(exact) == 1:
            return exact[0]
        if not exact:
            subsets = [
                c for c in all_contribs
                if _name_tokens(c.full_name) and
                (target.issubset(_name_tokens(c.full_name))
                 or _name_tokens(c.full_name).issubset(target))
            ]
            if len(subsets) == 1:
                return subsets[0]
        return None

    if candidates_by_init:
        if len(candidates_by_init) == 1:
            cand = candidates_by_init[0]
            if not target or (_name_tokens(cand.full_name) & target):
                return cand
            # Names share zero tokens — vol 29's OCR likely dropped a
            # distinguishing mark (Bell `L. Bl.`→`L. Be.`, a lost `*` on
            # `V. C.*` / `J. T. M.*`), colliding this entry onto the wrong
            # neighbour.  Prefer a distinct contributor the ENTRY's name
            # resolves to; if it resolves nowhere else this is mere spelling
            # drift (McNaught/M'Naught) — keep the initials owner.
            named = _by_name()
            return named if named is not None else cand
        # Multiple contributors at this initials key — pick the name match.
        if target:
            name_match = [c for c in candidates_by_init
                          if _name_tokens(c.full_name) == target]
            if len(name_match) == 1:
                return name_match[0]
            subset_match = [
                c for c in candidates_by_init
                if _name_tokens(c.full_name) and
                (target.issubset(_name_tokens(c.full_name))
                 or _name_tokens(c.full_name).issubset(target))
            ]
            if len(subset_match) == 1:
                return subset_match[0]
        return None
    # No initials match — fall back to name match across the corpus.
    return _by_name()


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
        # Pre-build a (initials → list[Contributor]) lookup so the
        # per-entry resolver doesn't re-scan the table 1457 times.
        all_contribs = session.query(Contributor).all()
        by_id = {c.id: c for c in all_contribs}
        by_initials: dict[str, list[Contributor]] = {}
        for ci in session.query(ContributorInitials).all():
            c = by_id.get(ci.contributor_id)
            if c is not None:
                by_initials.setdefault(_normalize_initials(ci.initials),
                                       []).append(c)

        created = 0
        bound_contribs: set[int] = set()
        unmatched_titles: list[tuple[str, str]] = []
        no_contributor: list[Vol29Entry] = []

        for entry in entries:
            if not entry.articles:
                continue
            c = _find_contributor(session, entry, by_initials, all_contribs)
            if c is None:
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
                                    ArticleContributor.contributor_id == c.id)
                            .first())
                if existing:
                    continue
                if apply_mode:
                    session.add(ArticleContributor(
                        article_id=target.id,
                        contributor_id=c.id,
                        sequence=99,
                    ))
                created += 1
                bound_contribs.add(c.id)

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
