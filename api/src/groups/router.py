from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser,  RequireRole
from src.database import get_db
from src.groups import service
from src.groups.exceptions import GroupNotFound
from src.groups.schemas import GroupCreate, GroupOut, GroupUpdate, UserGroupAccessCreate, UserGroupAccessOut
from src.replies.exceptions import ReplyNotFound
from src.replies.schemas import ReplyOut
from src.tickets.exceptions import TicketNotFound
from src.tickets.service import get_all
from src.tickets.models import TicketStatus
from src.replies.service import get_by_ticket

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@router.get(
    "/",
    response_model=list[GroupOut],
    summary="List groups",
    description="Returns all groups, optionally filtered by name substring.",
)
async def list_groups(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, min_length=1, max_length=200, description="Search groups by name"),
):
    return await service.get_all(db, search=search)


@router.post("/", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.create(db, data.name, data.tg_group_id)


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await service.get_by_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    return group


@router.patch("/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await service.get_by_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    return await service.update(db, group, data.name, data.tg_group_id)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await service.get_by_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    await service.delete(db, group)


@router.get("/{group_id}/replies", response_model=list[ReplyOut])
async def get_group_replies(
    group_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, description="Search term"),
    ticket_status: TicketStatus | None = Query(default=None, alias="status", description="Filter by parent ticket status"),
    theme_id: int | None = Query(default=None, description="Filter by parent ticket theme ID"),
    assigned_to_id: int | None = Query(default=None, description="Filter by assigned user ID"),
    assigned_by_id: int | None = Query(default=None, description="Filter by user who made the assignment"),
):
    group = await service.get_by_id(db, group_id)
    if group is None:
        raise GroupNotFound()

    from src.replies.service import get_all as get_all_replies
    return await get_all_replies(
        db,
        group_id=group_id,
        search=search,
        status=ticket_status,
        theme_id=theme_id,
        assigned_to_id=assigned_to_id,
        assigned_by_id=assigned_by_id,
    )



@router.post("/{group_id}/users", response_model=UserGroupAccessOut, status_code=status.HTTP_201_CREATED)
async def assign_user(
    group_id: int,
    data: UserGroupAccessCreate,
    _: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await service.get_by_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    
    return await service.assign_user_to_group(db, group_id, data.user_id, data.is_responsible)


@router.delete("/{group_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    group_id: int,
    user_id: int,
    _: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await service.remove_user_from_group(db, group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access record not found")
