from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.groups.models import Group, UserGroupAccess


async def get_all(db: AsyncSession, search: str | None = None) -> list[Group]:
    q = select(Group).order_by(Group.id)
    if search:
        q = q.where(Group.name.ilike(f"%{search}%"))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, group_id: int) -> Group | None:
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, name: str, tg_group_id: int | None) -> Group:
    group = Group(name=name, tg_group_id=tg_group_id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update(db: AsyncSession, group: Group, name: str | None, tg_group_id: int | None) -> Group:
    if name is not None:
        group.name = name
    if tg_group_id is not None:
        group.tg_group_id = tg_group_id
    await db.commit()
    await db.refresh(group)
    return group


async def delete(db: AsyncSession, group: Group) -> None:
    await db.delete(group)
    await db.commit()


async def assign_user_to_group(db: AsyncSession, group_id: int, user_id: int, is_responsible: bool) -> UserGroupAccess:
    # Check if already exists
    result = await db.execute(
        select(UserGroupAccess).where(
            UserGroupAccess.group_id == group_id,
            UserGroupAccess.user_id == user_id
        )
    )
    access = result.scalar_one_or_none()
    if access:
        access.is_responsible = is_responsible
    else:
        access = UserGroupAccess(group_id=group_id, user_id=user_id, is_responsible=is_responsible)
        db.add(access)
    
    await db.commit()
    await db.refresh(access)
    return access


async def remove_user_from_group(db: AsyncSession, group_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UserGroupAccess).where(
            UserGroupAccess.group_id == group_id,
            UserGroupAccess.user_id == user_id
        )
    )
    access = result.scalar_one_or_none()
    if access:
        await db.delete(access)
        await db.commit()
        return True
    return False
