"""Seed admin user

Revision ID: d4e5f6a7b8c9
Revises: a363b1d4e3aa
Create Date: 2026-07-10 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from src.auth.utils import hash_password

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'a7e543e9a78f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT id FROM user WHERE username = 'admin'"))
    if not res.fetchone():
        user_table = sa.table('user',
            sa.column('username', sa.String),
            sa.column('password', sa.String),
            sa.column('role', sa.String),
            sa.column('is_active', sa.Boolean)
        )
        op.bulk_insert(user_table,
            [
                {'username': 'admin', 'password': hash_password('changeme'), 'role': 'admin', 'is_active': True}
            ]
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM user WHERE username = 'admin'"))
