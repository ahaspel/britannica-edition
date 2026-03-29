from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from britannica.db.base import Base


class ArticleImage(Base):
    __tablename__ = "article_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"),
        nullable=False,
    )

    source_page_id: Mapped[int] = mapped_column(
        ForeignKey("source_pages.id"),
        nullable=False,
    )

    sequence_in_article: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    filename: Mapped[str] = mapped_column(String(500), nullable=False)

    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    commons_url: Mapped[str] = mapped_column(String(1000), nullable=False)
