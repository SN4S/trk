from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.auth.models import User
from src.database import get_db
from src.folders import service
from src.folders.exceptions import FolderNotFound
from src.folders.schema import FolderCreate, FolderGroupAdd, FolderOut, FolderUpdate

router = APIRouter(
    prefix="/folders",
    tags=["folders"],
)


@router.get("/", response_model=list[FolderOut])
async def list_folders(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.get_all(db, user.id)


@router.post("/", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.create(db, data.name, user.id)


@router.get("/{folder_id}", response_model=FolderOut)
async def get_folder(
    folder_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    folder = await service.get_by_id(db, folder_id, user.id)
    if folder is None:
        raise FolderNotFound()
    return folder


@router.patch("/{folder_id}", response_model=FolderOut)
async def update_folder(
    folder_id: int,
    data: FolderUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    folder = await service.get_by_id(db, folder_id, user.id)
    if folder is None:
        raise FolderNotFound()
    return await service.update(db, folder, data.name)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    folder = await service.get_by_id(db, folder_id, user.id)
    if folder is None:
        raise FolderNotFound()
    await service.delete(db, folder)


@router.post("/{folder_id}/groups", response_model=FolderOut, status_code=status.HTTP_200_OK)
async def add_group_to_folder(
    folder_id: int,
    data: FolderGroupAdd,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    folder = await service.get_by_id(db, folder_id, user.id)
    if folder is None:
        raise FolderNotFound()
    return await service.add_group(db, folder, data.group_id)


@router.delete("/{folder_id}/groups/{group_id}", response_model=FolderOut, status_code=status.HTTP_200_OK)
async def remove_group_from_folder(
    folder_id: int,
    group_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    folder = await service.get_by_id(db, folder_id, user.id)
    if folder is None:
        raise FolderNotFound()
    return await service.remove_group(db, folder, group_id)
