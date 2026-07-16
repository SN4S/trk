from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.notifications.model import Notification
from src.auth.models import User
from src.websockets.manager import manager
from src.notifications.schemas import NotificationOut
from typing import Any

async def broadcast_event(type: str, data: dict[str, Any]):
    """Broadcast an event to all connected clients for live data updates."""
    await manager.broadcast({"type": type, "data": data})

async def notify_users(db: AsyncSession, type: str, data: dict[str, Any], user_ids: list[int]):
    """Create a Notification DB record for specific users and send it to them via WebSocket."""
    if not user_ids:
        return

    # Filter out duplicates and inactive users
    user_ids = list(set(user_ids))
    users_result = await db.execute(select(User.id).where(User.is_active == True, User.id.in_(user_ids)))
    active_user_ids = users_result.scalars().all()
    
    if not active_user_ids:
        return

    notifications = [
        Notification(user_id=uid, type=type, data=data)
        for uid in active_user_ids
    ]
    db.add_all(notifications)
    await db.commit()
    
    # We must refresh the notifications to get the IDs and created_at timestamps.
    for n in notifications:
        await db.refresh(n)

    # Broadcast to connected sockets
    for notification in notifications:
        notif_data = NotificationOut.model_validate(notification).model_dump(mode="json")
        await manager.send_personal_message({
            "type": "notification_event",
            "data": notif_data
        }, notification.user_id)

async def get_user_notifications(db: AsyncSession, user_id: int, unread_only: bool = False, limit: int = 50) -> list[Notification]:
    q = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    if unread_only:
        q = q.where(Notification.is_read == False)
    q = q.limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())

async def mark_as_read(db: AsyncSession, notification_id: int, user_id: int) -> Notification | None:
    q = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    result = await db.execute(q)
    notification = result.scalar_one_or_none()
    if notification:
        notification.is_read = True
        await db.commit()
    return notification
