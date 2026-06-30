"""demo account flag

Revision ID: 20260630_0010
Revises: 20260630_0009
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0010"
down_revision: str | None = "20260630_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEMO_EMAILS = (
    "admin@clinic.com",
    "rupa.kapale@clinic.com",
    "amit.deshmukh@clinic.com",
    "reception1@clinic.com",
    "reception2@clinic.com",
)


def upgrade() -> None:
    op.add_column("users", sa.Column("is_demo_account", sa.Boolean(), nullable=False, server_default=sa.false()))
    emails = ", ".join(f"'{email}'" for email in DEMO_EMAILS)
    op.execute(f"UPDATE users SET is_demo_account = true WHERE lower(email) IN ({emails})")
    op.alter_column("users", "is_demo_account", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_demo_account")
