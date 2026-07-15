from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser, RequireRole
from src.database import get_db
from src.tickets import service
from src.tickets.exceptions import TicketNotFound
from src.tickets.models import TicketStatus, Ticket
from src.tickets.schemas import (
    TicketCreate, TicketOut, TicketUpdate, TicketStats,
    GeneralChatMessageOut, GeneralChatMessageCreate,
    TicketAssign, TicketAssignmentOut,
)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)


@router.get(
    "/",
    response_model=list[TicketOut],
    summary="List tickets",
    description="Returns tickets filtered by group, status, theme, and/or a free-text search term.",
)
async def list_tickets(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    group_id: int | None = Query(default=None, description="Filter by Telegram group ID"),
    ticket_status: TicketStatus | None = Query(default=None, alias="status", description="Filter by status: open, pending, closed"),
    theme_id: int | None = Query(default=None, description="Filter by theme ID"),
    search: str | None = Query(default=None, min_length=1, max_length=200, description="Search in ticket number, message body, and theme name"),
    assigned_to_id: int | None = Query(default=None, description="Support filter: tickets currently assigned TO this user"),
    assigned_by_id: int | None = Query(default=None, description="Manager/Admin filter: tickets where any assignment was made BY this user"),
):
    return await service.get_all(
        db,
        group_id=group_id,
        status=ticket_status,
        theme_id=theme_id,
        search=search,
        assigned_to_id=assigned_to_id,
        assigned_by_id=assigned_by_id,
    )


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.create(
        db,
        ticket_num=data.ticket_num,
        theme_id=data.theme_id,
        group_id=data.group_id,
        soc_user_id=data.soc_user_id,
        message=data.message,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    return await service.update(db, ticket, data.model_dump(exclude_none=True))

from src.auth.dependencies import RequireRole

@router.patch("/{ticket_id}/assign", response_model=TicketOut)
async def assign_ticket(
    ticket_id: int,
    data: TicketAssign,
    current_user: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    return await service.assign(db, ticket, data.user_id, assigned_by_id=current_user.id)


@router.get("/{ticket_id}/assignments", response_model=list[TicketAssignmentOut])
async def get_ticket_assignment_history(
    ticket_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the full assignment audit trail for a ticket (oldest → newest)."""
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    return await service.get_assignment_history(db, ticket_id)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    await service.delete(db, ticket)


general_chat_router = APIRouter(
    prefix="/general-chat",
    tags=["general-chat"],
)

@general_chat_router.get("/messages", response_model=list[GeneralChatMessageOut])
async def get_general_chat_messages(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.get_general_chat_messages(db)

@general_chat_router.post("/messages", response_model=GeneralChatMessageOut, status_code=status.HTTP_201_CREATED)
async def create_general_chat_message(
    data: GeneralChatMessageCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await service.create_general_chat_message(db, user.id, data.message, data.parent_id)

@router.post("/{ticket_id}/forward", response_model=GeneralChatMessageOut, status_code=status.HTTP_201_CREATED)
async def forward_ticket_to_general_chat(
    ticket_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    
    group_name = ticket.group.name if ticket.group else "Unknown Group"
    theme_name = ticket.theme.name if ticket.theme else "Unknown Theme"
    
    message = f"Переслано тікет #{ticket.ticket_num}\nГрупа: {group_name}\nТема: {theme_name}"
    return await service.forward_to_general_chat(db, ticket_id, user.id, message)
