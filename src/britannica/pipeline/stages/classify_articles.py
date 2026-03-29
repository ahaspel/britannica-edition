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

        # Find the first real encyclopedia article.
        # The first headword is always a single short word (AA, AB, ABACUS).
        first_real_page = None
        for article in articles:
            body = (article.body or "").strip()
            title = article.title
            if (
                len(body.split()) >= 10
                and title.upper() == title
                and " " not in title
                and len(title) <= 15
            ):
                first_real_page = article.page_start
                break

        for article in articles:
            body = (article.body or "").strip()

            # Preserve plate classification from boundary detection
            if article.article_type == "plate":
                article_type = "plate"
            elif first_real_page and article.page_start < first_real_page:
                article_type = "front_matter"
            elif not body and first_real_page and article.page_start > first_real_page:
                article_type = "plate"
            elif not body:
                article_type = "front_matter"
            else:
                article_type = "article"

            if article.article_type != article_type:
                article.article_type = article_type

            counts[article_type] = counts.get(article_type, 0) + 1

        session.commit()
        return counts

    finally:
        session.close()
