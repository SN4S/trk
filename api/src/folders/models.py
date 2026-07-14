from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class Folder(Base):
    __tablename__ = "folder"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="folders")
    folder_groups: Mapped[list["FolderGroup"]] = relationship(back_populates="folder")

    @property
    def groups(self):
        return [fg.group for fg in self.folder_groups if fg.group is not None]


class FolderGroup(Base):
    __tablename__ = "folder_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("folder.id"), nullable=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("group.id"), nullable=True)

    folder: Mapped["Folder | None"] = relationship(back_populates="folder_groups")
    group: Mapped["Group | None"] = relationship(back_populates="folder_groups")