from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.folders.models import Folder, FolderGroup
from src.groups.models import Group


async def _get_with_groups(db: AsyncSession, folder_id: int) -> Folder | None:
    result = await db.execute(
        select(Folder)
        .options(selectinload(Folder.folder_groups).selectinload(FolderGroup.group))
        .where(Folder.id == folder_id)
    )
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession, user_id: int) -> list[Folder]:
    result = await db.execute(
        select(Folder)
        .options(selectinload(Folder.folder_groups).selectinload(FolderGroup.group))
        .where(Folder.user_id == user_id)
        .order_by(Folder.id)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, folder_id: int, user_id: int) -> Folder | None:
    result = await db.execute(
        select(Folder)
        .options(selectinload(Folder.folder_groups).selectinload(FolderGroup.group))
        .where(Folder.id == folder_id, Folder.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, name: str, user_id: int) -> Folder:
    folder = Folder(name=name, user_id=user_id)
    db.add(folder)
    await db.commit()
    folder = await _get_with_groups(db, folder.id)
    return folder


async def update(db: AsyncSession, folder: Folder, name: str) -> Folder:
    folder.name = name
    await db.commit()
    folder = await _get_with_groups(db, folder.id)
    return folder


async def delete(db: AsyncSession, folder: Folder) -> None:
    await db.delete(folder)
    await db.commit()


async def add_group(db: AsyncSession, folder: Folder, group_id: int) -> Folder:
    """Link a group to a folder. Returns the updated folder."""
    # Check duplicate
    existing = await db.execute(
        select(FolderGroup).where(
            FolderGroup.folder_id == folder.id,
            FolderGroup.group_id == group_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        from src.folders.exceptions import GroupAlreadyInFolder
        raise GroupAlreadyInFolder()

    db.add(FolderGroup(folder_id=folder.id, group_id=group_id))
    await db.commit()
    return await _get_with_groups(db, folder.id)


async def remove_group(db: AsyncSession, folder: Folder, group_id: int) -> Folder:
    """Unlink a group from a folder. Returns the updated folder."""
    result = await db.execute(
        select(FolderGroup).where(
            FolderGroup.folder_id == folder.id,
            FolderGroup.group_id == group_id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        from src.folders.exceptions import GroupNotInFolder
        raise GroupNotInFolder()

    await db.delete(link)
    await db.commit()
    return await _get_with_groups(db, folder.id)
