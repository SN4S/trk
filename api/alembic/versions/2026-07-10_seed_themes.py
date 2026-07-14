"""Seed default themes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-10 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    theme_table = sa.table('theme',
        sa.column('name', sa.String)
    )
    
    op.bulk_insert(theme_table,
        [
            {'name': 'Технічна підтримка'},
            {'name': 'Фінансові питання'},
            {'name': 'Загальні питання'},
            {'name': 'Співпраця'}
        ]
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM theme WHERE name IN ('Технічна підтримка', 'Фінансові питання', 'Загальні питання', 'Співпраця')"))
