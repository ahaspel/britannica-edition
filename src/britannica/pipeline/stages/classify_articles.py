from britannica.db.models import Article
from britannica.db.session import SessionLocal


def classify_articles_for_volume(volume: int) -> dict[str, int]:
    """Classify articles as 'article', 'front_matter', or 'plate'."""
    session = SessionLocal()

    try:
        articles = (
            session.query(Article)
            .filter(Article.volume == volume)
            .order_by(Article.page_start, Article.title)
            .all()
        )

        counts: dict[str, int] = {}

        for article in articles:
            body = (article.body or "").strip()

            # Preserve plate classification from boundary detection
            if article.article_type == "plate":
                article_type = "plate"
            elif body:
                article_type = "article"
            else:
                # No body — either a plate or front matter.
                # Boundary detection already classifies plates; anything
                # else without body is front matter.
                article_type = "front_matter"

            if article.article_type != article_type:
                article.article_type = article_type

            counts[article_type] = counts.get(article_type, 0) + 1

        session.commit()
        return counts

    finally:
        session.close()
