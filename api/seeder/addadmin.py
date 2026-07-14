import asyncio
from src.database import SessionFactory
from src.auth.models import User
from src.auth.utils import hash_password

import src.auth.models
import src.tickets.models
import src.groups.models
import src.folders.models
import src.themes.models
import src.replies.models


async def main():
    async with SessionFactory() as db:
        db.add(User(username="admin", password=hash_password("changeme")))
        await db.commit()

asyncio.run(main())