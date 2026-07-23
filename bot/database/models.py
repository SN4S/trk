from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, func, Boolean, Enum, Table, Column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum

class StatusEnum(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"

class Base(AsyncAttrs, DeclarativeBase):
    pass


class Theme(Base):
    __tablename__ = "theme"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

class Group(Base):
    __tablename__ = "group"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tg_group_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())

class Attachment(Base):
    __tablename__ = "attachment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("ticket.id", ondelete="SET NULL"), nullable=True)
    reply_id: Mapped[int | None] = mapped_column(ForeignKey("reply.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())

class Ticket(Base):
    __tablename__ = "ticket"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_num: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    theme_id: Mapped[int] = mapped_column(ForeignKey("theme.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=False)
    soc_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    soc_user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.OPEN)
    tg_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    theme: Mapped["Theme"] = relationship()
    group: Mapped["Group"] = relationship()
    replies: Mapped[list["Reply"]] = relationship(back_populates="ticket", order_by="Reply.created_at")
    attachments: Mapped[list["Attachment"]] = relationship()

class Reply(Base):
    __tablename__ = "reply"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_support: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    tg_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reply_to_reply_id: Mapped[int | None] = mapped_column(ForeignKey("reply.id", ondelete="CASCADE"), nullable=True)

    ticket: Mapped["Ticket"] = relationship(back_populates="replies")
    user: Mapped["User"] = relationship()
    parent_reply: Mapped["Reply | None"] = relationship(remote_side=[id])
    attachments: Mapped[list["Attachment"]] = relationship()

class TicketAssignment(Base):
    __tablename__ = "ticket_assignment"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False)
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    assigned_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())

class Folder(Base):
    __tablename__ = "folder"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    user: Mapped["User"] = relationship()

class FolderGroup(Base):
    __tablename__ = "folder_group"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("folder.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    
    folder: Mapped["Folder"] = relationship()
    group: Mapped["Group"] = relationship()


engine = None
async_session = None

def init_engine(db_url: str):
    global engine, async_session
    engine = create_async_engine(db_url, pool_recycle=3600)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)