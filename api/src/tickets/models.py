import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, ForeignKey, DateTime, func, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_num: Mapped[str] = mapped_column(String(32))
    theme_id: Mapped[int] = mapped_column(ForeignKey("theme.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    soc_user_id: Mapped[int] = mapped_column(BigInteger)
    soc_user_name: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now(), nullable=True)
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.OPEN)

    theme: Mapped["Theme"] = relationship(back_populates="tickets")
    group: Mapped["Group"] = relationship(back_populates="tickets")
    replies: Mapped[list["Reply"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    # Ordered history; latest entry = current assignment
    assignments: Mapped[list["TicketAssignment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketAssignment.assigned_at",
    )


class TicketAssignment(Base):
    """Audit log of every assignment action on a ticket.

    The *current* assignee is the row with the highest ``id`` (or ``assigned_at``).
    A row with ``assigned_to_id=NULL`` means the ticket was explicitly unassigned.
    """
    __tablename__ = "ticket_assignment"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id", ondelete="CASCADE"))
    # NULL = unassigned
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="assignments")
    assigned_to: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_to_id])
    assigned_by: Mapped["User"] = relationship(foreign_keys=[assigned_by_id])


class GeneralChatMessage(Base):
    __tablename__ = "general_chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("ticket.id"), nullable=True)
    reply_id: Mapped[int | None] = mapped_column(ForeignKey("reply.id"), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("general_chat_message.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    message: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    ticket: Mapped["Ticket"] = relationship()
    reply: Mapped["Reply"] = relationship()
    parent: Mapped["GeneralChatMessage"] = relationship(remote_side=[id])
    user: Mapped["User"] = relationship()