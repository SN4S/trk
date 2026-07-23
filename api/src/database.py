from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


from src.auth import models as _auth_models          # noqa: E402,F401
from src.tickets import models as _tickets_models    # noqa: E402,F401
from src.groups import models as _groups_models      # noqa: E402,F401
from src.folders import models as _folders_models    # noqa: E402,F401
from src.themes import models as _themes_models      # noqa: E402,F401
from src.replies import models as _replies_models    # noqa: E402,F401
from src.notifications import model as _notifications_model # noqa: E402,F401
from src.attachments import models as _attachments_models # noqa: E402,F401