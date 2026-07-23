from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from src.schemas import UtcDatetime
from src.attachments.schemas import AttachmentOut


class ReplyCreate(BaseModel):
    message: str = Field(default="", max_length=4000)
    is_support: bool
    requires_client_reply: bool = False
    reply_to_reply_id: int | None = None
    attachment_ids: list[int] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_content(self) -> 'ReplyCreate':
        if not self.message.strip() and not self.attachment_ids:
            raise ValueError('Message cannot be empty without attachments')
        return self


class UserInReply(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}


class ParentReplyPreview(BaseModel):
    id: int
    message: str
    user: UserInReply | None = None
    model_config = {"from_attributes": True}

class ReplyOut(BaseModel):
    id: int
    ticket_id: int
    message: str
    is_support: bool
    user_id: int | None
    created_at: UtcDatetime
    tg_message_id: int | None = None
    reply_to_reply_id: int | None = None
    user: UserInReply | None = None
    parent_reply: ParentReplyPreview | None = None
    attachments: list[AttachmentOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
