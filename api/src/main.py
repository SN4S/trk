import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.folders.router import router as folder_router
from src.groups.router import router as group_router
from src.tickets.router import router as ticket_router
from src.replies.router import router as reply_router
from src.themes.router import router as theme_router
from src.misc.router import router as misc_router
from src.tickets.router import general_chat_router
from src.websockets.router import router as websocket_router

app = FastAPI(
    title="XproSupport API",
    description="REST API",
    version="1.0.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(folder_router)
app.include_router(group_router)
app.include_router(ticket_router)
app.include_router(reply_router)
app.include_router(theme_router)
app.include_router(misc_router)
app.include_router(general_chat_router)
app.include_router(websocket_router)


@app.get("/", tags=["health"])
async def root():
    return {"health": "OK"}
