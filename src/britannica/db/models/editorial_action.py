from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from britannica.db.base import Base


class EditorialAction(Base):
    __tablename__ = "editorial_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    page_id: Mapped[int] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(100))

    before: Mapped[str | None] = mapped_column(Text, nullable=True)
    after: Mapped[str | None] = mapped_column(Text, nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)