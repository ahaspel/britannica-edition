from collections import defaultdict

from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal
from britannica.xrefs.alias_table import (
    build_alias_map,
    build_section_alias_map,
    build_vol29_index_aliases,
)
from britannica.xrefs.resolver import (
    disambiguate_among, resolve_xref_exact, resolve_xref_fuzzy,
)


def resolve_xrefs_for_volume(volume: int) -> int:
    session = SessionLocal()

    try:
        articles = session.query(Article).filter(Article.volume == volume).all()
        xrefs = (
            session.query(CrossReference)
            .join(Article, CrossReference.article_id == Article.id)
            .filter(Article.volume == volume)
            .all()
        )

        resolved = 0

        for xref in xrefs:
            if xref.target_article_id is not None and xref.status == "resolved":
                continue

            target_article_id = resolve_xref_exact(xref, articles)

            if target_article_id is not None:
                xref.target_article_id = target_article_id
                xref.status = "resolved"
                resolved += 1
            else:
                xref.target_article_id = None
                xref.status = "unresolved"

        session.commit()
        return resolved

    finally:
        session.close()


def resolve_xrefs_all() -> int:
    """Resolve all unresolved xrefs against articles from any volume.

    Uses a unified lookup: canonical titles + aliases + fuzzy matching.
    Colliding titles (e.g. ZÜRICH canton vs city) are routed through
    the collision-aware `disambiguate_among` in the resolver module —
    the same code path the intra-volume pass uses — so self-references
    get filtered and display-disambiguator hints get honored.
    """
    session = SessionLocal()

    try:
        all_articles = session.query(Article).all()

        # Collision-aware canonical map: title (UPPER) → list[Article].
        # 580 titles in the corpus are shared by 2+ articles (ABBAS I,
        # ABDERA, ABERDEEN, ZÜRICH, …); the legacy single-value dict
        # silently dropped all but one candidate.
        title_to_articles: dict[str, list[Article]] = defaultdict(list)
        for a in all_articles:
            if a.article_type == "plate":
                continue
            key = (a.title or "").strip().upper()
            if key:
                title_to_articles[key].append(a)

        # Aliases: same guard as before — don't overwrite canonical
        # titles.  When the canonical has collisions, the alias
        # inherits the full candidate list so disambiguation applies
        # uniformly.
        alias_map = build_alias_map()
        for alias, canonical in alias_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]

        section_map = build_section_alias_map()
        section_lookup: dict[str, str] = {}
        for alias, canonical in section_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]
                section_lookup[alias] = alias

        vol29_map = build_vol29_index_aliases()
        for alias, canonical in vol29_map.items():
            if alias not in title_to_articles and canonical in title_to_articles:
                title_to_articles[alias] = title_to_articles[canonical]

        # Fuzzy matching still needs a plain title→id map.  Include
        # all titles (picking the first candidate for collisions) so
        # fuzzy retains the coverage it had before collision-aware
        # lookup landed — fuzzy has no xref-side signal to disambiguate,
        # and the first-wins fallback matches what disambiguate_among
        # does when no rule fires.
        title_map: dict[str, int] = {
            k: v[0].id
            for k, v in title_to_articles.items()
        }

        unresolved = (
            session.query(CrossReference)
            .filter(CrossReference.status == "unresolved")
            .all()
        )

        resolved = 0

        for xref in unresolved:
            target = xref.normalized_target.strip().upper()
            target_article_id: int | None = None
            section: str | None = None

            # 1. Exact title / alias / section-alias (collision-aware)
            candidates = title_to_articles.get(target)
            if candidates:
                target_article_id = disambiguate_among(xref, candidates)
                if target in section_lookup:
                    section = section_lookup[target]

            # 2. Section-suffix form: "EUROPE: HISTORY" -> (EUROPE, HISTORY)
            if target_article_id is None and ": " in target:
                base, _, suffix = target.rpartition(": ")
                base = base.strip()
                suffix = suffix.strip()
                base_candidates = title_to_articles.get(base)
                if base_candidates and suffix:
                    target_article_id = disambiguate_among(
                        xref, base_candidates
                    )
                    section = suffix

            # 3. Fuzzy matching (plurals, name inversion, section-strip, etc.)
            if target_article_id is None:
                target_article_id = resolve_xref_fuzzy(xref, title_map)

            if target_article_id is not None:
                xref.target_article_id = target_article_id
                xref.target_section = section
                xref.status = "resolved"
                resolved += 1

        session.commit()
        return resolved

    finally:
        session.close()