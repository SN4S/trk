import asyncio

from src.database import SessionFactory, engine
from src.auth.models import User
from src.auth.utils import hash_password
from src.groups.models import Group
from src.themes.models import Theme
from src.folders.models import Folder, FolderGroup
from src.tickets.models import Ticket, TicketStatus
from src.replies.models import Reply


async def main():
    async with SessionFactory() as db:
        # --- users ---
        admin = User(username="admin2", password=hash_password("changeme"), is_active=True)
        agent = User(username="agent1", password=hash_password("changeme"), is_active=True)
        db.add_all([admin, agent])
        await db.flush()  # get ids without committing yet

        # --- groups (telegram support chats) ---
        group1 = Group(name="Support Chat 1", tg_group_id=-1001111111111)
        group2 = Group(name="Support Chat 2", tg_group_id=-1002222222222)
        db.add_all([group1, group2])
        await db.flush()

        # --- themes ---
        theme_billing = Theme(name="Billing")
        theme_technical = Theme(name="Technical")
        db.add_all([theme_billing, theme_technical])
        await db.flush()

        # --- folders ---
        folder1 = Folder(name="Active Tickets", user_id=admin.id)
        folder2 = Folder(name="Archived", user_id=admin.id)
        db.add_all([folder1, folder2])
        await db.flush()

        # --- folder_group (link folders to groups) ---
        db.add_all([
            FolderGroup(folder_id=folder1.id, group_id=group1.id),
            FolderGroup(folder_id=folder1.id, group_id=group2.id),
        ])

        # --- tickets ---
        ticket1 = Ticket(
            ticket_num="T-0001",
            theme_id=theme_billing.id,
            group_id=group1.id,
            soc_user_id=123456789,
            soc_user_name='Bjorn',
            message="I was charged twice this month.",
            status=TicketStatus.OPEN,
        )
        ticket2 = Ticket(
            ticket_num="T-0002",
            theme_id=theme_technical.id,
            group_id=group2.id,
            soc_user_id=987654321,
            soc_user_name='Jogn',
            message="App crashes on login.",
            status=TicketStatus.PENDING,
        )
        db.add_all([ticket1, ticket2])
        await db.flush()

        # --- replies ---
        db.add_all([
            Reply(
                ticket_id=ticket1.id,
                message="Can you send your receipt?",
                is_support=True,
                user_id=agent.id,
            ),
            Reply(
                ticket_id=ticket1.id,
                message="Attached above.",
                is_support=False,
                user_id=None,  # from the telegram end-user, not an admin User row
            ),
            Reply(
                ticket_id=ticket2.id,
                message="Looking into it now.",
                is_support=True,
                user_id=agent.id,
            ),
        ])

        await db.commit()
        print("Seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())