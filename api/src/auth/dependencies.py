from typing import Annotated
from uuid import UUID

from fastapi import Depends,  HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import utils
from src.auth.exceptions import InactiveUser, InvalidToken, TokenExpired
from src.auth.models import User
from src.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def parse_jwt_data(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    try:
        payload = utils.decode_access_token(token)
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except InvalidTokenError as exc:
        raise InvalidToken() from exc

    if payload.get("type") != "access":
        raise InvalidToken()
    return payload


async def get_current_user(
    token_data: Annotated[dict, Depends(parse_jwt_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user_id = int(token_data["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidToken()
    if not user.is_active:
        raise InactiveUser()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

class RequireRole:
    def __init__(self, allowed_roles: list[str] | str):
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]
        self.allowed_roles = allowed_roles

    async def __call__(self, user: CurrentUser) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user