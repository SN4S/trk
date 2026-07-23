from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.notifications import service
from src.notifications.schemas import NotificationOut, PushSubscriptionIn


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

@router.get("", response_model=List[NotificationOut])
async def get_notifications(
    unread_only: bool = Query(False, description="Fetch only unread notifications"),
    limit: int = Query(50, description="Limit the number of results"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notifications = await service.get_user_notifications(db, user.id, unread_only, limit)
    return notifications

@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notification = await service.mark_as_read(db, notification_id, user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/push-subscribe")
async def push_subscribe(
    subscription: PushSubscriptionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await service.save_push_subscription(db, user.id, subscription)
    return {"status": "ok"}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    import os
    import base64
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from py_vapid import Vapid
    key_path = "keys/private_key.pem"
    if os.path.exists(key_path):
        vapid = Vapid.from_file(key_path)
        # Browser needs the raw uncompressed EC point (65 bytes) as URL-safe base64, NOT PEM
        raw_key = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        app_server_key = base64.urlsafe_b64encode(raw_key).decode("utf-8").rstrip("=")
        return {"public_key": app_server_key}
    return {"public_key": None}
