from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.tickets.models import Ticket
from src.replies.models import Reply
from src.auth.models import User
from src.groups.models import Group, UserGroupAccess


async def get_all(db: AsyncSession, search: str | None = None) -> list[Group]:
    q = select(Group).order_by(Group.id)
    if search:
        q = q.where(Group.name.ilike(f"%{search}%"))
    result = await db.execute(q)
    groups = list(result.scalars().all())

    if not groups:
        return groups

    group_ids = [g.id for g in groups]
    from sqlalchemy import func, literal_column

    # Latest ticket per group — ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY created_at DESC)
    rn_ticket = func.row_number().over(
        partition_by=Ticket.group_id,
        order_by=Ticket.created_at.desc()
    ).label("rn")
    ticket_subq = (
        select(
            Ticket.group_id,
            Ticket.soc_user_name,
            Ticket.message,
            Ticket.created_at,
            rn_ticket,
        )
        .where(Ticket.group_id.in_(group_ids))
    ).subquery()

    ticket_rows = await db.execute(
        select(
            ticket_subq.c.group_id,
            ticket_subq.c.soc_user_name,
            ticket_subq.c.message,
            ticket_subq.c.created_at,
        ).where(ticket_subq.c.rn == 1)
    )
    latest_tickets: dict[int, any] = {r.group_id: r for r in ticket_rows}

    # Latest reply per group — ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY reply.created_at DESC)
    rn_reply = func.row_number().over(
        partition_by=Ticket.group_id,
        order_by=Reply.created_at.desc()
    ).label("rn")
    reply_subq = (
        select(
            Ticket.group_id,
            Reply.message,
            Reply.created_at,
            User.username,
            rn_reply,
        )
        .join(Ticket, Reply.ticket_id == Ticket.id)
        .outerjoin(User, Reply.user_id == User.id)
        .where(Ticket.group_id.in_(group_ids))
    ).subquery()

    reply_rows = await db.execute(
        select(
            reply_subq.c.group_id,
            reply_subq.c.message,
            reply_subq.c.created_at,
            reply_subq.c.username,
        ).where(reply_subq.c.rn == 1)
    )
    latest_replies: dict[int, any] = {r.group_id: r for r in reply_rows}

    for group in groups:
        t = latest_tickets.get(group.id)
        r = latest_replies.get(group.id)

        last_msg = None
        last_date = None

        if t and t.message:
            last_msg = f"{t.soc_user_name}: {t.message}"
            last_date = t.created_at

        if r:
            if last_date is None or r.created_at > last_date:
                author = r.username or "Клієнт"
                last_msg = f"{author}: {r.message}"
                last_date = r.created_at

        group.last_message = last_msg
        group.last_time = last_date

    return groups


async def get_by_id(db: AsyncSession, group_id: int) -> Group | None:
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, name: str, tg_group_id: int | None) -> Group:
    group = Group(name=name, tg_group_id=tg_group_id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update(db: AsyncSession, group: Group, name: str | None, tg_group_id: int | None) -> Group:
    if name is not None:
        group.name = name
    if tg_group_id is not None:
        group.tg_group_id = tg_group_id
    await db.commit()
    await db.refresh(group)
    return group


async def delete(db: AsyncSession, group: Group) -> None:
    await db.delete(group)
    await db.commit()


async def assign_user_to_group(db: AsyncSession, group_id: int, user_id: int, is_responsible: bool) -> UserGroupAccess:
    # Check if already exists
    result = await db.execute(
        select(UserGroupAccess).where(
            UserGroupAccess.group_id == group_id,
            UserGroupAccess.user_id == user_id
        )
    )
    access = result.scalar_one_or_none()
    if access:
        access.is_responsible = is_responsible
    else:
        access = UserGroupAccess(group_id=group_id, user_id=user_id, is_responsible=is_responsible)
        db.add(access)
    
    await db.commit()
    await db.refresh(access)
    return access


async def remove_user_from_group(db: AsyncSession, group_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UserGroupAccess).where(
            UserGroupAccess.group_id == group_id,
            UserGroupAccess.user_id == user_id
        )
    )
    access = result.scalar_one_or_none()
    if access:
        await db.delete(access)
        await db.commit()
        return True
    return False
