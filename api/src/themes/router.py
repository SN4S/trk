from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.database import get_db
from src.themes import service
from src.themes.exceptions import ThemeNotFound
from src.themes.schemas import ThemeCreate, ThemeOut, ThemeUpdate

router = APIRouter(
    prefix="/themes",
    tags=["themes"],
)


@router.get("/", response_model=list[ThemeOut])
async def list_themes(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.get_all(db)


@router.post("/", response_model=ThemeOut, status_code=status.HTTP_201_CREATED)
async def create_theme(
    data: ThemeCreate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.create(db, data.name)


@router.get("/{theme_id}", response_model=ThemeOut)
async def get_theme(
    theme_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    theme = await service.get_by_id(db, theme_id)
    if theme is None:
        raise ThemeNotFound()
    return theme


@router.patch("/{theme_id}", response_model=ThemeOut)
async def update_theme(
    theme_id: int,
    data: ThemeUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    theme = await service.get_by_id(db, theme_id)
    if theme is None:
        raise ThemeNotFound()
    return await service.update(db, theme, data.name)


@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    theme = await service.get_by_id(db, theme_id)
    if theme is None:
        raise ThemeNotFound()
    await service.delete(db, theme)
