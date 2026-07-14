from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.themes.models import Theme


async def get_all(db: AsyncSession) -> list[Theme]:
    result = await db.execute(select(Theme).order_by(Theme.id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, theme_id: int) -> Theme | None:
    result = await db.execute(select(Theme).where(Theme.id == theme_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, name: str) -> Theme:
    theme = Theme(name=name)
    db.add(theme)
    await db.commit()
    await db.refresh(theme)
    return theme


async def update(db: AsyncSession, theme: Theme, name: str) -> Theme:
    theme.name = name
    await db.commit()
    await db.refresh(theme)
    return theme


async def delete(db: AsyncSession, theme: Theme) -> None:
    await db.delete(theme)
    await db.commit()
