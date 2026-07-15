from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field

UserRole = Literal["admin", "manager", "support"]


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "support"

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    role: str

class UserUpdateRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = Field(default=None)
    is_active: bool | None = Field(default=None)