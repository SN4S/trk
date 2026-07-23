from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.auth import service
from src.auth.config import auth_settings
from src.auth.dependencies import CurrentUser, RequireRole
from src.auth.exceptions import InvalidToken
from src.auth.schemas import AccessTokenResponse, LoginRequest, UserOut, RegisterRequest, UserUpdateRequest
from src.auth.utils import create_access_token
from src.auth.models import User
from src.database import get_db
from sqlalchemy import select


router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        httponly=True,
        secure=auth_settings.SECURE_COOKIES,
        samesite="lax",
        max_age=int(auth_settings.REFRESH_TOKEN_EXP.total_seconds()),
        path="/",
    )

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[CurrentUser, Depends(RequireRole(["admin"]))],
):
    return await service.register_user(db, data.username, data.password, role=data.role)

@router.post("/login", response_model=AccessTokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await service.authenticate_user(db, data.username, data.password)
    refresh_token = await service.issue_refresh_token(db, user.id)
    _set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if refresh_token is None:
        raise InvalidToken()

    user, new_refresh_token = await service.rotate_refresh_token(db, refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return AccessTokenResponse(access_token=create_access_token(user.id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
):
    if refresh_token:
        await service.revoke_refresh_token(db, refresh_token)
    response.delete_cookie(REFRESH_COOKIE, path="/")

@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user

@router.get("/users", response_model=list[UserOut])
async def list_users(
    _: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User))
    return list(result.scalars().all())

@router.get("/users/mentionable", response_model=list[UserOut])
async def list_mentionable_users(
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User).where(User.is_active == True))
    return list(result.scalars().all())

@router.put("/users/{user_id}", response_model=UserOut)
async def update_user_endpoint(
    user_id: int,
    data: UserUpdateRequest,
    _: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        user = await service.update_user(
            db, 
            user_id, 
            role=data.role, 
            is_active=data.is_active, 
            password=data.password
        )
        return user
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    _: Annotated[CurrentUser, Depends(RequireRole(["admin", "manager"]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        await service.delete_user(db, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    except IntegrityError:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete user because they have associated folders or replies. Please deactivate them instead."
        )