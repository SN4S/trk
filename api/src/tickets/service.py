from sqlalchemy import or_, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.themes.models import Theme
from src.tickets.models import Ticket, TicketStatus, GeneralChatMessage, TicketAssignment
from src.replies.models import Reply

import re
from src.auth.models import User
from src.notifications.service import broadcast_event, notify_users
from src.tickets.schemas import TicketOut, GeneralChatMessageOut

MENTION_TOKEN = re.compile(r'@\[(\d+):([^\]]+)\]')
RAW_MENTION = re.compile(r'@(\w+)')

def _ticket_options():
    """Shared eager-load options for ticket queries."""
    return [
        selectinload(Ticket.theme),
        selectinload(Ticket.group),
        selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_to),
        selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_by),
        selectinload(Ticket.replies),
    ]


async def get_all(
    db: AsyncSession,
    group_id: int | None = None,
    status: TicketStatus | None = None,
    theme_id: int | None = None,
    search: str | None = None,
    assigned_to_id: int | None = None,
    assigned_by_id: int | None = None,
) -> list[Ticket]:
    q = (
        select(Ticket)
        .options(*_ticket_options())
        .join(Ticket.theme, isouter=True)
    )

    if group_id is not None:
        q = q.where(Ticket.group_id == group_id)

    if status is not None:
        q = q.where(Ticket.status == status)

    if theme_id is not None:
        q = q.where(Ticket.theme_id == theme_id)

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
        # Any assignment row for this ticket was created BY this user
        q = q.where(
            select(TicketAssignment.id)
            .where(TicketAssignment.ticket_id == Ticket.id)
            .where(TicketAssignment.assigned_by_id == assigned_by_id)
            .exists()
        )

    if search:
        from src.replies.models import Reply
        q = q.outerjoin(Ticket.replies)
        
        conditions = []
        for term in search.split():
            t = f"%{term}%"
            conditions.append(
                or_(
                    Ticket.ticket_num.ilike(t),
                    Ticket.message.ilike(t),
                    Theme.name.ilike(t),
                    Reply.message.ilike(t),
                )
            )
        q = q.where(and_(*conditions)).distinct()

    q = q.order_by(Ticket.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())



async def get_by_id(db: AsyncSession, ticket_id: int) -> Ticket | None:
    q = (
        select(Ticket)
        .options(*_ticket_options())
        .where(Ticket.id == ticket_id)
        .execution_options(populate_existing=True)
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    ticket_num: str,
    theme_id: int,
    group_id: int,
    soc_user_id: int,
    message: str | None,
) -> Ticket:
    ticket = Ticket(
        ticket_num=ticket_num,
        theme_id=theme_id,
        group_id=group_id,
        soc_user_id=soc_user_id,
        message=message,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    await db.commit()
    
    created_ticket = await get_by_id(db, ticket.id)
    data = TicketOut.model_validate(created_ticket).model_dump(mode="json")
    await broadcast_event("new_ticket", data)
    
    # Notify admins and managers
    admins_managers_query = select(User.id).where(User.role.in_(["admin", "manager"]), User.is_active == True)
    result = await db.execute(admins_managers_query)
    admin_manager_ids = result.scalars().all()
    await notify_users(db, "new_ticket", data, user_ids=list(admin_manager_ids))
    
    return created_ticket


async def update(db: AsyncSession, ticket: Ticket, data: dict) -> Ticket:
    old_status = ticket.status
    for field, value in data.items():
        if value is not None:
            setattr(ticket, field, value)
    await db.commit()
    
    if "status" in data and data["status"] != old_status:
        if ticket.tg_message_id and ticket.group and ticket.group.tg_group_id:
            await update_ticket_tg_message(db, ticket)
    elif any(k in data for k in ("theme_id", "message")) and ticket.tg_message_id and ticket.group and ticket.group.tg_group_id:
        await update_ticket_tg_message(db, ticket)
            
    updated_ticket = await get_by_id(db, ticket.id)
    await broadcast_event("update_ticket", TicketOut.model_validate(updated_ticket).model_dump(mode="json"))
    return updated_ticket

async def update_ticket_tg_message(db: AsyncSession, ticket: Ticket):
    from src.config import settings
    import httpx
    import logging
    logger = logging.getLogger(__name__)
    
    if not settings.TG_BOT_TOKEN:
        return
        
    status_val = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
    status_ua = "Відкритий" if status_val == "open" else "В очікуванні" if status_val == "pending" else "Закритий" if status_val == "closed" else str(status_val)
    
    theme_name = ticket.theme.name if ticket.theme else "Невідомо"
    message_text = ticket.message or "(без тексту)"
    
    text = (
        f"🎫 Тікет #{ticket.ticket_num}\n\n"
        f"Тема: {theme_name}\n"
        f"Статус: {status_ua}\n"
        f"Від: @{ticket.soc_user_name}\n"
        f"Повідомлення: {message_text}"
    )
    
    reply_markup = {
        "inline_keyboard": [[{"text": "Відповісти", "callback_data": f"pick_{ticket.id}"}]]
    }
    
    payload = {
        "chat_id": ticket.group.tg_group_id,
        "message_id": ticket.tg_message_id,
        "text": text,
        "reply_markup": reply_markup
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/editMessageText",
                json=payload
            )
    except Exception as exc:
        logger.warning("Failed to edit Telegram message for ticket %s: %s", ticket.id, exc)

async def assign(
    db: AsyncSession,
    ticket: Ticket,
    user_id: int | None,
    assigned_by_id: int,
) -> Ticket:
    """Create an assignment audit record. user_id=None records an explicit unassign."""
    record = TicketAssignment(
        ticket_id=ticket.id,
        assigned_to_id=user_id,
        assigned_by_id=assigned_by_id,
    )
    db.add(record)
    await db.commit()
    db.expunge(ticket)
    assigned_ticket = await get_by_id(db, ticket.id)
    
    data = TicketOut.model_validate(assigned_ticket).model_dump(mode="json")
    await broadcast_event("update_ticket", data)
    
    # Only post to general chat if the assignee actually changed
    previous_assignment = assigned_ticket.assignments[-2] if len(assigned_ticket.assignments) >= 2 else None
    previous_assignee_id = previous_assignment.assigned_to_id if previous_assignment else None

    if user_id and user_id != previous_assignee_id:
        assigned_user = await db.get(User, user_id)
        if assigned_user:
            msg = f"Призначив(ла) тікет #{assigned_ticket.ticket_num} на @{assigned_user.username}"
            await forward_to_general_chat(db, ticket_id=ticket.id, user_id=assigned_by_id, message=msg)
            
        await notify_users(db, "assign_ticket", data, user_ids=[user_id])
        
    return assigned_ticket


async def get_assignment_history(
    db: AsyncSession, ticket_id: int
) -> list[TicketAssignment]:
    """Return all assignment records for a ticket, oldest first."""
    q = (
        select(TicketAssignment)
        .options(
            selectinload(TicketAssignment.assigned_to),
            selectinload(TicketAssignment.assigned_by),
        )
        .where(TicketAssignment.ticket_id == ticket_id)
        .order_by(TicketAssignment.assigned_at.asc())
    )
    result = await db.execute(q)
    return list(result.scalars().all())


async def delete(db: AsyncSession, ticket: Ticket) -> None:
    await db.delete(ticket)
    await db.commit()

async def forward_to_general_chat(db: AsyncSession, ticket_id: int, user_id: int, message: str) -> GeneralChatMessage:
    message, mentioned_ids = await _encode_mentions(db, message)
    chat_message = GeneralChatMessage(ticket_id=ticket_id, user_id=user_id, message=message)
    db.add(chat_message)
    await db.commit()
    msg = await _get_general_chat_message(db, chat_message.id)
    data = GeneralChatMessageOut.model_validate(msg).model_dump(mode="json")
    await broadcast_event("new_general_message", data)
    
    notify_ids = set(mentioned_ids)
    if notify_ids:
        await notify_users(db, "new_general_message", data, user_ids=list(notify_ids))
        
    return msg

async def _encode_mentions(db: AsyncSession, message: str) -> tuple[str, list[int]]:
    names = set(RAW_MENTION.findall(message))
    if not names:
        return message, []
    result = await db.execute(select(User).where(User.username.in_(names)))
    lookup = {u.username: u.id for u in result.scalars()}

    def repl(m: re.Match) -> str:
        uname = m.group(1)
        uid = lookup.get(uname)
        return f"@[{uid}:{uname}]" if uid else m.group(0)

    return RAW_MENTION.sub(repl, message), list(lookup.values())


async def create_general_chat_message(db: AsyncSession, user_id: int, message: str, parent_id: int | None = None) -> GeneralChatMessage:
    message, mentioned_ids = await _encode_mentions(db, message)
    chat_message = GeneralChatMessage(user_id=user_id, message=message, parent_id=parent_id)
    db.add(chat_message)
    await db.commit()
    msg = await _get_general_chat_message(db, chat_message.id)
    
    data = GeneralChatMessageOut.model_validate(msg).model_dump(mode="json")
    await broadcast_event("new_general_message", data)
    
    notify_ids = set(mentioned_ids)
    if msg.parent and msg.parent.user_id != user_id:
        notify_ids.add(msg.parent.user_id)
        
    if notify_ids:
        await notify_users(db, "new_general_message", data, user_ids=list(notify_ids))
        
    return msg


async def forward_reply_to_general_chat(db: AsyncSession, ticket_id: int, reply_id: int, user_id: int, message: str) -> GeneralChatMessage:
    message, mentioned_ids = await _encode_mentions(db, message)
    chat_message = GeneralChatMessage(ticket_id=ticket_id, reply_id=reply_id, user_id=user_id, message=message)
    db.add(chat_message)
    await db.commit()
    msg = await _get_general_chat_message(db, chat_message.id)
    data = GeneralChatMessageOut.model_validate(msg).model_dump(mode="json")
    await broadcast_event("new_general_message", data)
    
    notify_ids = set(mentioned_ids)
    if notify_ids:
        await notify_users(db, "new_general_message", data, user_ids=list(notify_ids))
        
    return msg


async def _get_general_chat_message(db: AsyncSession, message_id: int) -> GeneralChatMessage:
    q = (
        select(GeneralChatMessage)
        .options(
            selectinload(GeneralChatMessage.user),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.theme),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.group),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_to),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_by),
            selectinload(GeneralChatMessage.reply).selectinload(Reply.user),
            selectinload(GeneralChatMessage.reply).selectinload(Reply.parent_reply).selectinload(Reply.user),
            selectinload(GeneralChatMessage.parent).selectinload(GeneralChatMessage.user),
        )
        .where(GeneralChatMessage.id == message_id)
    )
    return (await db.execute(q)).scalars().first()


async def get_general_chat_messages(db: AsyncSession) -> list[GeneralChatMessage]:
    q = (
        select(GeneralChatMessage)
        .options(
            selectinload(GeneralChatMessage.user),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.theme),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.group),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_to),
            selectinload(GeneralChatMessage.ticket).selectinload(Ticket.assignments).selectinload(TicketAssignment.assigned_by),
            selectinload(GeneralChatMessage.reply).selectinload(Reply.user),
            selectinload(GeneralChatMessage.reply).selectinload(Reply.parent_reply).selectinload(Reply.user),
            selectinload(GeneralChatMessage.parent).selectinload(GeneralChatMessage.user),
        )
        .order_by(GeneralChatMessage.created_at.asc())
    )
    return list((await db.execute(q)).scalars().all())