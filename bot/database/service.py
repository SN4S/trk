from datetime import timezone

from sqlalchemy import select, desc, func, case
from sqlalchemy.orm import selectinload
from database import models
from database.models import Theme, Ticket, Reply, Group, User, TicketAssignment, Attachment
import asyncio
import httpx
import os

async def notify_api(event_type: str, data: dict):
    secret = os.getenv("INTERNAL_API_SECRET", "")
    api_url = os.getenv("API_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{api_url}/ws/broadcast",
                json={"type": event_type, "data": data},
                headers={"X-Internal-Secret": secret},
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
        slug_parts = []
        for word in group.name.replace('-', ' ').replace('_', ' ').split():
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word:
                slug_parts.append(clean_word[0].upper())
        slug = "".join(slug_parts) or "T"
        ticket_num = f"{slug}-{(count + 1):06d}"

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

async def finalize_ticket(ticket_id: int, message: str, attachment_ids: list[int] | None = None) -> Ticket:
    async with models.async_session() as session:
        ticket_row = await session.execute(
            select(Ticket, Group.name.label("group_name"), Theme.name.label("theme_name"))
            .outerjoin(Group, Ticket.group_id == Group.id)
            .outerjoin(Theme, Ticket.theme_id == Theme.id)
            .where(Ticket.id == ticket_id)
        )
        ticket_info = ticket_row.first()
        if ticket_info:
            ticket, group_name, theme_name = ticket_info
            ticket.message = message
            
            attachments_data = []
            if attachment_ids:
                from sqlalchemy import update
                await session.execute(
                    update(Attachment)
                    .where(Attachment.id.in_(attachment_ids))
                    .values(ticket_id=ticket.id)
                )
                att_result = await session.execute(select(Attachment).where(Attachment.id.in_(attachment_ids)))
                for att in att_result.scalars().all():
                    attachments_data.append({
                        "id": att.id,
                        "filename": att.filename,
                        "file_url": f"/{att.file_path}" if not att.file_path.startswith("/") else att.file_path,
                        "content_type": att.content_type
                    })
            
            await session.commit()
            await session.refresh(ticket)
            asyncio.create_task(notify_api("new_ticket", {
                "id": ticket.id,
                "group_id": ticket.group_id,
                "soc_user_name": ticket.soc_user_name,
                "message": ticket.message,
                "created_at": ticket.created_at.replace(tzinfo=timezone.utc).isoformat() if ticket.created_at else None,
                "ticket_num": ticket.ticket_num,
                "theme_id": ticket.theme_id,
                "status": ticket.status.value if hasattr(ticket.status, "value") else ticket.status,
                "group_name": group_name,
                "theme_name": theme_name,
                "attachments": attachments_data,
            }))
            return ticket
        return None

async def set_ticket_tg_message_id(ticket_id: int, tg_message_id: int) -> Ticket | None:
    async with models.async_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket:
            ticket.tg_message_id = tg_message_id
            await session.commit()
            await session.refresh(ticket)
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

async def add_reply(ticket_id: int, message: str, is_support: bool, user_id: int | None = None, tg_message_id: int | None = None, reply_to_reply_id: int | None = None, attachment_ids: list[int] | None = None) -> dict:
    async with models.async_session() as session:
        reply = Reply(ticket_id=ticket_id, message=message, is_support=is_support, user_id=user_id, tg_message_id=tg_message_id, reply_to_reply_id=reply_to_reply_id)
        session.add(reply)
        await session.flush()
        
        attachments_data = []
        if attachment_ids:
            from sqlalchemy import update
            await session.execute(
                update(Attachment)
                .where(Attachment.id.in_(attachment_ids))
                .values(reply_id=reply.id)
            )
            att_result = await session.execute(select(Attachment).where(Attachment.id.in_(attachment_ids)))
            for att in att_result.scalars().all():
                attachments_data.append({
                    "id": att.id,
                    "filename": att.filename,
                    "file_url": f"/{att.file_path}" if not att.file_path.startswith("/") else att.file_path,
                    "content_type": att.content_type
                })
        
        await session.commit()
        await session.refresh(reply)
        
        admin_name = None
        if user_id:
            user = await session.get(User, user_id)
            if user:
                admin_name = user.username
                
        latest_assignment = await session.execute(
            select(TicketAssignment)
            .where(TicketAssignment.ticket_id == ticket_id)
            .order_by(TicketAssignment.id.desc())
            .limit(1)
        )
        assignment = latest_assignment.scalar_one_or_none()
        assignee_id = assignment.assigned_to_id if assignment else None

        # Fetch group_id, soc_user_name, group_name, theme_name, ticket_num for frontend
        ticket_row = await session.execute(
            select(Ticket, Group.name.label("group_name"), Theme.name.label("theme_name"))
            .outerjoin(Group, Ticket.group_id == Group.id)
            .outerjoin(Theme, Ticket.theme_id == Theme.id)
            .where(Ticket.id == ticket_id)
        )
        ticket_info = ticket_row.first()
        if ticket_info:
            ticket_obj, group_name, theme_name = ticket_info
            group_id = ticket_obj.group_id
            soc_user_name = ticket_obj.soc_user_name
            ticket_num = ticket_obj.ticket_num
        else:
            group_id = soc_user_name = group_name = theme_name = ticket_num = None

        data = {
            "id": reply.id,
            "ticket_id": ticket_id,
            "message": reply.message,
            "is_support": reply.is_support,
            "user_id": reply.user_id,
            "created_at": reply.created_at.replace(tzinfo=timezone.utc).isoformat() if reply.created_at else None,
            "ticket_assigned_to_id": assignee_id,
            "group_id": group_id,
            "soc_user_name": soc_user_name,
            "group_name": group_name,
            "theme_name": theme_name,
            "ticket_num": ticket_num,
            "attachments": attachments_data,
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

async def get_reply_by_tg_message_id(tg_message_id: int, ticket_id: int) -> Reply | None:
    async with models.async_session() as session:
        result = await session.execute(
            select(Reply).where(Reply.tg_message_id == tg_message_id, Reply.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()


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
    # await directly — session is closed, no DB dependency
    await notify_api("update_ticket", {"id": ticket_id})
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