from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.notifications import service
from src.notifications.schemas import NotificationOut

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
