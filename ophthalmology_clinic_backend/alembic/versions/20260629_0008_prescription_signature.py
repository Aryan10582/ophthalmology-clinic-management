"""prescription signature

Revision ID: 20260629_0008
Revises: 20260629_0007
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0008"
down_revision: str | None = "20260629_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prescription_templates", sa.Column("doctor_signature", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("prescription_templates", "doctor_signature")
