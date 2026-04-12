from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal
from britannica.xrefs.alias_table import (
    build_alias_map,
    build_section_alias_map,
    build_vol29_index_aliases,
)
from britannica.xrefs.resolver import resolve_xref_exact, resolve_xref_fuzzy


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
    """
    session = SessionLocal()

    try:
        all_articles = session.query(Article).all()
        # Build unified lookup: title -> article_id (exclude plates —
        # xrefs should always target the article, not a plate page)
        title_map = {a.title.strip().upper(): a.id
                     for a in all_articles if a.article_type != "plate"}

        # Add aliases to the lookup (don't overwrite canonical titles)
        alias_map = build_alias_map()
        for alias, canonical in alias_map.items():
            if alias not in title_map and canonical in title_map:
                title_map[alias] = title_map[canonical]

        # Section aliases: <section begin="Clement I"/> inside
        # CLEMENT (POPES) makes "CLEMENT I" resolve to that article
        # AND records the section name for the viewer to turn into a
        # #section-<slug> URL fragment.
        section_map = build_section_alias_map()
        section_lookup: dict[str, tuple[int, str]] = {}
        for alias, canonical in section_map.items():
            if alias not in title_map and canonical in title_map:
                title_map[alias] = title_map[canonical]
                section_lookup[alias] = (title_map[canonical], alias)

        # Vol 29 (Index volume) aliases: PENINSULAR WAR -> NAPOLEONIC
        # CAMPAIGNS etc., harvested from the transcribed index entries.
        vol29_map = build_vol29_index_aliases()
        for alias, canonical in vol29_map.items():
            if alias not in title_map and canonical in title_map:
                title_map[alias] = title_map[canonical]

        # Section-suffix targets (e.g. "EUROPE: HISTORY"): resolve to
        # EUROPE with section = "HISTORY".
        suffix_section_lookup: dict[str, tuple[int, str]] = {}
        for target_upper, article_id in title_map.items():
            # Skip — the whole map iteration would be O(N²); do it
            # inline during xref resolution instead.
            break

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

            # 1. Exact title / alias / section-alias
            target_article_id = title_map.get(target)
            if target_article_id is not None and target in section_lookup:
                section = section_lookup[target][1]

            # 2. Section-suffix form: "EUROPE: HISTORY" -> (EUROPE, HISTORY)
            if target_article_id is None and ": " in target:
                base, _, suffix = target.rpartition(": ")
                base = base.strip()
                suffix = suffix.strip()
                if base in title_map and suffix:
                    target_article_id = title_map[base]
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