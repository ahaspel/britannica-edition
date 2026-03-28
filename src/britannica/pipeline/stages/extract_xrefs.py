from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal
from britannica.xrefs.extractor import extract_xrefs


def extract_xrefs_for_volume(volume: int) -> int:
    session = SessionLocal()

    try:
        articles = session.query(Article).filter(Article.volume == volume).all()
        created = 0

        for article in articles:
            matches = extract_xrefs(article.body or "")

            for match in matches:
                existing = (
                    session.query(CrossReference)
                    .filter(
                        CrossReference.article_id == article.id,
                        CrossReference.surface_text == match["surface_text"],
                        CrossReference.normalized_target == match["normalized_target"],
                    )
                    .first()
                )

                if existing:
                    continue

                session.add(
                    CrossReference(
                        article_id=article.id,
                        surface_text=match["surface_text"],
                        normalized_target=match["normalized_target"],
                        xref_type=match["xref_type"],
                        target_article_id=None,
                        status="unresolved",
                    )
                )
                created += 1

        session.commit()
        return created
    finally:
        session.close()