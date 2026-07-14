from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import utils
from src.auth.config import auth_settings
from src.auth.exceptions import InactiveUser, InvalidCredentials, InvalidToken, UsernameTaken
from src.auth.models import User, RefreshToken


async def register_user(db: AsyncSession, username: str, password: str, role: str = "support") -> User:
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none() is not None:
        raise UsernameTaken()

    user = User(username=username, password=utils.hash_password(password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not utils.verify_password(password, user.password):
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()

    return user


async def issue_refresh_token(db: AsyncSession, user_id: UUID) -> str:
    raw_token = utils.generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=utils.hash_refresh_token(raw_token),
            expires_at=datetime.now(UTC) + auth_settings.REFRESH_TOKEN_EXP,
        )
    )
    await db.commit()
    return raw_token


async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[User, str]:
    """Validate + revoke the old refresh token, issue a new one. Detects reuse."""
    token_hash = utils.hash_refresh_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()

    if stored is None:
        raise InvalidToken()

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if stored.revoked or expires_at < datetime.now(UTC):
        # Reused a revoked/expired token → possible theft. Nuke all sessions for this user.
        await db.execute(
            update(RefreshToken).where(RefreshToken.user_id == stored.user_id).values(revoked=True)
        )
        await db.commit()
        raise InvalidToken()

    stored.revoked = True
    result = await db.execute(select(User).where(User.id == stored.user_id))
    user = result.scalar_one()
    if not user.is_active:
        raise InactiveUser()

    new_token = await issue_refresh_token(db, user.id)
    await db.commit()
    return user, new_token


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    token_hash = utils.hash_refresh_token(raw_token)
    await db.execute(
        update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
    )
    await db.commit()

async def update_user(db: AsyncSession, user_id: int, role: str | None = None, is_active: bool | None = None, password: str | None = None) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
        
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    if password is not None:
        user.password = utils.hash_password(password)
        
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
        
    await db.delete(user)
    await db.commit()