from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    tg_group_id: int | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tg_group_id: int | None = None


class GroupOut(BaseModel):
    id: int
    name: str
    tg_group_id: int | None

    model_config = {"from_attributes": True}


class UserGroupAccessCreate(BaseModel):
    user_id: int
    is_responsible: bool = False


class UserGroupAccessOut(BaseModel):
    id: int
    user_id: int
    group_id: int
    is_responsible: bool

    model_config = {"from_attributes": True}
