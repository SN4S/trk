"""Add ticket_assignment table (3NF refactor)

Revision ID: b1c2d3e4f5a6
Revises: 067f29f4ec48
Create Date: 2026-07-14 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    1. Migrate existing assigned_to_id values into the new ticket_assignment table.
    2. Drop the FK constraint and assigned_to_id column from ticket.
    3. Create ticket_assignment table.
    """
    # Step 1: Create the new table first
    op.create_table(
        'ticket_assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),   # NULL means "unassigned"
        sa.Column('assigned_by_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['user.id'], name='fk_ticket_assignment_assigned_by'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], name='fk_ticket_assignment_assigned_to'),
        sa.ForeignKeyConstraint(['ticket_id'], ['ticket.id'], name='fk_ticket_assignment_ticket', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Step 2: Migrate existing assignments into the audit table.
    # We use the admin user (id from seed: the first user with role='admin') as assigned_by.
    # Fall back to id=1 if no admin row exists yet (fresh DB).
    conn = op.get_bind()

    # Resolve a sensible "system" user to attribute historic assignments to
    admin_row = conn.execute(
        sa.text("SELECT id FROM `user` WHERE role = 'admin' ORDER BY id LIMIT 1")
    ).fetchone()
    system_user_id = admin_row[0] if admin_row else None

    if system_user_id:
        conn.execute(sa.text("""
            INSERT INTO ticket_assignment (ticket_id, assigned_to_id, assigned_by_id, assigned_at)
            SELECT id, assigned_to_id, :sys_uid, COALESCE(updated_at, created_at)
            FROM ticket
            WHERE assigned_to_id IS NOT NULL
        """), {"sys_uid": system_user_id})

    # Step 3: Drop the old FK and column
    # MySQL names the FK automatically; use a try/except to handle both named and unnamed constraints.
    try:
        op.drop_constraint('ticket_ibfk_assigned_to', 'ticket', type_='foreignkey')
    except Exception:
        # The constraint name varies; find and drop it via information_schema
        fk_row = conn.execute(sa.text("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'ticket'
              AND COLUMN_NAME  = 'assigned_to_id'
              AND REFERENCED_TABLE_NAME IS NOT NULL
            LIMIT 1
        """)).fetchone()
        if fk_row:
            op.drop_constraint(fk_row[0], 'ticket', type_='foreignkey')

    op.drop_column('ticket', 'assigned_to_id')


def downgrade() -> None:
    """Reverse: restore assigned_to_id on ticket from the latest assignment row."""
    # Re-add the column
    op.add_column('ticket', sa.Column('assigned_to_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_ticket_assigned_to_user',
        'ticket', 'user',
        ['assigned_to_id'], ['id'],
    )

    # Restore the latest assignment per ticket
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE ticket t
        JOIN (
            SELECT ticket_id, assigned_to_id
            FROM ticket_assignment
            WHERE id IN (
                SELECT MAX(id) FROM ticket_assignment GROUP BY ticket_id
            )
        ) latest ON latest.ticket_id = t.id
        SET t.assigned_to_id = latest.assigned_to_id
    """))

    # Drop the new table
    op.drop_table('ticket_assignment')
