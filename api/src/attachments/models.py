from datetime import datetime

from sqlalchemy import Integer, String, ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1000))
    content_type: Mapped[str] = mapped_column(String(100))
    
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("ticket.id"), nullable=True)
    reply_id: Mapped[int | None] = mapped_column(ForeignKey("reply.id"), nullable=True)
    general_chat_message_id: Mapped[int | None] = mapped_column(ForeignKey("general_chat_message.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="attachments")
    reply: Mapped["Reply"] = relationship(back_populates="attachments")
    general_chat_message: Mapped["GeneralChatMessage"] = relationship(back_populates="attachments")
