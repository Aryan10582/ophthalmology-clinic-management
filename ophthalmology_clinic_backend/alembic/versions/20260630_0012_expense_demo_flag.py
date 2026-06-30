"""expense demo flag

Revision ID: 20260630_0012
Revises: 20260630_0011
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0012"
down_revision: str | None = "20260630_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("expenses", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE expenses SET is_demo_data = true WHERE notes = 'Historical analytics seed' AND EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)")
    op.alter_column("expenses", "is_demo_data", server_default=None)


def downgrade() -> None:
    op.drop_column("expenses", "is_demo_data")
