from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Boolean, String, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.database import Base


class Reply(Base):
    __tablename__ = "reply"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id"))
    message: Mapped[str] = mapped_column(String(4000))
    is_support: Mapped[bool] = mapped_column(Boolean)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="replies")
    user: Mapped["User | None"] = relationship(back_populates="replies")