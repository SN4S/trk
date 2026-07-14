from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas import UtcDatetime


class ReplyCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    is_support: bool
    requires_client_reply: bool = False


class UserInReply(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}


class ReplyOut(BaseModel):
    id: int
    ticket_id: int
    message: str
    is_support: bool
    user_id: int | None
    created_at: UtcDatetime
    user: UserInReply | None = None

    model_config = {"from_attributes": True}
