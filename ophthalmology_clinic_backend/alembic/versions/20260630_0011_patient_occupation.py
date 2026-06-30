"""patient occupation and demo flag

Revision ID: 20260630_0011
Revises: 20260630_0010
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0011"
down_revision: str | None = "20260630_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("occupation", sa.String(length=120), nullable=True))
    op.add_column("patients", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute(
        """
        UPDATE patients
        SET is_demo_data = true
        WHERE (
            phone LIKE '98765010%%'
            OR phone LIKE '988770%%'
            OR address LIKE '%%Analytics Demo Address%%'
        )
          AND EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)
        """
    )
    op.alter_column("patients", "is_demo_data", server_default=None)


def downgrade() -> None:
    op.drop_column("patients", "is_demo_data")
    op.drop_column("patients", "occupation")
