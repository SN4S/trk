import logging
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import parse_jwt_data, get_current_user
from src.database import get_db
from src.websockets.manager import manager

from pydantic import BaseModel

logger = logging.getLogger(__name__)

INTERNAL_SECRET = os.getenv("INTERNAL_API_SECRET", "")


class BroadcastEvent(BaseModel):
    type: str
    data: dict


def verify_internal_secret(x_internal_secret: str = Header(..., alias="X-Internal-Secret")) -> None:
    if not INTERNAL_SECRET or x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


router = APIRouter(
    prefix="/ws",
    tags=["websockets"]
)


@router.post("/broadcast", dependencies=[Depends(verify_internal_secret)])
async def broadcast_event(event: BroadcastEvent, db: AsyncSession = Depends(get_db)):
    from src.notifications.service import broadcast_event as service_broadcast, notify_users
    from src.auth.models import User
    from sqlalchemy import select
    
    await service_broadcast(type=event.type, data=event.data)
    
    if event.type == "new_ticket":
        admins_managers_query = select(User.id).where(User.role.in_(["admin", "manager"]), User.is_active == True)
        result = await db.execute(admins_managers_query)
        admin_manager_ids = result.scalars().all()
        await notify_users(db, "new_ticket", event.data, user_ids=list(admin_manager_ids))
        
    elif event.type == "new_reply":
        assignee_id = event.data.get("ticket_assigned_to_id")
        is_support = event.data.get("is_support", False)
        if not is_support:
            if assignee_id:
                await notify_users(db, "new_reply", event.data, user_ids=[assignee_id])
            else:
                admins_managers_query = select(User.id).where(User.role.in_(["admin", "manager"]), User.is_active == True)
                result = await db.execute(admins_managers_query)
                admin_manager_ids = result.scalars().all()
                await notify_users(db, "new_reply", event.data, user_ids=list(admin_manager_ids))
            
    return {"status": "ok"}


@router.websocket("/updates")
async def websocket_updates(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Access Token"),
    db: AsyncSession = Depends(get_db)
):
    try:
        token_data = await parse_jwt_data(token)
        user = await get_current_user(token_data, db)
        logger.info("WS Auth Success: %s", user.username)
    except Exception as e:
        logger.warning("WS Auth Failed: %s", e)
        await websocket.close(code=1008, reason="Invalid authentication credentials")
        return

    await manager.connect(websocket, user.id)
    logger.debug("WS Connected. Active connections: %d", sum(len(conns) for conns in manager.active_connections.values()))
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
