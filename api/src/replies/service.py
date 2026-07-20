from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.replies.models import Reply
from src.tickets.models import TicketAssignment
import logging
import httpx
from src.config import settings
from src.notifications.service import broadcast_event, notify_users
from src.replies.schemas import ReplyOut
from src.tickets.models import Ticket
from src.themes.models import Theme
from src.groups.models import Group
from src.auth.models import User


logger = logging.getLogger(__name__)


async def get_by_ticket(db: AsyncSession, ticket_id: int, search: str | None = None) -> list[Reply]:
    q = (
        select(Reply)
        .options(
            selectinload(Reply.user),
            selectinload(Reply.ticket),
            selectinload(Reply.parent_reply).selectinload(Reply.user)
        )
        .where(Reply.ticket_id == ticket_id)
        .order_by(Reply.created_at.asc())
    )
    if search:
        conditions = [Reply.message.ilike(f"%{term}%") for term in search.split()]
        q = q.where(and_(*conditions))
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
        .options(
            selectinload(Reply.user), 
            selectinload(Reply.ticket),
            selectinload(Reply.parent_reply).selectinload(Reply.user)
        )
        .join(Reply.ticket)
        .order_by(Reply.created_at.asc())
    )
    if status:
        q = q.where(Ticket.status == status)
    if theme_id is not None:
        q = q.where(Ticket.theme_id == theme_id)
    if group_id is not None:
        q = q.where(Ticket.group_id == group_id)
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
        conditions = []
        for term in search.split():
            t = f"%{term}%"
            conditions.append(
                or_(
                    Reply.message.ilike(t),
                    Ticket.ticket_num.ilike(t)
                )
            )
        q = q.where(and_(*conditions))
    result = await db.execute(q)
    return list(result.scalars().all())

async def get_by_id(db: AsyncSession, reply_id: int) -> Reply | None:
    result = await db.execute(
        select(Reply)
        .options(
            selectinload(Reply.user),
            selectinload(Reply.parent_reply).selectinload(Reply.user)
        )
        .where(Reply.id == reply_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    ticket_id: int,
    message: str,
    is_support: bool,
    user_id: int | None,
    reply_to_reply_id: int | None = None,
) -> Reply:
    from src.tickets.service import _encode_mentions
    if is_support:
        message, _ = await _encode_mentions(db, message)
    reply = Reply(
        ticket_id=ticket_id,
        message=message,
        is_support=is_support,
        user_id=user_id,
        reply_to_reply_id=reply_to_reply_id,
    )
    db.add(reply)
    await db.commit()
    created_reply = await get_by_id(db, reply.id)
    
    latest_assignment = await db.execute(
        select(TicketAssignment)
        .where(TicketAssignment.ticket_id == ticket_id)
        .order_by(TicketAssignment.id.desc())
        .limit(1)
    )
    assignment = latest_assignment.scalar_one_or_none()
    assignee_id = assignment.assigned_to_id if assignment else None

    # Fetch group_id and soc_user_name for sidebar last-message update
    ticket_row = await db.execute(
        select(Ticket.group_id, Ticket.soc_user_name, Group.name.label("group_name"), Theme.name.label("theme_name"), Ticket.ticket_num)
        .outerjoin(Group, Ticket.group_id == Group.id)
        .outerjoin(Theme, Ticket.theme_id == Theme.id)
        .where(Ticket.id == ticket_id)
    )
    ticket_info = ticket_row.first()
    group_id = ticket_info.group_id if ticket_info else None
    soc_user_name = ticket_info.soc_user_name if ticket_info else None
    group_name = ticket_info.group_name if ticket_info else None
    theme_name = ticket_info.theme_name if ticket_info else None
    ticket_num = ticket_info.ticket_num if ticket_info else None

    data = ReplyOut.model_validate(created_reply).model_dump(mode="json")
    data["ticket_assigned_to_id"] = assignee_id
    data["group_id"] = group_id
    data["soc_user_name"] = soc_user_name
    data["group_name"] = group_name
    data["theme_name"] = theme_name
    data["ticket_num"] = ticket_num

    await broadcast_event("new_reply", data)
    
    if not is_support:
        if assignee_id:
            await notify_users(db, "new_reply", data, user_ids=[assignee_id])
        else:
            # If unassigned, notify all admins/managers
            admins_managers_query = select(User.id).where(User.role.in_(["admin", "manager"]), User.is_active == True)
            users_result = await db.execute(admins_managers_query)
            admin_manager_ids = users_result.scalars().all()
            await notify_users(db, "new_reply", data, user_ids=list(admin_manager_ids))
        
    return created_reply


async def delete(db: AsyncSession, reply: Reply) -> None:
    await db.delete(reply)
    await db.commit()

async def notify_client_reply(db: AsyncSession, reply_obj: Reply, ticket: Ticket, user, message: str, requires_client_reply: bool) -> None:
    if not settings.TG_BOT_TOKEN:
        return

    status_val = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
    status_ua = "Відкритий" if status_val == "open" else "В очікуванні" if status_val == "pending" else "Закритий" if status_val == "closed" else str(status_val)

    text = (
        f"💬 Від {user.username}\n"
        f"<a href='tg://user?id={ticket.soc_user_id}'>@{ticket.soc_user_name}</a>, "
        f"відповідь по тікету #{ticket.ticket_num}\n\n{message}"
    )
    chat_id = ticket.group.tg_group_id if ticket.group and ticket.group.tg_group_id else ticket.soc_user_id
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    payload["reply_markup"] = {
        "inline_keyboard": [[{"text": "Відповісти", "callback_data": f"pick_{ticket.id}"}]]
    }

    if reply_obj.reply_to_reply_id:
        target_reply = await db.get(Reply, reply_obj.reply_to_reply_id)
        if target_reply and target_reply.tg_message_id:
            payload["reply_to_message_id"] = target_reply.tg_message_id
    elif ticket.tg_message_id:
        payload["reply_to_message_id"] = ticket.tg_message_id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage",
                json=payload,
            )
            data = response.json()
            if data.get("ok"):
                reply_obj.tg_message_id = data["result"]["message_id"]
                await db.commit()
    except httpx.HTTPError as exc:
        logger.warning("Telegram send failed for ticket %s: %s", ticket.id, exc)