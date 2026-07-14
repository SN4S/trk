from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.database import get_db
from src.tickets.models import TicketStatus, Ticket
from src.tickets.schemas import TicketCreate, TicketOut, TicketUpdate, TicketStats


from src.replies.schemas import ReplyOut
from src.replies import service as replies_service

router = APIRouter(
    tags=["misc"],
)

@router.get("/replies", response_model=list[ReplyOut], summary="Get all replies globally")
async def get_all_replies(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, description="Search term"),
    ticket_status: TicketStatus | None = Query(default=None, alias="status", description="Filter by parent ticket status"),
    theme_id: int | None = Query(default=None, description="Filter by parent ticket theme ID"),
    assigned_to_id: int | None = Query(default=None, description="Filter by parent ticket assigned user ID"),
    assigned_by_id: int | None = Query(default=None, description="Filter by user who made the assignment"),
):
    return await replies_service.get_all(
        db,
        search=search,
        status=ticket_status,
        theme_id=theme_id,
        assigned_to_id=assigned_to_id,
        assigned_by_id=assigned_by_id,
    )

@router.get("/stats", response_model=TicketStats)
async def get_ticket_stats(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    group_id: Annotated[int | None, Query()] = None,
):
    stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)

    if group_id is not None:
        stmt = stmt.where(Ticket.group_id == group_id)

    result = await db.execute(stmt)
    counts = {status: count for status, count in result.all()}

    open_ = counts.get("open", 0)
    pending = counts.get("pending", 0)
    closed = counts.get("closed", 0)

    return TicketStats(
        group_id=group_id,
        all=open_ + pending + closed,
        open=open_,
        pending=pending,
        closed=closed,
    )