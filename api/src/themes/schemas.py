from pydantic import BaseModel, Field


class ThemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ThemeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ThemeOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
