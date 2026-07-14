import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from database.models import init_engine, create_tables
from database import service

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DB_URL", "")
    if not db_url:
        raise RuntimeError("DB_URL is not set in .env")
    init_engine(db_url)
    await create_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class ThemeCreate(BaseModel):
    name: str

class TicketStatusPatch(BaseModel):
    status: Literal["open", "pending", "closed"]

class ReplyCreate(BaseModel):
    message: str
    user_id: int | None = None
    request_info: bool = False

@app.get("/tickets/counts", tags=["tickets"])
async def ticket_counts():
    return await service.get_ticket_counts()

@app.get("/tickets", tags=["tickets"])
async def list_tickets(group_chat_id: int | None = None):
    rows = await service.get_all_tickets(group_chat_id)
    return [serialize(r) for r in rows]


@app.get("/tickets/{ticket_id}", tags=["tickets"])
async def get_ticket(ticket_id: int):
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    replies = ticket.pop("replies", [])
    return serialize({"ticket": ticket, "replies": replies})


@app.patch("/tickets/{ticket_id}", tags=["tickets"])
async def patch_ticket_status(ticket_id: int, body: TicketStatusPatch):
    updated = await service.update_ticket_status(ticket_id, body.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return serialize(updated)


@app.post("/tickets/{ticket_id}/reply", status_code=201, tags=["tickets"])
async def reply_to_ticket(ticket_id: int, body: ReplyCreate):
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not ticket.get("soc_user_id"):
        raise HTTPException(status_code=400, detail="Ticket has no associated Telegram user")

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Reply message cannot be empty")

    reply = await service.add_reply(ticket_id, message, is_support=True, user_id=body.user_id)


    tg_token = os.getenv("TG_BOT_TOKEN", "")
    tg_error: str | None = None
    if tg_token:
        try:
            bot = Bot(token=tg_token)
            text = f"\U0001f4ac Відповідь по тікету #{ticket['ticket_num']}\n\n{message}"
            if body.request_info:
                buttons = [[InlineKeyboardButton("Додати інформацію", callback_data=f"pick_{ticket_id}")]]
                kb = InlineKeyboardMarkup(buttons)
                await bot.send_message(chat_id=ticket["soc_user_id"], text=text, reply_markup=kb)
            else:
                await bot.send_message(chat_id=ticket["soc_user_id"], text=text)
        except Exception as exc:
            logging.warning("Telegram send failed for ticket %s: %s", ticket_id, exc)
            tg_error = str(exc)
    else:
        tg_error = "TG_BOT_TOKEN not set"

    return {**serialize(reply), "tg_delivered": tg_error is None, "tg_error": tg_error}


@app.get("/groups", tags=["groups"])
async def list_groups():
    return await service.get_groups_with_counts()


@app.get("/themes", tags=["themes"])
async def list_themes():
    themes = await service.get_themes()
    return [{"id": t.id, "name": t.name} for t in themes]


@app.post("/themes", status_code=201, tags=["themes"])
async def create_theme(body: ThemeCreate):
    theme = await service.create_theme(body.name.strip())
    return {"id": theme.id, "name": theme.name}


@app.delete("/themes/{theme_id}", status_code=204, tags=["themes"])
async def delete_theme(theme_id: int):
    deleted = await service.delete_theme(theme_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Theme not found")


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
