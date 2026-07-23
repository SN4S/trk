from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.database import get_db
from src.replies import service
from src.replies.exceptions import ReplyNotFound
from src.replies.schemas import ReplyCreate, ReplyOut
from src.tickets import service as ticket_service
from src.tickets.exceptions import TicketNotFound
from src.replies.service import notify_client_reply
from src.tickets.schemas import GeneralChatMessageOut, TicketAssign
from src.auth.models import User
from src.replies.models import Reply
from fastapi import HTTPException
router = APIRouter(
    prefix="/tickets/{ticket_id}/replies",
    tags=["replies"],
)


@router.get(
    "/",
    response_model=list[ReplyOut],
    summary="List replies for a ticket",
    description="Returns all replies for a ticket, optionally filtered by message content.",
)
async def list_replies(
    ticket_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, min_length=1, max_length=200, description="Search in reply message text"),
):
    ticket = await ticket_service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    return await service.get_by_ticket(db, ticket_id, search=search)


@router.post("/", response_model=ReplyOut, status_code=status.HTTP_201_CREATED)
async def create_reply(
    ticket_id: int,
    data: ReplyCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await ticket_service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    reply = await service.create(
        db,
        ticket_id=ticket_id,
        message=data.message,
        is_support=data.is_support,
        user_id=user.id,
        reply_to_reply_id=data.reply_to_reply_id,
        attachment_ids=data.attachment_ids,
    )

    send_to_tg = True
    if data.reply_to_reply_id:
        parent_reply = await db.get(Reply, data.reply_to_reply_id)
        if parent_reply and not parent_reply.tg_message_id:
            send_to_tg = False

    if send_to_tg and data.is_support and user.role in ["admin", "manager"]:
        await notify_client_reply(db, reply, ticket, user, data.message, data.requires_client_reply)
    return reply


@router.delete("/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reply(
    ticket_id: int,
    reply_id: int,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reply = await service.get_by_id(db, reply_id)
    if reply is None or reply.ticket_id != ticket_id:
        raise ReplyNotFound()
    await service.delete(db, reply)


@router.post("/{reply_id}/forward", response_model=GeneralChatMessageOut, status_code=status.HTTP_201_CREATED)
async def forward_reply(
    ticket_id: int,
    reply_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await ticket_service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    reply = await service.get_by_id(db, reply_id)
    if reply is None or reply.ticket_id != ticket_id:
        raise ReplyNotFound()
    message = f"Переслано повідомлення з тікету #{ticket.ticket_num}:\n{reply.message}"
    return await ticket_service.forward_reply_to_general_chat(db, ticket_id, reply_id, user.id, message)


@router.post("/{reply_id}/assign", response_model=GeneralChatMessageOut, status_code=status.HTTP_201_CREATED)
async def assign_reply(
    ticket_id: int,
    reply_id: int,
    data: TicketAssign,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await ticket_service.get_by_id(db, ticket_id)
    if ticket is None:
        raise TicketNotFound()
    reply = await service.get_by_id(db, reply_id)
    if reply is None or reply.ticket_id != ticket_id:
        raise ReplyNotFound()
        
    if not data.user_id:
        raise HTTPException(status_code=400, detail="User ID is required to assign a reply")
        
    assigned_user = await db.get(User, data.user_id)
    if not assigned_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    message = f"Призначив(ла) повідомлення з тікету #{ticket.ticket_num} на @{assigned_user.username}:\n{reply.message}"
    
    return await ticket_service.forward_reply_to_general_chat(db, ticket_id, reply_id, user.id, message)