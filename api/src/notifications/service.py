from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.notifications.model import Notification, PushSubscription
from src.auth.models import User
from src.websockets.manager import manager
from src.notifications.schemas import NotificationOut, PushSubscriptionIn
from typing import Any
import json
import asyncio
from pywebpush import webpush, WebPushException
from fastapi.concurrency import run_in_threadpool
from src.config import settings

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
    await db.flush()  # assigns PKs without a full commit
    notification_ids = [n.id for n in notifications]
    await db.commit()

    # Re-fetch all in one query to get server-generated fields (created_at)
    fresh_result = await db.execute(
        select(Notification).where(Notification.id.in_(notification_ids))
    )
    fresh_notifications = fresh_result.scalars().all()

    # Broadcast to connected sockets
    tasks = []
    for notification in fresh_notifications:
        notif_data = NotificationOut.model_validate(notification).model_dump(mode="json")
        tasks.append(manager.send_personal_message({
            "type": "notification_event",
            "data": notif_data
        }, notification.user_id))
        
    if tasks:
        await asyncio.gather(*tasks)
        
    # Fetch web push subscriptions
    sub_result = await db.execute(select(PushSubscription).where(PushSubscription.user_id.in_(active_user_ids)))
    subs = sub_result.scalars().all()
    sub_infos = [{"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}} for sub in subs]
    
    if sub_infos:
        payload = json.dumps({
            "title": "New Notification",
            "body": "You have a new update.",
            "type": type,
            "data": data,
            "url": "/"
        })
        asyncio.create_task(_run_web_push_batch(sub_infos, payload))

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


async def save_push_subscription(db: AsyncSession, user_id: int, sub: PushSubscriptionIn):
    result = await db.execute(select(PushSubscription).where(PushSubscription.endpoint == sub.endpoint))
    existing = result.scalar_one_or_none()
    if existing:
        existing.user_id = user_id
        existing.p256dh = sub.keys.p256dh
        existing.auth = sub.keys.auth
    else:
        new_sub = PushSubscription(
            user_id=user_id,
            endpoint=sub.endpoint,
            p256dh=sub.keys.p256dh,
            auth=sub.keys.auth
        )
        db.add(new_sub)
    await db.commit()

def _send_web_push(subscription_info: dict, payload: str):
    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY_PATH,
            vapid_claims={"sub": settings.VAPID_SUBJECT}
        )
    except WebPushException as ex:
        print("Web Push failed:", repr(ex))

async def _run_web_push_batch(sub_infos: list[dict], payload: str):
    tasks = [run_in_threadpool(_send_web_push, info, payload) for info in sub_infos]
    if tasks:
        await asyncio.gather(*tasks)
