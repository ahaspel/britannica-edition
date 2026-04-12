from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from britannica.db.base import Base


class CrossReference(Base):
    __tablename__ = "cross_references"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)

    surface_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_target: Mapped[str] = mapped_column(String(255), nullable=False)
    xref_type: Mapped[str] = mapped_column(String(50), nullable=False)

    target_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id"),
        nullable=True,
    )

    # When the xref points to a section *within* the target article
    # (e.g. "Clement I" inside CLEMENT (POPES)), this holds the section
    # name. The viewer appends #section-<slug> to the link so the user
    # lands at the correct anchor.
    target_section: Mapped[str | None] = mapped_column(
        String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unresolved")