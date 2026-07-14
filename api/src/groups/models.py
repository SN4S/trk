from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tg_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="group")
    folder_groups: Mapped[list["FolderGroup"]] = relationship(back_populates="group")
    users_access: Mapped[list["UserGroupAccess"]] = relationship(back_populates="group")


class UserGroupAccess(Base):
    __tablename__ = "user_group_access"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id", ondelete="CASCADE"))
    is_responsible: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship(back_populates="users_access")
