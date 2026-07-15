from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.schemas import UtcDatetime
from src.tickets.models import TicketStatus
from src.replies.schemas import ReplyOut


class TicketCreate(BaseModel):
    ticket_num: str = Field(min_length=1, max_length=32)
    theme_id: int
    group_id: int
    soc_user_id: int
    soc_user_name: str = Field(min_length=1, max_length=255)
    message: str | None = Field(default=None, max_length=4000)


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    theme_id: int | None = None
    group_id: int | None = None
    message: str | None = Field(default=None, max_length=4000)


class TicketAssign(BaseModel):
    """Body for PATCH /{ticket_id}/assign. Pass user_id=null to unassign."""
    user_id: int | None = None


class ThemeInTicket(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class GroupInTicket(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class UserInTicket(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}


class TicketAssignmentOut(BaseModel):
    id: int
    ticket_id: int
    assigned_to: UserInTicket | None = None
    assigned_by: UserInTicket
    assigned_at: UtcDatetime

    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: int
    ticket_num: str
    theme_id: int
    group_id: int
    soc_user_id: int
    soc_user_name: str
    message: str | None
    status: TicketStatus
    created_at: UtcDatetime
    updated_at: UtcDatetime | None
    theme: ThemeInTicket | None = None
    group: GroupInTicket | None = None
    # The latest assignment entry; None if never assigned
    current_assignment: TicketAssignmentOut | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _derive_current_assignment(cls, data: Any) -> Any:
        """When built from an ORM Ticket, pull the last assignment out of the list."""
        assignments = getattr(data, "assignments", None)
        if assignments is not None:
            object.__setattr__(
                data,
                "current_assignment",
                assignments[-1] if assignments else None,
            )
        return data


class TicketStats(BaseModel):
    group_id: int | None
    all: int
    open: int
    pending: int
    closed: int


class GeneralChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    parent_id: int | None = None


class GeneralChatParentPreview(BaseModel):
    id: int
    message: str
    user: UserInTicket | None = None
    model_config = {"from_attributes": True}


class GeneralChatMessageOut(BaseModel):
    id: int
    ticket_id: int | None
    reply_id: int | None
    parent_id: int | None
    user_id: int
    message: str
    created_at: UtcDatetime
    ticket: TicketOut | None = None
    reply: ReplyOut | None = None
    parent: GeneralChatParentPreview | None = None
    user: UserInTicket | None = None

    model_config = {"from_attributes": True}