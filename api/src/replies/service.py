from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.replies.models import Reply
from src.tickets.models import TicketAssignment
import logging
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


async def get_by_ticket(db: AsyncSession, ticket_id: int, search: str | None = None) -> list[Reply]:
    q = (
        select(Reply)
        .options(selectinload(Reply.user), selectinload(Reply.ticket))
        .where(Reply.ticket_id == ticket_id)
        .order_by(Reply.created_at.asc())
    )
    if search:
        q = q.where(Reply.message.ilike(f"%{search}%"))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_all(
    db: AsyncSession,
    search: str | None = None,
    status: str | None = None,
    theme_id: int | None = None,
    assigned_to_id: int | None = None,
    assigned_by_id: int | None = None,
    group_id: int | None = None,
) -> list[Reply]:
    from src.tickets.models import Ticket
    q = (
        select(Reply)
        .options(selectinload(Reply.user), selectinload(Reply.ticket))
        .join(Reply.ticket)
        .order_by(Reply.created_at.asc())
    )
    if status:
        q = q.where(Reply.ticket.has(status=status))
    if theme_id is not None:
        q = q.where(Reply.ticket.has(theme_id=theme_id))
    if group_id is not None:
        q = q.where(Reply.ticket.has(group_id=group_id))
    if assigned_to_id is not None:
        # Latest assignment row for this ticket must point TO this user
        latest_for_ticket = (
            select(TicketAssignment.id)
            .where(TicketAssignment.ticket_id == Ticket.id)
            .order_by(TicketAssignment.id.desc())
            .limit(1)
            .correlate(Ticket)
            .scalar_subquery()
        )
        q = q.where(
            select(TicketAssignment.id)
            .where(TicketAssignment.id == latest_for_ticket)
            .where(TicketAssignment.assigned_to_id == assigned_to_id)
            .exists()
        )
    if assigned_by_id is not None:
        q = q.where(
            select(TicketAssignment.id)
            .where(TicketAssignment.ticket_id == Ticket.id)
            .where(TicketAssignment.assigned_by_id == assigned_by_id)
            .exists()
        )
    if search:
        q = q.where(Reply.message.ilike(f"%{search}%"))
    result = await db.execute(q)
    return list(result.scalars().all())

async def get_by_id(db: AsyncSession, reply_id: int) -> Reply | None:
    result = await db.execute(
        select(Reply)
        .options(selectinload(Reply.user))
        .where(Reply.id == reply_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    ticket_id: int,
    message: str,
    is_support: bool,
    user_id: int | None,
) -> Reply:
    from src.tickets.service import _encode_mentions
    if is_support:
        message = await _encode_mentions(db, message)
    reply = Reply(
        ticket_id=ticket_id,
        message=message,
        is_support=is_support,
        user_id=user_id,
    )
    db.add(reply)
    await db.commit()
    return await get_by_id(db, reply.id)


async def delete(db: AsyncSession, reply: Reply) -> None:
    await db.delete(reply)
    await db.commit()

async def notify_client_reply(ticket, user, message: str, requires_client_reply: bool) -> None:
    if not settings.TG_BOT_TOKEN:
        return

    text = (
        f"💬 Від {user.username}\n"
        f"<a href='tg://user?id={ticket.soc_user_id}'>@{ticket.soc_user_name}</a>, "
        f"відповідь по тікету #{ticket.ticket_num}\n\n{message}"
    )
    payload = {
        "chat_id": ticket.soc_user_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if requires_client_reply:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "Надати інформацію", "callback_data": f"pick_{ticket.id}"}]]
        }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage",
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.warning("Telegram send failed for ticket %s: %s", ticket.id, exc)