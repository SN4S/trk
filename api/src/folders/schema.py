from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class FolderUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class FolderGroupAdd(BaseModel):
    group_id: int


class GroupInFolder(BaseModel):
    id: int
    name: str
    tg_group_id: int | None

    model_config = {"from_attributes": True}


class FolderOut(BaseModel):
    id: int
    name: str
    groups: list[GroupInFolder] = []

    model_config = {"from_attributes": True}


class FolderOutSimple(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
