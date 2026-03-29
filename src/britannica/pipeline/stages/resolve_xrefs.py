from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal
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

    Tries exact match first, then fuzzy matching (plural/singular, name inversion).
    """
    session = SessionLocal()

    try:
        all_articles = session.query(Article).all()
        title_map = {a.title.strip().upper(): a.id for a in all_articles}

        unresolved = (
            session.query(CrossReference)
            .filter(CrossReference.status == "unresolved")
            .all()
        )

        resolved = 0

        for xref in unresolved:
            # Try exact match first
            target_article_id = resolve_xref_exact(xref, all_articles)

            # Fall back to fuzzy matching
            if target_article_id is None:
                target_article_id = resolve_xref_fuzzy(xref, title_map)

            if target_article_id is not None:
                xref.target_article_id = target_article_id
                xref.status = "resolved"
                resolved += 1

        session.commit()
        return resolved

    finally:
        session.close()