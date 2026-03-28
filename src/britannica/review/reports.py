from collections import defaultdict

from britannica.db.models import Article, CrossReference
from britannica.db.session import SessionLocal


def get_unresolved_xrefs_report(volume: int) -> dict[str, list[CrossReference]]:
    session = SessionLocal()

    try:
        rows = (
            session.query(CrossReference, Article)
            .join(Article, CrossReference.article_id == Article.id)
            .filter(Article.volume == volume, CrossReference.status == "unresolved")
            .order_by(Article.title, CrossReference.id)
            .all()
        )

        grouped: dict[str, list[CrossReference]] = defaultdict(list)

        for xref, article in rows:
            grouped[article.title].append(xref)

        return dict(grouped)

    finally:
        session.close()

def get_backlinks_report(volume: int) -> dict[str, list[CrossReference]]:
    session = SessionLocal()

    try:
        rows = (
            session.query(CrossReference, Article)
            .join(Article, CrossReference.target_article_id == Article.id)
            .filter(
                Article.volume == volume,
                CrossReference.status == "resolved",
                CrossReference.target_article_id.isnot(None),
            )
            .order_by(Article.title, CrossReference.id)
            .all()
        )

        grouped: dict[str, list[CrossReference]] = defaultdict(list)

        for xref, target_article in rows:
            grouped[target_article.title].append(xref)

        return dict(grouped)

    finally:
        session.close()