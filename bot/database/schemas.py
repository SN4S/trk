from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ThemeOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class GroupOut(BaseModel):
    id: int
    name: str
    tg_group_id: Optional[int]
    model_config = {"from_attributes": True}

class TicketOut(BaseModel):
    id: int
    ticket_num: str
    theme_id: int
    group_id: int
    soc_user_id: int
    soc_user_name: str
    message: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: str
    theme_name: Optional[str] = None
    group_name: Optional[str] = None
    model_config = {"from_attributes": True}