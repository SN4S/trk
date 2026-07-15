from sqlalchemy import select, desc, func, case
from database import models
from database.models import Theme, Ticket, Reply, Group, User
import asyncio
import httpx
import os

INTERNAL_SECRET = os.getenv("INTERNAL_API_SECRET", "")

async def notify_api(event_type: str, data: dict):
    api_url = os.getenv("API_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{api_url}/ws/broadcast",
                json={"type": event_type, "data": data},
                headers={"X-Internal-Secret": INTERNAL_SECRET},
                timeout=2.0
            )
    except Exception as e:
        print("Failed to notify API:", e)


async def get_themes() -> list[Theme]:
    async with models.async_session() as session:
        result = await session.execute(select(Theme))
        return list(result.scalars().all())

async def reserve_ticket(group_chat_id: int, group_title: str, theme_id: int, soc_user_id: int, soc_user_name: str) -> Ticket:
    async with models.async_session() as session:
        # Get or create group
        result = await session.execute(select(Group).where(Group.tg_group_id == group_chat_id))
        group = result.scalar_one_or_none()
        if not group:
            group = Group(tg_group_id=group_chat_id, name=group_title)
            session.add(group)
            await session.flush()

        # Get count of tickets for this group
        count_result = await session.execute(select(func.count(Ticket.id)).where(Ticket.group_id == group.id))
        count = count_result.scalar() or 0
        slug = "".join(c for c in group.name if c.isalnum()) or "group"
        ticket_num = f"{slug}-{count + 1}"

        ticket = Ticket(
            ticket_num=ticket_num,
            group_id=group.id,
            theme_id=theme_id,
            soc_user_id=soc_user_id,
            soc_user_name=soc_user_name,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket

async def finalize_ticket(ticket_id: int, message: str) -> Ticket:
    async with models.async_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket:
            ticket.message = message
            await session.commit()
            await session.refresh(ticket)
            asyncio.create_task(notify_api("new_ticket", {"id": ticket.id}))
        return ticket

async def delete_ticket(ticket_id: int):
    async with models.async_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket:
            await session.delete(ticket)
            await session.commit()
            asyncio.create_task(notify_api("update_ticket", {"id": ticket_id}))

async def get_theme_name(theme_id: int) -> str | None:
    async with models.async_session() as session:
        theme = await session.get(Theme, theme_id)
        return theme.name if theme else None

async def add_reply(ticket_id: int, message: str, is_support: bool, user_id: int | None = None) -> dict:
    async with models.async_session() as session:
        reply = Reply(ticket_id=ticket_id, message=message, is_support=is_support, user_id=user_id)
        session.add(reply)
        await session.commit()
        await session.refresh(reply)
        
        admin_name = None
        if user_id:
            user = await session.get(User, user_id)
            if user:
                admin_name = user.username
                
        from database.models import TicketAssignment
        latest_assignment = await session.execute(
            select(TicketAssignment)
            .where(TicketAssignment.ticket_id == ticket_id)
            .order_by(TicketAssignment.id.desc())
            .limit(1)
        )
        assignment = latest_assignment.scalar_one_or_none()
        assignee_id = assignment.assigned_to_id if assignment else None

        # Fetch group_id and soc_user_name for sidebar update
        ticket_obj = await session.get(Ticket, ticket_id)
        group_id = ticket_obj.group_id if ticket_obj else None
        soc_user_name = ticket_obj.soc_user_name if ticket_obj else None

        data = {
            "id": reply.id,
            "ticket_id": ticket_id,
            "message": reply.message,
            "is_support": reply.is_support,
            "user_id": reply.user_id,
            "created_at": reply.created_at.isoformat() if reply.created_at else None,
            "ticket_assigned_to_id": assignee_id,
            "group_id": group_id,
            "soc_user_name": soc_user_name,
        }
        if admin_name:
            data["user"] = {"id": user_id, "username": admin_name}

        asyncio.create_task(notify_api("new_reply", data))
        return {"id": reply.id, "message": reply.message, "is_support": reply.is_support,
                "admin_name": admin_name, "created_at": reply.created_at}

async def get_replies(ticket_id: int) -> list[dict]:
    async with models.async_session() as session:
        stmt = (
            select(Reply, User.username.label("admin_name"))
            .outerjoin(User, Reply.user_id == User.id)
            .where(Reply.ticket_id == ticket_id)
            .order_by(Reply.created_at)
        )
        result = await session.execute(stmt)
        return [
            {"id": r.id, "message": r.message, "is_support": r.is_support,
             "admin_name": admin_name, "created_at": r.created_at}
            for r, admin_name in result
        ]

from sqlalchemy.orm import selectinload

async def get_ticket_by_num(ticket_num: str) -> Ticket | None:
    async with models.async_session() as session:
        result = await session.execute(
            select(Ticket).options(selectinload(Ticket.group)).where(Ticket.ticket_num == ticket_num)
        )
        return result.scalar_one_or_none()

async def get_open_tickets_for_user(soc_user_id: int) -> list[Ticket]:
    async with models.async_session() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.soc_user_id == soc_user_id, Ticket.status != "closed")
            .order_by(desc(Ticket.created_at))
        )
        return list(result.scalars().all())

async def get_ticket_by_id(ticket_id: int) -> Ticket | None:
    async with models.async_session() as session:
        return await session.get(Ticket, ticket_id)


# help methods for api calls

async def get_all_tickets(group_chat_id: int | None = None) -> list[dict]:
    async with models.async_session() as session:
        stmt = (
            select(Ticket, Theme.name.label("theme_name"), Group.name.label("group_name"))
            .outerjoin(Theme, Ticket.theme_id == Theme.id)
            .outerjoin(Group, Ticket.group_id == Group.id)
            .order_by(Ticket.updated_at.desc())
        )
        if group_chat_id is not None:
            stmt = stmt.where(Group.tg_group_id == group_chat_id)
        rows = await session.execute(stmt)
        result = []
        for ticket, theme_name, group_name in rows:
            d = {c.name: getattr(ticket, c.name) for c in Ticket.__table__.columns}
            if hasattr(d.get("status"), "value"):
                d["status"] = d["status"].value
            d["theme_name"] = theme_name
            d["group_name"] = group_name
            result.append(d)
        return result

async def get_ticket(ticket_id: int) -> dict | None:
    async with models.async_session() as session:
        stmt = (
            select(Ticket, Theme.name.label("theme_name"), Group.name.label("group_name"))
            .outerjoin(Theme, Ticket.theme_id == Theme.id)
            .outerjoin(Group, Ticket.group_id == Group.id)
            .where(Ticket.id == ticket_id)
        )
        row = (await session.execute(stmt)).first()
        if not row:
            return None
        ticket, theme_name, group_name = row
        d = {c.name: getattr(ticket, c.name) for c in Ticket.__table__.columns}
        if hasattr(d.get("status"), "value"):
            d["status"] = d["status"].value
        d["theme_name"] = theme_name
        d["group_name"] = group_name
        
        d["replies"] = await get_replies(ticket_id)
        return d

async def get_groups_with_counts() -> list[dict]:
    async with models.async_session() as session:
        stmt = (
            select(
                Group.tg_group_id,
                Group.name,
                func.sum(case((Ticket.status != "closed", 1), else_=0)).label("ticket_count"),
            )
            .outerjoin(Ticket, Group.id == Ticket.group_id)
            .group_by(Group.tg_group_id, Group.name)
        )
        rows = await session.execute(stmt)
        return [
            {"chat_id": r.tg_group_id, "title": r.name, "ticket_count": r.ticket_count or 0}
            for r in rows
        ]

async def get_ticket_counts() -> dict:
    async with models.async_session() as session:
        stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        rows = (await session.execute(stmt)).all()
        counts = {r[0].value if hasattr(r[0], "value") else r[0]: r[1] for r in rows}
        return {
            "all": sum(counts.values()),
            "open": counts.get("open", 0),
            "pending": counts.get("pending", 0),
            "closed": counts.get("closed", 0),
        }

async def update_ticket_status(ticket_id: int, status: str) -> dict | None:
    async with models.async_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            return None
        ticket.status = status
        await session.commit()
    asyncio.create_task(notify_api("update_ticket", {"id": ticket_id}))
    return await get_ticket(ticket_id)

async def create_theme(name: str) -> Theme:
    async with models.async_session() as session:
        theme = Theme(name=name)
        session.add(theme)
        await session.commit()
        await session.refresh(theme)
        return theme

async def delete_theme(theme_id: int) -> bool:
    async with models.async_session() as session:
        theme = await session.get(Theme, theme_id)
        if theme:
            await session.delete(theme)
            await session.commit()
            return True
        return False